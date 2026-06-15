import api from "./client";

export async function getSlackStatus() {
  const response = await api.get("/slack/status");
  return response.data;
}

export async function getSlackConnectUrl({ workspaceName, slackTeamId } = {}) {
  const response = await api.get("/slack/connect", {
    params: {
      workspace_name: workspaceName,
      slack_team_id: slackTeamId || undefined,
    },
  });
  return response.data;
}

export async function getSlackChannels() {
  const response = await api.get("/slack/channels");
  return response.data;
}

export async function saveSlackDefaultChannel(channel_id, channel_name) {
  const response = await api.put("/slack/default-channel", {
    channel_id,
    channel_name,
  });
  return response.data;
}

export async function disconnectSlack() {
  const response = await api.delete("/slack/disconnect");
  return response.data;
}
