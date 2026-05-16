import api from "./client";

export const inviteMemberApi = async (email) => {

  const response = await api.post(
    "/invite/member",
    {
      email
    }
  );

  return response.data;
};