import axios from "axios";
import { API_BASE_URL } from "../config/runtime";

const ACCESS_TOKEN_KEY = "opssight_access_token";

export function setAccessToken(token) {
  if (token) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  }
}

function getAccessToken() {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export { getAccessToken };

export function hasAccessToken() {
  return Boolean(getAccessToken());
}

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: 60000,
});

let refreshPromise = null;

api.interceptors.request.use((config) => {
  const token = getAccessToken();

  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,

  async (error) => {

    const originalRequest = error.config || {};

    // routes that should NEVER trigger refresh
    const excludedRoutes = [
      "/auth/login",
      "/auth/signup",
      "/auth/verify-otp",
      "/auth/refresh",
    ];

    // stop if not 401
    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    // allow callers like /dashboard/me on the login page to fail quietly
    if (originalRequest.skipAuthRefresh) {
      setAccessToken(null);
      return Promise.reject(error);
    }

    // stop if excluded route
    if (excludedRoutes.includes(originalRequest.url)) {
      return Promise.reject(error);
    }

    // stop retry loop
    if (originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {

      // try refresh token
      if (!refreshPromise) {
        refreshPromise = api
          .post("/auth/refresh")
          .finally(() => {
            refreshPromise = null;
          });
      }

      const refreshResponse = await refreshPromise;
      if (refreshResponse.data?.access_token) {
        setAccessToken(refreshResponse.data.access_token);
      }

      // retry original request
      return api(originalRequest);

    } catch (refreshError) {

      console.log("Refresh token expired");
      setAccessToken(null);

      // avoid redirect loop
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }

      return Promise.reject(refreshError);
    }
  }
);

export default api;
