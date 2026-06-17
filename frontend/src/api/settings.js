import { request } from "./client.js";

export const get = () => request("GET", "/settings");

export const update = (data) => request("PUT", "/settings", data);
