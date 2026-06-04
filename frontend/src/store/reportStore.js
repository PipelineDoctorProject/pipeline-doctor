import api from "../api/client";

export async function getLatestIncidentReport(incidentId) {
  const response = await api.get(`/reports/incidents/${incidentId}/latest`);
  return response.data;
}

export async function getIncidentReport(reportId) {
  const response = await api.get(`/reports/${reportId}`);
  return response.data;
}

export async function getIncidentReportVersions(incidentId) {
  const response = await api.get(`/reports/incidents/${incidentId}`);
  return response.data;
}
