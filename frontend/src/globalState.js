// src/globalState.js

import { reactive } from 'vue';

export const globalState = reactive({
    refreshSessionHandler: null,
    initRagChat:null,
    submitSession:null,
    changeYield:null,
    closeConfirm:()=>{}
});
