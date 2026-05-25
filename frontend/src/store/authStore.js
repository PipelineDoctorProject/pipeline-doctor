import { create } from "zustand";
import api, { setAccessToken } from "../api/client";
import { inviteMemberApi } from "../api/invite";

const useAuthStore = create((set, get) => ({

  user: null,
  isAuthenticated: false,
  workspace: null,
  dashboardData: null,
  loading: false,
  checkingAuth: true,
  onboardingStep: 1,

  signup: async (email, password) => {

    set({ loading: true });

    try {

      const response = await api.post("/auth/signup", {
        email,
        password,
      });

      set({ loading: false });

      return response.data;

    } catch (error) {

      set({ loading: false });

      throw error.response?.data || error;
    }
  },

  inviteMember: async (email) => {

    try {

      const data = await inviteMemberApi(email);

      return data;

    } catch (err) {

      throw err.response?.data || err;
    }
  },

  verifyOtp: async (email, otp) => {

    set({ loading: true });

    try {

      const response = await api.post("/auth/verify-otp", {
        email,
        otp,
      });

      setAccessToken(response.data?.access_token);

      await get().me();

      set({
        loading: false,
      });

      return response.data;

    } catch (error) {

      set({
        loading: false,
      });

      throw error.response?.data || error;
    }
  },

  login: async (email, password) => {

    set({ loading: true });

    try {

      const response = await api.post("/auth/login", {
        email,
        password,
      });

      setAccessToken(response.data?.access_token);

      await get().me();

      set({
        loading: false,
      });

      return response.data;

    } catch (error) {

      setAccessToken(null);
      set({
        loading: false,
      });

      throw error.response?.data || error;
    }
  },

  createCompany: async (company_name) => {

  set({ loading: true });

  try {

    const response = await api.post(
      "/onboarding/company",
      {
        company_name,
      }
    );

    await get().me();

    set({
      loading: false,
      onboardingStep: 2,
    });

    return response.data;

  } catch (error) {

    set({ loading: false });

    throw error.response?.data || error;
  }
},
  logout: async () => {

    try {

      await api.post("/auth/logout");

    } catch (error) {

      console.log(error);
    }

    setAccessToken(null);
    set({
      user: null,
      isAuthenticated: false,
      workspace: null,
      dashboardData: null,
      checkingAuth: false,
    });

    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  },

  me: async () => {

    try {

      const response = await api.get(
        "/dashboard/me",
        {
          skipAuthRefresh: true,
        }
      );

      set({
        user: response.data.user,
        workspace: response.data.workspace,
        dashboardData: response.data,
        isAuthenticated: true,
        checkingAuth: false,
      });

      return response.data;

    } catch (error) {

      set({
        user: null,
        workspace: null,
        dashboardData: null,
        isAuthenticated: false,
        checkingAuth: false,
      });

      return null;
    }
  },
}));

export default useAuthStore;
