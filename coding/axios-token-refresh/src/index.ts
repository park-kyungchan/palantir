/**
 * Token Refresh System - Main Entry Point
 * 3가지 해결책이 적용된 TypeScript Axios 인터셉터
 */

// 클라이언트 측 내보내기
export {
  setupAxiosInterceptors,
  initializeAuthClient,
  TokenManager,
  TokenResponse,
  StoredToken,
} from './axiosInterceptor';

// 서버 측 내보내기
export { AuthServer, AuthTokenPayload, RefreshTokenPayload } from './tokenRefreshServer';

// 사용 예제
export {
  initializeApplication,
  login,
  fetchUserData,
  testRaceCondition,
  testTokenExpiration,
  test401Response,
  logout,
  demonstrateCompleteFlow,
} from './usageExample';
