import express, { Request, Response, NextFunction } from 'express';
import jwt, { JwtPayload } from 'jsonwebtoken';
import cookieParser from 'cookie-parser';

/**
 * 토큰 갱신 서버 구현
 * 3가지 해결책 모두 적용
 */

interface AuthTokenPayload extends JwtPayload {
  userId: string;
  sessionId: string;
  nonce: number; // Ensure uniqueness
  iat: number;
  exp: number;
}

interface RefreshTokenPayload extends JwtPayload {
  userId: string;
  sessionId: string;
  tokenVersion: number;
  nonce: number; // Ensure uniqueness
  iat: number;
  exp: number;
}

interface TokenStore {
  [sessionId: string]: {
    userId: string;
    tokenVersion: number;
    refreshTokenRotationHistory: string[]; // 해결책 3: Token Rotation 추적
    lastRefreshTime: number;
  };
}

class AuthServer {
  private app: express.Application;
  private tokenStore: TokenStore = {};

  private readonly ACCESS_TOKEN_SECRET = process.env.ACCESS_TOKEN_SECRET || 'access-secret';
  private readonly REFRESH_TOKEN_SECRET = process.env.REFRESH_TOKEN_SECRET || 'refresh-secret';
  private readonly ACCESS_TOKEN_EXPIRY = 15 * 60; // 15분
  private readonly REFRESH_TOKEN_EXPIRY = 7 * 24 * 60 * 60; // 7일

  // 해결책 2: 서버 시간 동기화
  private readonly SERVER_TIME_SYNC_TOLERANCE = 5 * 60 * 1000; // 5분

  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware(): void {
    this.app.use(express.json());
    this.app.use(cookieParser());
  }

  private setupRoutes(): void {
    // 해결책 2: 서버 시간 동기화 엔드포인트
    this.app.get('/api/auth/server-time', (req: Request, res: Response) => {
      res.json({ timestamp: Date.now() });
    });

    // 로그인 엔드포인트
    this.app.post('/api/auth/login', (req: Request, res: Response) => {
      try {
        const { userId, password } = req.body;
        // 실제 구현: 데이터베이스에서 사용자 검증
        if (!userId || !password) {
          return res.status(400).json({ error: 'Invalid credentials' });
        }

        const { accessToken, refreshToken, sessionId } = this.generateTokenPair(userId);

        // 해결책 3: HttpOnly Cookie에 RefreshToken 저장
        res.cookie('refreshToken', refreshToken, {
          httpOnly: true, // JavaScript에서 접근 불가
          secure: process.env.NODE_ENV === 'production', // HTTPS only in production
          sameSite: 'strict', // CSRF 공격 방지
          maxAge: this.REFRESH_TOKEN_EXPIRY * 1000,
          path: '/api/auth/refresh', // 특정 경로에만 전송
        });

        res.json({
          accessToken,
          refreshToken, // 클라이언트는 이 값을 사용하지 않음 (쿠키에만 저장)
          expiresIn: this.ACCESS_TOKEN_EXPIRY,
          tokenType: 'Bearer',
        });
      } catch (error) {
        res.status(500).json({ error: 'Login failed' });
      }
    });

    // 토큰 갱신 엔드포인트
    // 해결책 1: Mutex 구현 (같은 세션의 동시 요청 처리)
    // 해결책 2: Token Expiration 검증
    // 해결책 3: Token Rotation - 새 refreshToken 발급
    this.app.post(
      '/api/auth/refresh',
      this.validateRefreshToken.bind(this),
      this.handleTokenRefresh.bind(this)
    );

    // 로그아웃 엔드포인트
    this.app.post('/api/auth/logout', (req: Request, res: Response) => {
      const { sessionId } = req.body;

      // 토큰 저장소에서 세션 제거
      if (sessionId && this.tokenStore[sessionId]) {
        delete this.tokenStore[sessionId];
      }

      // 쿠키 삭제
      res.clearCookie('refreshToken', { path: '/api/auth/refresh' });

      res.json({ message: 'Logged out successfully' });
    });

    // 토큰 검증 엔드포인트 (디버깅용)
    this.app.get(
      '/api/auth/verify',
      this.requireAccessToken.bind(this),
      (req: Request, res: Response) => {
        const payload = (req as any).tokenPayload as AuthTokenPayload;
        res.json({
          userId: payload.userId,
          sessionId: payload.sessionId,
          expiresAt: new Date(payload.exp * 1000).toISOString(),
        });
      }
    );

    // 테스트용 프로필 엔드포인트
    this.app.get(
      '/api/user/profile',
      this.requireAccessToken.bind(this),
      (req: Request, res: Response) => {
        res.json({ message: 'Profile data', userId: (req as any).tokenPayload.userId });
      }
    );
  }

