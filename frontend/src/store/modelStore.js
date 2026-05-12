import api from "../api/client";

export const discoverModels = async (
  trackingUri
) => {

  const response = await api.post(
    "/ml-models/discover",
    {
      tracking_uri: trackingUri,
    }
  );

  return response.data;
};

export const getModelVersions =
  async (
    trackingUri,
    modelName
  ) => {

    const response = await api.post(
      "/ml-models/versions",
      {
        tracking_uri: trackingUri,
        model_name: modelName,
      }
    );

    return response.data;
};

export const registerModel = async (
  payload
) => {

  const response = await api.post(
    "/ml-models/",
    payload
  );

  return response.data;
};