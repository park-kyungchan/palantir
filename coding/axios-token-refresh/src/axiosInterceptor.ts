import axios, { AxiosInstance, AxiosRequestConfig, AxiosError, InternalAxiosRequestConfig, AxiosHeaders } from 'axios';

/**
 * Token 관리 및 Refresh 로직을 위한 인터셉터
 * 3가지 해결책 적용:
 * 1. Token Refresh Lock (뮤텍스) - Race Condition 해결
 * 2. 시간 동기화 + Skew Tolerance - Token Expiration Timing Mismatch 해결
 * 3. HttpOnly Cookie + Token Rotation - Refresh Token Vulnerability 해결
 */


interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

interface StoredToken {
  accessToken: string;
  // refreshToken: string; // REMOVED: Managed strictly via HttpOnly Cookie
  expiresAt: number;
  issuedAt: number;
}

interface ServerTimeResponse {
  timestamp: number;
}

class TokenManager {
  private tokenCache: StoredToken | null = null;

  // 해결책 1: Token Refresh Lock (뮤텍스)
  // Race Condition 방지: 첫 요청만 갱신, 나머지는 대기
  private refreshPromise: Promise<TokenResponse> | null = null;
  private isRefreshing = false;

  // 해결책 2: 시간 동기화 + Skew Tolerance
  // 서버와 클라이언트 시간 차이 보정
  private serverTimeDiff: number = 0;
  private readonly SKEW_TOLERANCE = 60 * 1000; // 60초 여유

  private apiClient: AxiosInstance;
  private readonly API_URL: string;
  private readonly REFRESH_TOKEN_ENDPOINT = '/api/auth/refresh';
  private readonly SERVER_TIME_ENDPOINT = '/api/auth/server-time';

  constructor(apiUrl: string) {
    this.API_URL = apiUrl;
    this.apiClient = axios.create({
      baseURL: apiUrl,
      withCredentials: true, // HttpOnly Cookie 자동 포함
    });
  }

  /**
   * 해결책 2: 서버 시간과 클라이언트 시간 동기화
   * 초기 앱 로드 시 한 번 호출하여 시간 차이 계산
   */
  async synchronizeServerTime(retryCount = 0): Promise<void> {
    try {
      const clientTime = Date.now();
      const response = await this.apiClient.get<ServerTimeResponse>(
        this.SERVER_TIME_ENDPOINT
      );
      const serverTime = response.data.timestamp;
      this.serverTimeDiff = serverTime - clientTime;
      console.log(`[TokenManager] Server time synced. Diff: ${this.serverTimeDiff}ms`);
    } catch (error) {
      console.error(`[TokenManager] Failed to sync server time (Attempt ${retryCount + 1}/3)`, error);
      if (retryCount < 2) {
        // Retry after 1 second
        await new Promise(resolve => setTimeout(resolve, 1000));
        return this.synchronizeServerTime(retryCount + 1);
      }
      // Fallback to 0 diff after retries exhausted
      this.serverTimeDiff = 0;
      console.warn('[TokenManager] Server time sync failed after 3 attempts. Using local time.');
    }
  }

  /**
   * 현재 시간 (서버 시간 기준)
   */
  private getCurrentTime(): number {
    return Date.now() + this.serverTimeDiff;
  }

  /**
   * 토큰이 곧 만료되는지 확인
   * 해결책 2: Skew Tolerance 적용 (60초 전부터 갱신)
   */
  private isTokenExpiringSoon(): boolean {
    if (!this.tokenCache) return true;

    const currentTime = this.getCurrentTime();
    const timeUntilExpiry = this.tokenCache.expiresAt - currentTime;

    // 60초 여유를 두고 갱신 시작
    const shouldRefresh = timeUntilExpiry < this.SKEW_TOLERANCE;

    if (shouldRefresh) {
      console.log(
        `[TokenManager] Token expiring soon. Expires in: ${timeUntilExpiry / 1000}s`
      );
    }

    return shouldRefresh;
  }

