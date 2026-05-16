import api from "../api/client";

export const getDriftFindings = async () => {
  const response = await api.get("/drift-findings/");
  return response.data;
};
