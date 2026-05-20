import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true,
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,

  async (error) => {

    const originalRequest = error.config;

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
      await api.post("/auth/refresh");

      // retry original request
      return api(originalRequest);

    } catch (refreshError) {

      console.log("Refresh token expired");

      // avoid redirect loop
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }

      return Promise.reject(refreshError);
    }
  }
);

export default api;