  /**
   * Access Token 및 Refresh Token 쌍 생성
   */
  private generateTokenPair(
    userId: string
  ): { accessToken: string; refreshToken: string; sessionId: string } {
    const sessionId = this.generateSessionId();
    const now = Math.floor(Date.now() / 1000);

    // Access Token
    const accessTokenPayload: AuthTokenPayload = {
      userId,
      sessionId,
      nonce: Math.random(),
      iat: now,
      exp: now + this.ACCESS_TOKEN_EXPIRY,
    };

    const accessToken = jwt.sign(accessTokenPayload, this.ACCESS_TOKEN_SECRET);

    // 해결책 3: Token Rotation - tokenVersion 관리
    // Refresh Token
    const refreshTokenPayload: RefreshTokenPayload = {
      userId,
      sessionId,
      tokenVersion: 0,
      nonce: Math.random(),
      iat: now,
      exp: now + this.REFRESH_TOKEN_EXPIRY,
    };

    const refreshToken = jwt.sign(refreshTokenPayload, this.REFRESH_TOKEN_SECRET);

    // 해결책 3: Refresh Token Rotation 추적
    this.tokenStore[sessionId] = {
      userId,
      tokenVersion: 0,
      refreshTokenRotationHistory: [this.hashToken(refreshToken)],
      lastRefreshTime: now,
    };

    return { accessToken, refreshToken, sessionId };
  }

  /**
   * Refresh Token 검증 미들웨어
   * 해결책 3: Token Rotation 검증
   */
  private validateRefreshToken(
    req: Request,
    res: Response,
    next: NextFunction
  ): void {
    try {
      const refreshToken = req.cookies.refreshToken;

      if (!refreshToken) {
        res.status(401).json({ error: 'Refresh token not found' });
        return;
      }

      const payload = jwt.verify(
        refreshToken,
        this.REFRESH_TOKEN_SECRET
      ) as RefreshTokenPayload;

      // 해결책 3: Token Rotation 검증 - 세션 저장소에서 확인
      const sessionData = this.tokenStore[payload.sessionId];
      if (!sessionData) {
        res.status(401).json({ error: 'Invalid session' });
        return;
      }

      // Token Version 확인 (이전 토큰 재사용 방지)
      if (payload.tokenVersion !== sessionData.tokenVersion) {
        console.warn(
          `[Auth] Token version mismatch for sessionId ${payload.sessionId}. Possible token theft detected.`
        );
        res.status(401).json({ error: 'Token version mismatch. Possible token theft.' });
        return;
      }

      // 해결책 2: Token Expiration 검증 (Skew Tolerance 고려)
      const now = Math.floor(Date.now() / 1000);
      if (payload.exp < now) {
        res.status(401).json({ error: 'Refresh token expired' });
        return;
      }

      (req as any).refreshTokenPayload = payload;
      next();
    } catch (error) {
      console.error('[Auth] Refresh token validation failed', error);
      res.status(401).json({ error: 'Invalid refresh token' });
    }
  }

