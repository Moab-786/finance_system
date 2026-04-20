const ACCESS_TOKEN_KEY = "fintrack_access_token";
const REFRESH_TOKEN_KEY = "fintrack_refresh_token";
const ROLE_KEY = "fintrack_user_role";

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function getStoredRole() {
  return localStorage.getItem(ROLE_KEY);
}

export function setAuthSession({ accessToken, refreshToken, role }) {
  if (accessToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  }
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
  if (role) {
    localStorage.setItem(ROLE_KEY, role);
  }
}

export function clearAuthSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
}
