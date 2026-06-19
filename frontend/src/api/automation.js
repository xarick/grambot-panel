import { request } from "./client.js";

export const listReplies = (botId) => request("GET", `/automation/auto-replies?bot_id=${botId}`);

export const createReply = (data) => request("POST", "/automation/auto-replies", data);

export const deleteReply = (id) => request("DELETE", `/automation/auto-replies/${id}`);

export const getWelcome = (botId) => request("GET", `/automation/welcome?bot_id=${botId}`);

export const setWelcome = (botId, welcome) =>
  request("PUT", `/automation/welcome?bot_id=${botId}`, { welcome });
