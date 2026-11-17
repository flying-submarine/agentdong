import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useModelStore = defineStore('model', () => {
  const currentModel = ref("llama2:latest");
  const setCurrentModel = (newModel) => {
    currentModel.value = newModel;
  };

  return { currentModel, setCurrentModel };
})

