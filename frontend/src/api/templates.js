import { request } from "./client.js";

export const list = () => request("GET", "/templates");

export const create = (data) => request("POST", "/templates", data);

export const update = (id, data) => request("PATCH", `/templates/${id}`, data);

export const remove = (id) => request("DELETE", `/templates/${id}`);
