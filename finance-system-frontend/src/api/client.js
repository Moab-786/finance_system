import axios from "axios";
import {
  clearAuthSession,
  getAccessToken,
  getRefreshToken,
  setAuthSession,
} from "./tokenStorage";

const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

let refreshInFlight = null;

function parseJwtRole(token) {
  if (!token) {
    return null;
  }

  try {
    const payload = token.split(".")[1];
    const decoded = JSON.parse(
      atob(payload.replace(/-/g, "+").replace(/_/g, "/")),
    );
    return decoded.role || null;
  } catch {
    return null;
  }
}

async function refreshAccessToken() {
  if (!refreshInFlight) {
    refreshInFlight = axios
      .post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: getRefreshToken(),
      })
      .then((response) => {
        const accessToken = response.data.access_token;
        const role = parseJwtRole(accessToken);
        setAuthSession({ accessToken, role });
        return accessToken;
      })
      .catch((error) => {
        clearAuthSession();
        throw error;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }

  return refreshInFlight;
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error?.response?.status;

    if (
      status === 401 &&
      !originalRequest._retry &&
      getRefreshToken() &&
      !originalRequest.url?.includes("/auth/refresh")
    ) {
      originalRequest._retry = true;
      const newAccessToken = await refreshAccessToken();
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return api(originalRequest);
    }

    throw error;
  },
);

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export function decodeRoleFromToken(token) {
  return parseJwtRole(token);
}
