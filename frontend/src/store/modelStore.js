import api from "../api/client";


// =====================================================
// DISCOVER MODELS
// =====================================================
export const discoverModels = async (
  trackingUri
) => {

  try {

    const response = await api.post(
      "/ml-models/discover",
      {
        tracking_uri: trackingUri,
      }
    );

    return response.data;

  } catch (error) {

    throw (
      error.response?.data ||
      error
    );
  }
};


// =====================================================
// GET MODEL VERSIONS
// =====================================================
export const getModelVersions = async (
  trackingUri,
  modelName
) => {

  try {

    const response = await api.post(
      "/ml-models/versions",
      {
        tracking_uri: trackingUri,
        model_name: modelName,
      }
    );

    return response.data;

  } catch (error) {

    throw (
      error.response?.data ||
      error
    );
  }
};


// =====================================================
// REGISTER MODEL
// =====================================================
export const registerModel = async (
  payload
) => {

  try {

    const response = await api.post(
      "/ml-models/",
      payload
    );

    return response.data;

  } catch (error) {

    throw (
      error.response?.data ||
      error
    );
  }
};

export const getModels = async () => {

  try {

    const response = await api.get(
      "/ml-models/"
    );

    return response.data;

  } catch (error) {

    throw (
      error.response?.data ||
      error
    );
  }
};