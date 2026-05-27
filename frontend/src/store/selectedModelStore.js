import { create } from "zustand";

const STORAGE_KEY_PREFIX = "pipeline-doctor:selected-model-id";

function buildStorageKey(scope) {
  return scope ? `${STORAGE_KEY_PREFIX}:${scope}` : STORAGE_KEY_PREFIX;
}

function readScopedModelId(scope) {
  if (typeof window === "undefined") return "all";
  return window.localStorage.getItem(buildStorageKey(scope)) || "all";
}

const useSelectedModelStore = create((set, get) => ({
  selectedModelId: "all",
  selectionScope: null,
  hydrateSelectionScope: (scope) => {
    const normalizedScope = scope || null;

    if (get().selectionScope === normalizedScope) {
      return;
    }

    set({
      selectionScope: normalizedScope,
      selectedModelId: readScopedModelId(normalizedScope),
    });
  },
  setSelectedModelId: (modelId) => {
    const value = modelId || "all";

    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        buildStorageKey(get().selectionScope),
        value,
      );
    }

    set({ selectedModelId: value });
  },
}));

export default useSelectedModelStore;