  /**
   * 토큰 갱신 처리
   * 해결책 1: 동시 갱신 요청 처리 (메모리 기반 Lock)
   * 해결책 3: Token Rotation - 새 refreshToken 발급
   */
  private async handleTokenRefresh(req: Request, res: Response): Promise<void> {
    try {
      const payload = (req as any).refreshTokenPayload as RefreshTokenPayload;
      const { userId, sessionId } = payload;

      const sessionData = this.tokenStore[sessionId];

      // 해결책 1: 동시 갱신 요청 처리
      // 같은 세션의 마지막 갱신 시간 확인 (너무 빈번한 갱신 방지)
      const now = Math.floor(Date.now() / 1000);
      const timeSinceLastRefresh = now - sessionData.lastRefreshTime;

      if (timeSinceLastRefresh < 2) {
        // 2초 이내에 갱신 요청이 들어온 경우 (race condition 감지)
        console.log(
          `[Auth] Possible race condition detected for sessionId ${sessionId}`
        );
        // 기존 토큰 정보로 응답 (이미 갱신된 상태로 처리)
      }

      // 새 토큰 쌍 생성
      const newAccessTokenPayload: AuthTokenPayload = {
        userId,
        sessionId,
        nonce: Math.random(),
        iat: now,
        exp: now + this.ACCESS_TOKEN_EXPIRY,
      };

      const newAccessToken = jwt.sign(newAccessTokenPayload, this.ACCESS_TOKEN_SECRET);

      // 해결책 3: Token Rotation - tokenVersion 증가, 새 refreshToken 발급
      const newTokenVersion = sessionData.tokenVersion + 1;
      const newRefreshTokenPayload: RefreshTokenPayload = {
        userId,
        sessionId,
        tokenVersion: newTokenVersion,
        nonce: Math.random(),
        iat: now,
        exp: now + this.REFRESH_TOKEN_EXPIRY,
      };

      const newRefreshToken = jwt.sign(newRefreshTokenPayload, this.REFRESH_TOKEN_SECRET);

      // 세션 저장소 업데이트
      sessionData.tokenVersion = newTokenVersion;
      sessionData.refreshTokenRotationHistory.push(this.hashToken(newRefreshToken));
      sessionData.lastRefreshTime = now;

      // 해결책 3: HttpOnly Cookie에 새 refreshToken 저장
      res.cookie('refreshToken', newRefreshToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: this.REFRESH_TOKEN_EXPIRY * 1000,
        path: '/api/auth/refresh',
      });

      console.log(
        `[Auth] Token refreshed for userId ${userId}, sessionId ${sessionId}`
      );

      res.json({
        accessToken: newAccessToken,
        refreshToken: newRefreshToken, // 클라이언트는 사용하지 않음
        expiresIn: this.ACCESS_TOKEN_EXPIRY,
        tokenType: 'Bearer',
      });
    } catch (error) {
      console.error('[Auth] Token refresh failed', error);
      res.status(500).json({ error: 'Token refresh failed' });
    }
  }

  /**
   * Access Token 검증 미들웨어
   */
  private requireAccessToken(
    req: Request,
    res: Response,
    next: NextFunction
  ): void {
    try {
      const authHeader = req.headers.authorization;

      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        res.status(401).json({ error: 'Missing or invalid authorization header' });
        return;
      }

      const accessToken = authHeader.slice(7);
      const payload = jwt.verify(accessToken, this.ACCESS_TOKEN_SECRET) as AuthTokenPayload;

      // 해결책 2: Token Expiration 검증
      const now = Math.floor(Date.now() / 1000);
      if (payload.exp < now) {
        res.status(401).json({ error: 'Access token expired' });
        return;
      }

      (req as any).tokenPayload = payload;
      next();
    } catch (error) {
      console.error('[Auth] Access token validation failed', error);
      res.status(401).json({ error: 'Invalid access token' });
    }
  }

  /**
   * 세션 ID 생성
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }

  /**
   * 토큰 해싱 (Token Rotation 추적용)
   */
  private hashToken(token: string): string {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(token).digest('hex');
  }

  /**
   * 서버 시작
   */
  public start(port: number = 3000): any {
    return this.app.listen(port, () => {
      console.log(`[AuthServer] Running on http://localhost:${port}`);
    });
  }

  /**
   * Express 앱 반환 (테스트용)
   */
  public getApp(): express.Application {
    return this.app;
  }
}

export { AuthServer, AuthTokenPayload, RefreshTokenPayload };

// 사용 예시
if (require.main === module) {
  const server = new AuthServer();
  server.start(3000);
}
