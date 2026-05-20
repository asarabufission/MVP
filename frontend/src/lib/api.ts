import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

import { useAuthStore } from "@/stores/auth-store";
import type { ApiError, LoginResponse } from "@/types/api";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL });

interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    if (!config.headers) {
      config.headers = new AxiosHeaders();
    }
    (config.headers as AxiosHeaders).set("Authorization", `Bearer ${token}`);
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

async function performRefresh(): Promise<string> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) {
    throw new Error("No refresh token");
  }
  const resp = await axios.post<LoginResponse>(
    `${baseURL}/auth/refresh`,
    { refreshToken },
  );
  const { accessToken, refreshToken: newRefresh, user, mspId } = resp.data;
  const rememberMe = useAuthStore.getState().rememberMe;
  useAuthStore.getState().setAuth(
    {
      accessToken,
      refreshToken: newRefresh,
      user,
      mspId,
    },
    rememberMe,
  );
  return accessToken;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const original = error.config as RetryConfig | undefined;
    const status = error.response?.status;
    const code = error.response?.data?.code;

    if (
      status === 401 &&
      code === "TOKEN_EXPIRED" &&
      original &&
      !original._retry &&
      !original.url?.includes("/auth/refresh") &&
      !original.url?.includes("/auth/login")
    ) {
      original._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = performRefresh().finally(() => {
            refreshPromise = null;
          });
        }
        const newAccess = await refreshPromise;
        if (!original.headers) {
          original.headers = new AxiosHeaders();
        }
        (original.headers as AxiosHeaders).set(
          "Authorization",
          `Bearer ${newAccess}`,
        );
        return api.request(original as AxiosRequestConfig);
      } catch (refreshError) {
        useAuthStore.getState().clear();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);
