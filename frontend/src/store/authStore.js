import { create } from "zustand";
import api, { hasAccessToken, setAccessToken } from "../api/client";
import { inviteMemberApi } from "../api/invite";

const useAuthStore = create((set, get) => ({

  user: null,
  isAuthenticated: false,
  workspace: null,
  dashboardData: null,
  loading: false,
  checkingAuth: true,
  onboardingStep: 1,
  authCheckVersion: 0,

  bootstrapAuth: async () => {

    if (!hasAccessToken()) {
      set({
        user: null,
        isAuthenticated: false,
        workspace: null,
        dashboardData: null,
        checkingAuth: false,
      });

      return null;
    }

    return get().me();
  },

  signup: async (email, password) => {

    set({ loading: true });

    try {
      const normalizedEmail = email.trim().toLowerCase();

      const response = await api.post("/auth/signup", {
        email: normalizedEmail,
        password,
      }, {
        timeout: 60000,
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
      const normalizedEmail = email.trim().toLowerCase();
      const normalizedOtp = String(otp).replace(/\s/g, "");

      const response = await api.post("/auth/verify-otp", {
        email: normalizedEmail,
        otp: normalizedOtp,
      });

      setAccessToken(response.data?.access_token);

      const dashboardContext = await get().me();

      if (!dashboardContext) {
        throw {
          detail: "We verified your OTP, but could not load your workspace session.",
        };
      }

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

  resendOtp: async (email) => {

    try {
      const normalizedEmail = email.trim().toLowerCase();

      const response = await api.post("/auth/resend-otp", {
        email: normalizedEmail,
      }, {
        timeout: 60000,
      });

      return response.data;

    } catch (error) {

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

      const dashboardContext = await get().me();

      if (!dashboardContext) {
        throw {
          detail: "Login succeeded, but we could not load your workspace session.",
        };
      }

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

    setAccessToken(response.data?.access_token);

    const workspace = {
      tenant_id: response.data?.tenant_id,
      workspace_name: response.data?.workspace_name || company_name,
      schema_name: response.data?.schema_name,
    };

    set((state) => ({
      loading: false,
      onboardingStep: 2,
      isAuthenticated: true,
      checkingAuth: false,
      workspace,
      dashboardData: {
        ...(state.dashboardData || {}),
        user: state.user || state.dashboardData?.user || null,
        workspace,
        is_onboarded: true,
      },
    }));

    const dashboardContext = await get().me();

    if (!dashboardContext) {
      set((state) => ({
        user: state.user || state.dashboardData?.user || null,
        isAuthenticated: true,
        checkingAuth: false,
        workspace,
        dashboardData: {
          ...(state.dashboardData || {}),
          user: state.user || state.dashboardData?.user || null,
          workspace,
          is_onboarded: true,
        },
      }));
    }

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
    const authCheckVersion = get().authCheckVersion + 1;

    set({ authCheckVersion });

    try {

      const response = await api.get(
        "/dashboard/me",
        {
          skipAuthRefresh: true,
        }
      );

      if (get().authCheckVersion !== authCheckVersion) {
        return response.data;
      }

      set({
        user: response.data.user,
        workspace: response.data.workspace,
        dashboardData: response.data,
        isAuthenticated: true,
        checkingAuth: false,
      });

      return response.data;

    } catch (error) {
      if (get().authCheckVersion !== authCheckVersion) {
        return null;
      }

      if (error?.response?.status === 401) {
        setAccessToken(null);
      }

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
