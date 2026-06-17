import { request } from "./client.js";

export const list = () => request("GET", "/users");

export const create = (data) => request("POST", "/users", data);

export const update = (id, data) => request("PATCH", `/users/${id}`, data);

export const remove = (id) => request("DELETE", `/users/${id}`);
