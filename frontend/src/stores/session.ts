const ACCESS_TOKEN_KEY = "postalia_access_token";

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);
export const setAccessToken = (token: string) => localStorage.setItem(ACCESS_TOKEN_KEY, token);
export const clearSession = () => localStorage.removeItem(ACCESS_TOKEN_KEY);

export function redirectToLogin(reason = "invalid") {
  clearSession();
  if (typeof window === "undefined") return;

  const loginUrl = new URL("/login", window.location.origin);
  loginUrl.searchParams.set("session", reason);
  window.location.replace(loginUrl.toString());
}
