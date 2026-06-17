import { request } from "./client.js";

export const list = ({ limit = 20, offset = 0 } = {}) =>
  request("GET", `/broadcast?limit=${limit}&offset=${offset}`);

export const create = (data) => request("POST", "/broadcast", data);

export const recipients = (botId) =>
  request("GET", `/broadcast/recipients?bot_id=${botId}`);

export const uploadMedia = async (file) => {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch("/api/v1/broadcast/media", {
    method: "POST",
    credentials: "include",
    body: fd,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw { detail };
  }
  return res.json();
};

export const status = (id) => request("GET", `/broadcast/${id}`);

export const cancel = (id) => request("POST", `/broadcast/${id}/cancel`);

export const remove = (id) => request("DELETE", `/broadcast/${id}`);
