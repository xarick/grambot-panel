import { request } from "./client.js";

export const get = (days = 14) => request("GET", `/stats?days=${days}`);
