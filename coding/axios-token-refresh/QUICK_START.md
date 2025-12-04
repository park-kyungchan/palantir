# 빠른 시작 가이드

## 5분 안에 구현하기

### 1단계: 클라이언트 초기화

```typescript
import { initializeAuthClient } from './axiosInterceptor';

// 앱 시작 시 (main.ts, App.tsx 등)
const { client, tokenManager } = initializeAuthClient('http://your-api.com');

// 서버 시간 동기화 (중요!)
await tokenManager.synchronizeServerTime();

export { client, tokenManager };
```

### 2단계: 로그인

```typescript
import { client, tokenManager } from './auth';

// 로그인 버튼 클릭
async function handleLogin(email: string, password: string) {
  const response = await client.post('/api/auth/login', { email, password });

  // 토큰 저장 (접근할 수 없는 HttpOnly Cookie에 자동 저장됨)
  tokenManager.storeToken(response.data);
}
```

### 3단계: API 요청

```typescript
import { client } from './auth';

// 모든 요청이 자동으로 토큰 관리됨
async function fetchData() {
  const response = await client.get('/api/user/profile');
  return response.data;
}
```

**끝!** 나머지는 모두 자동으로 처리됩니다.

---

## 자동으로 처리되는 것들

✓ 토큰 만료 확인 (Skew Tolerance 포함)
✓ 필요시 토큰 갱신 (Race Condition 방지)
✓ 요청에 토큰 추가
✓ 401 응답 처리 및 재시도
✓ Refresh Token을 안전한 쿠키에 저장
✓ Token Rotation으로 탈취 방지

---

## 주요 API

### TokenManager

```typescript
// 로그인 후 토큰 저장
tokenManager.storeToken(loginResponse.data);

// 수동 토큰 갱신 (보통 필요 없음)
const newToken = await tokenManager.getAccessToken();

// 로그아웃
tokenManager.clearToken();

// 현재 토큰 정보 조회 (디버깅용)
const tokenCache = tokenManager.getTokenCache();
```

### Axios Client

```typescript
// 일반 GET 요청
const data = await client.get('/api/endpoint');

// POST 요청
const response = await client.post('/api/endpoint', { body: 'data' });

// 헤더 커스터마이징 (토큰은 자동 추가됨)
const data = await client.get('/api/endpoint', {
  headers: { 'X-Custom-Header': 'value' }
});

// 에러 처리
try {
  const data = await client.get('/api/endpoint');
} catch (error) {
  // 401: 자동으로 처리됨 (토큰 갱신 + 재시도)
  // 401 이외의 에러는 여기서 처리
  console.error(error.response?.status, error.message);
}
```

---

## 서버 구현 (Node.js + Express)

### 최소 구현

```typescript
import express from 'express';
import cookieParser from 'cookie-parser';
import jwt from 'jsonwebtoken';

const app = express();
app.use(express.json());
app.use(cookieParser());

const ACCESS_SECRET = 'your-secret';
const REFRESH_SECRET = 'your-secret';

// 로그인
app.post('/api/auth/login', (req, res) => {
  const userId = req.body.userId;

  // Access Token (15분)
  const accessToken = jwt.sign({ userId }, ACCESS_SECRET, { expiresIn: '15m' });

  // Refresh Token (7일) - HttpOnly Cookie에 저장
  const refreshToken = jwt.sign({ userId }, REFRESH_SECRET, { expiresIn: '7d' });

  res.cookie('refreshToken', refreshToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 7 * 24 * 60 * 60 * 1000,
  });

  res.json({
    accessToken,
    expiresIn: 900, // 15분 = 900초
    tokenType: 'Bearer',
  });
});

// 토큰 갱신
app.post('/api/auth/refresh', (req, res) => {
  const refreshToken = req.cookies.refreshToken;

  try {
    const decoded = jwt.verify(refreshToken, REFRESH_SECRET);

    // 새 Access Token 발급
    const newAccessToken = jwt.sign(
      { userId: decoded.userId },
      ACCESS_SECRET,
      { expiresIn: '15m' }
    );

    // 새 Refresh Token 발급 (Token Rotation)
    const newRefreshToken = jwt.sign(
      { userId: decoded.userId },
      REFRESH_SECRET,
      { expiresIn: '7d' }
    );

    res.cookie('refreshToken', newRefreshToken, {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
      maxAge: 7 * 24 * 60 * 60 * 1000,
    });

    res.json({
      accessToken: newAccessToken,
      expiresIn: 900,
      tokenType: 'Bearer',
    });
  } catch (error) {
    res.status(401).json({ error: 'Invalid refresh token' });
  }
});

// 서버 시간 동기화
app.get('/api/auth/server-time', (req, res) => {
  res.json({ timestamp: Date.now() });
});

// API 보호
app.get('/api/user/profile', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];

  try {
    const decoded = jwt.verify(token, ACCESS_SECRET);
    res.json({ userId: decoded.userId, /* ... */ });
  } catch (error) {
    res.status(401).json({ error: 'Unauthorized' });
  }
});

app.listen(3000);
```

---

## React 예제

