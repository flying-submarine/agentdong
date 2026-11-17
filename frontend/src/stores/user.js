import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', () => {
  const user = ref('');
  const setUser = (nu) => {
    console.log(nu)
    user.value = nu;
  };

  return { user, setUser };
})

export const useRoleLoginList = defineStore('roleLoginList', () => {
  const roleLoginList = ref([]);
  const setRoleLoginList = (nu) => {
    console.log(nu)
    roleLoginList.value = nu;
  };

  return { roleLoginList, setRoleLoginList };
})
