import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useGeneratStore = defineStore('status', () => {
  const status = ref(false);
  const setStatus = (nu) => {
    status.value = nu;
  };

  return { status, setStatus };
})

