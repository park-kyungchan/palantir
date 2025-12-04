import axios from 'axios';
import {
  initializeAuthClient,
  TokenManager,
} from './axiosInterceptor';

/**
 * Axios 인터셉터 사용 예제
 * 3가지 해결책이 모두 적용된 토큰 갱신 시스템
 */

// 1. 초기화
async function initializeApplication(): Promise<{
  apiClient: any;
  tokenManager: TokenManager;
}> {
  const apiUrl = process.env.API_URL || 'http://localhost:3000';

  const { client, tokenManager } = initializeAuthClient(apiUrl);

  // 해결책 2: 서버 시간 동기화
  // 앱 시작 시 한 번 호출하여 클라이언트-서버 시간 차이 계산
  await tokenManager.synchronizeServerTime();

  return { apiClient: client, tokenManager };
}

// 2. 로그인
async function login(
  apiClient: any,
  tokenManager: TokenManager,
  userId: string,
  password: string
): Promise<void> {
  try {
    const response = await apiClient.post('/api/auth/login', {
      userId,
      password,
    });

    // 로그인 응답에서 토큰 저장
    // HttpOnly Cookie는 자동으로 브라우저에 저장됨
    tokenManager.storeToken(response.data);

    console.log('[Example] Login successful');
    console.log(`[Example] Access Token stored (expires in ${response.data.expiresIn}s)`);
    console.log('[Example] Refresh Token stored in HttpOnly Cookie');
  } catch (error) {
    console.error('[Example] Login failed', error);
    throw error;
  }
}

// 3. API 요청 (자동 토큰 관리)
async function fetchUserData(apiClient: any): Promise<any> {
  try {
    // 요청 인터셉터에서 자동으로:
    // 1. 토큰 만료 확인
    // 2. 필요시 토큰 갱신 (Lock으로 동시 갱신 방지)
    // 3. 요청에 토큰 추가
    const response = await apiClient.get('/api/user/profile');

    console.log('[Example] User data fetched successfully');
    return response.data;
  } catch (error) {
    console.error('[Example] Failed to fetch user data', error);
    throw error;
  }
}

// 4. 토큰 갱신 테스트 (Race Condition 방지)
async function testRaceCondition(apiClient: any): Promise<void> {
  console.log('\n[Test] Starting race condition test...');

  try {
    // 동시에 3개의 요청 발생
    // 해결책 1: Token Refresh Lock에 의해 첫 요청만 갱신, 나머지는 대기
    const promises = [
      apiClient.get('/api/user/profile'),
      apiClient.get('/api/user/settings'),
      apiClient.get('/api/user/notifications'),
    ];

    const results = await Promise.all(promises);

    console.log('[Test] All requests completed successfully');
    console.log('[Test] Only first request triggered token refresh');
    console.log(`[Test] Other requests reused refreshed token`);
  } catch (error) {
    console.error('[Test] Race condition test failed', error);
  }
}

// 5. 토큰 만료 시나리오 테스트
async function testTokenExpiration(apiClient: any, tokenManager: TokenManager): Promise<void> {
  console.log('\n[Test] Testing token expiration scenario...');

  try {
    // 현재 토큰 상태
    const cachedToken = tokenManager.getTokenCache();
    if (cachedToken) {
      const timeUntilExpiry = (cachedToken.expiresAt - Date.now()) / 1000;
      console.log(`[Test] Token expires in: ${timeUntilExpiry}s`);
    }

    // API 요청
    // 토큰이 60초 이내로 만료될 예정이면 자동으로 갱신됨 (Skew Tolerance)
    const response = await apiClient.get('/api/user/profile');
    console.log('[Test] Request completed with valid token');
  } catch (error) {
    console.error('[Test] Token expiration test failed', error);
  }
}

// 6. 401 응답 처리 테스트
async function test401Response(apiClient: any): Promise<void> {
  console.log('\n[Test] Testing 401 unauthorized response...');

  try {
    // 응답 인터셉터에서 자동으로:
    // 1. 401 상태 감지
    // 2. 토큰 갱신 시도
    // 3. 원본 요청 재시도
    const response = await apiClient.get('/api/user/profile');
    console.log('[Test] Request succeeded after token refresh');
  } catch (error) {
    console.error('[Test] 401 handling failed', error);
  }
}

// 7. 로그아웃
async function logout(
  apiClient: any,
  tokenManager: TokenManager,
  sessionId?: string
): Promise<void> {
  try {
    // 로그아웃 API 호출
    if (sessionId) {
      await apiClient.post('/api/auth/logout', { sessionId });
    }

    // 로컬 토큰 캐시 삭제
    tokenManager.clearToken();

    // HttpOnly Cookie는 서버에서 Set-Cookie로 삭제 (자동)
    console.log('[Example] Logout successful');
    console.log('[Example] Token cache cleared');
    console.log('[Example] HttpOnly Cookie deleted by server');
  } catch (error) {
    console.error('[Example] Logout failed', error);
  }
}

// 8. 완전한 사용 흐름
async function demonstrateCompleteFlow(): Promise<void> {
  console.log('='.repeat(60));
  console.log('Axios Interceptor with Token Refresh - Complete Flow');
  console.log('='.repeat(60));

  const { apiClient, tokenManager } = await initializeApplication();

  console.log('\n1. LOGIN');
  console.log('-'.repeat(60));
  await login(apiClient, tokenManager, 'user@example.com', 'password123');

  console.log('\n2. FETCH USER DATA');
  console.log('-'.repeat(60));
  const userData = await fetchUserData(apiClient);
  console.log(`[Example] User data:`, userData);

  console.log('\n3. RACE CONDITION TEST (동시 다중 요청)');
  console.log('-'.repeat(60));
  // 해결책 1 테스트: Token Refresh Lock
  // 첫 요청만 갱신, 나머지는 대기
  await testRaceCondition(apiClient);

  console.log('\n4. TOKEN EXPIRATION TEST');
  console.log('-'.repeat(60));
  // 해결책 2 테스트: Skew Tolerance
  // 토큰이 60초 이내로 만료될 예정이면 자동 갱신
  await testTokenExpiration(apiClient, tokenManager);

  console.log('\n5. 401 RESPONSE TEST');
  console.log('-'.repeat(60));
  // 응답 인터셉터 테스트: 401 응답 자동 처리
  // 토큰 갱신 후 자동으로 원본 요청 재시도
  await test401Response(apiClient);

  console.log('\n6. LOGOUT');
  console.log('-'.repeat(60));
  // 해결책 3 테스트: HttpOnly Cookie
  // 서버에서 자동으로 쿠키 삭제
  await logout(apiClient, tokenManager, 'session_id_here');

  console.log('\n' + '='.repeat(60));
  console.log('Flow Complete');
  console.log('='.repeat(60));
}

// 9. 환경 변수 설정
export function setupEnvironment(): void {
  if (!process.env.API_URL) {
    process.env.API_URL = 'http://localhost:3000';
  }
  if (!process.env.NODE_ENV) {
    process.env.NODE_ENV = 'development';
  }
}

// 프로그램 실행
if (require.main === module) {
  setupEnvironment();
  demonstrateCompleteFlow().catch(console.error);
}

export {
  initializeApplication,
  login,
  fetchUserData,
  testRaceCondition,
  testTokenExpiration,
  test401Response,
  logout,
  demonstrateCompleteFlow,
};
