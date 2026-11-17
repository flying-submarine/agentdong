import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useTokenStore = defineStore('token', () => {
  const token = ref('');
  const setToken = (nu) => {
    token.value = nu;
  };

  return { token, setToken };
})

