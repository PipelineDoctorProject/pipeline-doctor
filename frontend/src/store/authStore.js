import { create } from "zustand";
import api from "../api/client";
import { inviteMemberApi } from "../api/invite";

const useAuthStore = create((set) => ({

  user: null,
  isAuthenticated: false,
  workspace:null,
  loading: false,

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

      set({
        isAuthenticated: true,
        loading: false,
      });

      return response.data;

    } catch (error) {

      set({ loading: false });

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

      set({
        isAuthenticated: true,
        loading: false,
      });

      return response.data;

    } catch (error) {

      set({ loading: false });

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

      set({ loading: false });

      return response.data;

    } catch (error) {

      set({ loading: false });

      throw error.response?.data || error;
    }
  },

  logout: async () => {

    try {

      await api.post("/auth/logout");

      set({
        user: null,
        isAuthenticated: false,
      });

    } catch (error) {
      console.log(error);
    }
  },

  me: async () =>{
    try{
      const response = await api.get("/me");
      return response.data

    }catch(error){
      console.log("Details Not Loaded");
      
    }
  }

}));

export default useAuthStore;