import { create } from "zustand";

const STORAGE_KEY = "pipeline-doctor:selected-model-id";

function readInitialModelId() {
  if (typeof window === "undefined") return "all";
  return window.localStorage.getItem(STORAGE_KEY) || "all";
}

const useSelectedModelStore = create((set) => ({
  selectedModelId: readInitialModelId(),
  setSelectedModelId: (modelId) => {
    const value = modelId || "all";
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, value);
    }
    set({ selectedModelId: value });
  },
}));

export default useSelectedModelStore;