  /**
   * 해결책 1: Token Refresh Lock 구현
   * 동시에 여러 요청이 토큰 갱신을 시도하는 경합(race condition) 방지
   * 첫 번째 요청만 실제 갱신 수행, 나머지는 Promise 대기
   */
  private async getValidAccessToken(): Promise<string> {
    // 토큰이 유효하면 즉시 반환
    if (this.tokenCache && !this.isTokenExpiringSoon()) {
      return this.tokenCache.accessToken;
    }

    // 이미 갱신 중이면 그 Promise 대기
    if (this.isRefreshing && this.refreshPromise) {
      console.log('[TokenManager] Token refresh in progress, waiting...');
      const result = await this.refreshPromise;
      return result.accessToken;
    }

    // 새로운 갱신 시작
    this.isRefreshing = true;
    this.refreshPromise = this.performTokenRefresh();

    try {
      const result = await this.refreshPromise;
      return result.accessToken;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * 실제 토큰 갱신 로직
   * 해결책 3: HttpOnly Cookie에서 Refresh Token 자동 포함
   * withCredentials: true로 설정되어 있어 자동 처리됨
   */
  private async performTokenRefresh(): Promise<TokenResponse> {
    try {
      console.log('[TokenManager] Starting token refresh...');

      const response = await this.apiClient.post<TokenResponse>(
        this.REFRESH_TOKEN_ENDPOINT,
        {}, // body는 비워두고, HttpOnly Cookie에서 refreshToken 자동 포함
        {
          withCredentials: true, // 해결책 3: HttpOnly Cookie 명시
        }
      );

      const { accessToken, expiresIn } = response.data;
      const currentTime = this.getCurrentTime();

      // 해결책 3: Token Rotation - 새 refreshToken 저장
      // HttpOnly Cookie는 자동으로 Set-Cookie 헤더로 갱신됨
      this.tokenCache = {
        accessToken,
        // refreshToken: response.data.refreshToken, // REMOVED
        expiresAt: currentTime + expiresIn * 1000,
        issuedAt: currentTime,
      };

      console.log(
        `[TokenManager] Token refreshed. Expires in: ${expiresIn}s`
      );

      return response.data;
    } catch (error) {
      console.error('[TokenManager] Token refresh failed', error);
      this.clearToken();
      throw error;
    }
  }

  /**
   * 토큰 저장 (초기 로그인 시)
   */
  storeToken(tokenData: TokenResponse): void {
    const currentTime = this.getCurrentTime();
    this.tokenCache = {
      accessToken: tokenData.accessToken,
      // refreshToken is NOT stored in memory
      expiresAt: currentTime + tokenData.expiresIn * 1000,
      issuedAt: currentTime,
    };
    console.log('[TokenManager] Token stored (Access Token only)');
  }

  /**
   * 토큰 삭제
   */
  clearToken(): void {
    this.tokenCache = null;
    console.log('[TokenManager] Token cleared');
  }

  /**
   * 토큰 획득 (요청 인터셉터에서 사용)
   */
  async getAccessToken(): Promise<string> {
    return this.getValidAccessToken();
  }

  /**
   * 토큰 캐시 조회 (디버깅용)
   */
  getTokenCache(): StoredToken | null {
    return this.tokenCache;
  }
}

/**
 * Axios 인터셉터 설정
 */
export function setupAxiosInterceptors(
  axiosInstance: AxiosInstance,
  tokenManager: TokenManager
): void {
  /**
   * Request 인터셉터
   * 모든 요청에 Access Token 추가
   */
  axiosInstance.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
      try {
        // 해결책 1, 2 적용: getAccessToken에서 필요시 갱신 + Skew Tolerance 체크
        const accessToken = await tokenManager.getAccessToken();

        if (!config.headers) {
          config.headers = new AxiosHeaders();
        }

        config.headers.set('Authorization', `Bearer ${accessToken}`);
        console.log('[Interceptor] Request sent with valid token');
      } catch (error) {
        console.error('[Interceptor] Failed to get access token', error);
        // 토큰 갱신 실패 시 로그인 페이지로 리다이렉트 (추가 구현 필요)
        throw error;
      }

      return config;
    },
    (error) => Promise.reject(error)
  );

  /**
   * Response 인터셉터
   * 401 Unauthorized 응답 처리
   */
  axiosInstance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

      // 401 Unauthorized 응답
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          console.log('[Interceptor] 401 Unauthorized, attempting token refresh...');

          // 토큰 갱신 시도
          // 해결책 1: 이미 갱신 중이면 자동으로 대기
          const accessToken = await tokenManager.getAccessToken();

          if (!originalRequest.headers) {
            originalRequest.headers = new AxiosHeaders();
          }

          originalRequest.headers.set('Authorization', `Bearer ${accessToken}`);
          console.log('[Interceptor] Retrying request with refreshed token');

          // 원본 요청 재시도
          return axiosInstance(originalRequest);
        } catch (refreshError) {
          console.error('[Interceptor] Token refresh failed after 401', refreshError);
          // 갱신 실패: 로그인 페이지로 리다이렉트
          tokenManager.clearToken();
          // 예: window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );
}

/**
 * 사용 예시
 */
export function initializeAuthClient(apiUrl: string): {
  client: AxiosInstance;
  tokenManager: TokenManager;
} {
  // Axios 인스턴스 생성
  const client = axios.create({
    baseURL: apiUrl,
    withCredentials: true, // 해결책 3: HttpOnly Cookie 자동 포함
  });

  // Token Manager 생성
  const tokenManager = new TokenManager(apiUrl);

  // 인터셉터 설정
  setupAxiosInterceptors(client, tokenManager);

  return { client, tokenManager };
}

export { TokenManager, TokenResponse, StoredToken };
