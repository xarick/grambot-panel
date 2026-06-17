import { request } from "./client.js";

export const login = (username, password) =>
  request("POST", "/auth/login", { username, password });

export const logout = () => request("POST", "/auth/logout");

export const me = () => request("GET", "/auth/me");

export const updateProfile = (data) => request("PATCH", "/auth/me", data);

export const loginPath = () => request("GET", "/auth/login-path");
