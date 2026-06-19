import { request, upload } from "./client.js";

export const listByBot = (botId, { tag, search, limit = 50, offset = 0 } = {}) => {
  const params = new URLSearchParams();
  if (tag) params.set("tag", tag);
  if (search) params.set("search", search);
  params.set("limit", limit);
  params.set("offset", offset);
  return request("GET", `/bots/${botId}/conversations?${params}`);
};

export const get = (id) => request("GET", `/conversations/${id}`);

export const update = (id, data) => request("PATCH", `/conversations/${id}`, data);

export const getMessages = (id, after = 0, before = 0) => {
  const params = new URLSearchParams();
  if (after) params.set("after", after);
  else if (before) params.set("before", before);
  return request("GET", `/conversations/${id}/messages${params.size ? `?${params}` : ""}`);
};

export const reply = (id, text) => request("POST", `/conversations/${id}/reply`, { text });

export const replyPhoto = (id, file, caption = "") => {
  const fd = new FormData();
  fd.append("file", file);
  if (caption) fd.append("caption", caption);
  return upload(`/conversations/${id}/reply-photo`, fd);
};

export const blockUser = (id, isBlocked) =>
  request("PATCH", `/conversations/${id}/block`, { is_blocked: isBlocked });
