import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true,
});




api.interceptors.response.use(

  (response) => response,

  async (error) => {

    const originalRequest = error.config;

    // Access token expired
    if (
      error.response?.status === 401 &&
      !originalRequest._retry
    ) {

      originalRequest._retry = true;

      try {

        // Request new access token
        await api.post("/auth/refresh");

        // Retry original request
        return api(originalRequest);

      } catch (refreshError) {

        console.log("Refresh token expired");

        window.location.href = "/login";

        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;