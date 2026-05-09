import axios from "axios";

import { getAccessToken, setAccessToken, redirectToLogin } from "../stores/session";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  withCredentials: true,
});

client.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as any;
    const status = error.response?.status;
    const requestUrl = original?.url || "";
    const authHeader =
      original?.headers?.Authorization ??
      original?.headers?.authorization ??
      (typeof original?.headers?.get === "function" ? original.headers.get("Authorization") : undefined);
    const hadAuthHeader = Boolean(authHeader);
    const isAuthEndpoint = ["/auth/login/", "/auth/register/", "/auth/google/", "/auth/logout/", "/auth/refresh/"].some(
      (path) => requestUrl.includes(path),
    );

    if (status === 401 && hadAuthHeader && !original?._retry && !isAuthEndpoint) {
      original._retry = true;
      try {
        const { data } = await client.post("/auth/refresh/");
        setAccessToken(data.access);
        original.headers = original.headers || {};
        original.headers.Authorization = `Bearer ${data.access}`;
        return client(original);
      } catch (refreshError: any) {
        const refreshStatus = refreshError?.response?.status;
        if (refreshStatus && refreshStatus < 500) {
          redirectToLogin("invalid");
        }
        return Promise.reject(error);
      }
    }

    if (status === 401 && hadAuthHeader && original?._retry && !isAuthEndpoint) {
      redirectToLogin("invalid");
    }

    return Promise.reject(error);
  },
);

export default client;
