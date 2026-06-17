import { request } from "./client.js";

export const list = () => request("GET", "/bots");

export const create = (data) => request("POST", "/bots", data);

export const update = (id, data) => request("PATCH", `/bots/${id}`, data);

export const remove = (id) => request("DELETE", `/bots/${id}`);

export const listChats = (botId) => request("GET", `/bots/${botId}/chats`);

export const chatInfo = (botId, chatRowId) =>
  request("GET", `/bots/${botId}/chats/${chatRowId}/info`);

export const refreshChat = (botId, chatRowId) =>
  request("POST", `/bots/${botId}/chats/${chatRowId}/refresh`);
