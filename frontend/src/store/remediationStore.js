import api from "../api/client";

export const getRemediationContext = async (incidentId) => {
  const response = await api.get(`/remediation/incident/${incidentId}/context`);
  return response.data;
};

export const getRemediationRunsForIncident = async (incidentId) => {
  const response = await api.get(`/remediation/incident/${incidentId}`);
  return response.data;
};

export const getRemediationRunLogs = async (remediationRunId) => {
  const response = await api.get(`/remediation/${remediationRunId}/logs`);
  return response.data;
};

export const approveRemediationForIncident = async (incidentId, targetColumn) => {
  const response = await api.post(
    `/remediation/incident/${incidentId}/approve`,
    null,
    {
      params: {
        target_column: targetColumn,
      },
    },
  );
  return response.data;
};

export const rejectRemediationRun = async (remediationRunId) => {
  const response = await api.post(`/remediation/${remediationRunId}/reject`);
  return response.data;
};

export const promoteRemediationCandidate = async (remediationRunId, reviewNotes = "") => {
  const response = await api.post(`/remediation/${remediationRunId}/promote`, null, {
    params: {
      review_notes: reviewNotes || undefined,
    },
  });
  return response.data;
};

export const rejectRemediationCandidate = async (remediationRunId, reviewNotes = "") => {
  const response = await api.post(`/remediation/${remediationRunId}/reject`, null, {
    params: {
      review_notes: reviewNotes || undefined,
    },
  });
  return response.data;
};