```typescript
import React, { useEffect, useState } from 'react';
import { client, tokenManager } from './auth';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 앱 시작 시 초기화
    (async () => {
      await tokenManager.synchronizeServerTime();
      setLoading(false);
    })();
  }, []);

  async function handleLogin(email: string, password: string) {
    const response = await client.post('/api/auth/login', { email, password });
    tokenManager.storeToken(response.data);

    const userData = await client.get('/api/user/profile');
    setUser(userData.data);
  }

  async function handleLogout() {
    tokenManager.clearToken();
    setUser(null);
  }

  if (loading) return <div>Loading...</div>;

  if (!user) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <div>
      <h1>Welcome, {user.name}!</h1>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}

export default App;
```

---

## 일반적인 실수

### ❌ 실수 1: 초기화 생략

```typescript
// 잘못됨
const { client } = initializeAuthClient('http://api.com');
// 시간 동기화 안 함 -> Skew Tolerance가 작동하지 않음
```

### ✓ 올바름

```typescript
const { client, tokenManager } = initializeAuthClient('http://api.com');
await tokenManager.synchronizeServerTime(); // 필수!
```

---

### ❌ 실수 2: localStorage에 토큰 저장

```typescript
// 잘못됨
localStorage.setItem('accessToken', token);
// XSS 공격으로 토큰 탈취 가능
```

### ✓ 올바름

```typescript
// storeToken을 사용하면 자동으로 안전하게 저장됨
tokenManager.storeToken(loginResponse.data);
// Access Token: 메모리 (JavaScript 접근 가능하지만 페이지 새로고침 시 리셋)
// Refresh Token: HttpOnly Cookie (JavaScript 접근 불가)
```

---

### ❌ 실수 3: 서버에서 토큰 갱신 안 함

```typescript
// 잘못됨
const accessToken = jwt.sign(payload, secret, { expiresIn: '30d' });
// Access Token이 너무 길어서 갱신이 필요 없게 됨
// 토큰 탈취 시 1개월간 악용 가능
```

### ✓ 올바름

```typescript
const accessToken = jwt.sign(payload, secret, { expiresIn: '15m' });
// 짧은 유효기간으로 자주 갱신됨
// 토큰 탈취 시 최대 15분만 악용 가능
```

---

## 문제 해결

### Q: "Token Refresh Lock" 테스트는 어떻게 하나?

```typescript
// 동시에 100개 요청 발생
const promises = Array(100)
  .fill(null)
  .map(() => client.get('/api/endpoint'));

await Promise.all(promises);
// 콘솔에서 "Token refresh in progress, waiting..." 메시지가 99번 출력되면 OK
```

### Q: 서버와 시간이 자꾸 맞지 않아요

```typescript
// 클라이언트 시간 확인
console.log(tokenManager.getTokenCache()?.expiresAt);

// 서버 시간 확인 (브라우저 개발자 도구)
fetch('http://your-api.com/api/auth/server-time')
  .then(r => r.json())
  .then(d => console.log(d.timestamp));

// 시간 차이가 60초 이상이면 시스템 시간 동기화 필요
```

### Q: Refresh Token이 도난당했어요

토큰 탈취가 감지되면 자동으로 차단됩니다 (Token Rotation).

탈취된 세션을 수동으로 무효화하려면:

```typescript
// 서버에서
delete tokenStore[sessionId];

// 또는 클라이언트에서
tokenManager.clearToken();
await client.post('/api/auth/logout');
```

---

## 성능 최적화

### 1. Skew Tolerance 조정

```typescript
// 기본값: 60초 전에 갱신
// 더 빨리 갱신하고 싶으면
this.SKEW_TOLERANCE = 30 * 1000; // 30초
```

### 2. Token 갱신 시간 조정

```typescript
// 서버에서
const ACCESS_TOKEN_EXPIRY = 15 * 60; // 15분 (기본값)
// 더 길게 하려면
const ACCESS_TOKEN_EXPIRY = 30 * 60; // 30분
// Skew Tolerance도 함께 조정해야 함
```

### 3. 배치 요청 최적화

```typescript
// 동시에 많은 요청이 필요한 경우
const results = await Promise.all([
  client.get('/api/endpoint1'),
  client.get('/api/endpoint2'),
  client.get('/api/endpoint3'),
]);
// Token Refresh Lock으로 인해 첫 요청만 갱신 (나머지 2개는 대기)
```

---

## 다음 단계

1. **IMPLEMENTATION_GUIDE.md** 읽기 - 상세한 구현 방식
2. **tokenRefresh.test.ts** 확인 - 테스트 케이스 및 예제
3. **usageExample.ts** 실행 - 실제 동작 확인

---

## 지원

문제가 있으시면 다음 사항을 확인하세요:

- [ ] `tokenManager.synchronizeServerTime()` 호출함
- [ ] `withCredentials: true` 설정함
- [ ] 서버에서 `/api/auth/server-time` 엔드포인트 구현함
- [ ] 서버에서 `/api/auth/refresh` 엔드포인트 구현함
- [ ] 쿠키에 `httpOnly: true` 설정함
- [ ] HTTPS 환경 (프로덕션)

Happy Coding! 🚀
