import api from "../api/client";

// Fetches the list of AgentRun records for a given incident
// GET /incidents/{incident_id}/agent-runs
export async function getIncidentAgentRuns(incidentId) {
  const response = await api.get(`/incidents/${incidentId}/agent-runs`);
  return response.data;
}

// Fetches the step logs for a given agent run
// GET /incidents/agent-runs/{agent_run_id}/steps
export async function getAgentRunSteps(agentRunId) {
  const response = await api.get(`/incidents/agent-runs/${agentRunId}/steps`);
  return response.data;
}
