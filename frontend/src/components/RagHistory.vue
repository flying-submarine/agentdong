<script setup lang="ts">
import { onMounted, toRefs, ref} from "vue";
import { useUserStore } from '@/stores/user.js'
// import PopoverConfirm from '@/components/PopoverConfirm.vue'
import Button from 'primevue/button';
import { RagSessionService } from "@/service/RagChatSession";
import { message } from 'ant-design-vue';
import { globalState } from '@/globalState'; 
import { useGeneratStore } from "@/stores/generat";
import ConfirmDialog from 'primevue/confirmdialog';
import { useConfirm } from "primevue/useconfirm";

const confirm = useConfirm();
const { user } = toRefs(useUserStore())
const confirmDialogVisible = ref(false);
const sessions = ref([])
const isYield = ref(false)
const loading = ref(false)
const current_session = ref()
const generating = useGeneratStore()

const get_sessions = (change = true) => {
  loading.value = true
  RagSessionService.get(user.value, change).then(data => {
    // console.log('获取到raghistory的值：', data);
    sessions.value = data
    if(!data.length){
      globalState.initRagChat()
      on_add_session()
    }
    current_session.value = data.length > 0 ? data[0] : {}
    loading.value = false
  }).catch(_ => {
    loading.value = false
  })
}

const cYield = (status:boolean)=>{
  isYield.value = status
}


const on_add_session = () => {
  if(sessions.value.length > 9 ) return message.warn('Maximum sessions 10');
  RagSessionService.add_session(() => {
    get_sessions()
  });
}

onMounted(() => {
  get_sessions()
  globalState.submitSession = on_add_session
  globalState.changeYield = cYield
  globalState.closeConfirm = cConfirm
})

const cConfirm = ()=>{
  confirmDialogVisible.value = false
}

const select_session = (ss) => {
  if(generating.status) return // chating
  RagSessionService.get(user.value, false).then(data => {
    // console.log('获取到raghistory的值：', data);
    sessions.value = data
    current_session.value =ss
    loading.value = false
    RagSessionService.change_session({ ...ss })
  }).catch(_ => {
    loading.value = false
  })
}

const on_delete_session = (sid) => {
  if(generating.status) return 
  confirmDialogVisible.value = true 
  confirm.require({
    message: 'Do you want to delete this record?',
    header: null,
    icon: 'pi pi-info-circle',
    rejectLabel: 'Cancel',
    rejectProps: {
        label: 'Cancel',
        severity: 'secondary',
        outlined: true
    },
    acceptProps: {
        label: 'Delete',
        severity: 'danger'
    },
    accept: async () => RagSessionService.delete(sid).then(_ => {
      RagSessionService.get(user.value, true).then(data => {
        sessions.value = data
        if(!data.length){
          globalState.initRagChat()
          on_add_session()
          loading.value = false
          confirmDialogVisible.value = false 
        }
        current_session.value = data.length > 0 ? data[0] : {}
        loading.value = false
      }).catch(_ => {
        loading.value = false
        confirmDialogVisible.value = false 
      })
    }),
    reject: () => {
      confirmDialogVisible.value = false;
    }
});
}

</script>

<template>
  <ConfirmDialog v-model:visible="confirmDialogVisible" style="width: 500px;" class="ragH_p" ></ConfirmDialog>
  <div class=" flex flex-column align-items-center p-2 w-full" >
    <Button class="w-12 " icon="pi pi-plus" label="Add Session" :disabled="generating.status" style="font-size: 16px;" @click="on_add_session" />
    <div class="flex flex-column mt-5 w-full ">
      <div 
        @click="select_session(ss)" v-for="ss in sessions"
        :style="generating.status ? { cursor: 'not-allowed' } : { }"
        :class="{ 'his-item flex w-full justify-content-between align-items-center pl-2 pr-2 w-full': true, active: ss.id === current_session?.id }"
      >
        <a-tooltip placement="rightTop" :title="ss.title">
          <p style="width: 80%; white-space: nowrap;overflow: hidden; text-overflow: ellipsis;">{{ ss.title }}</p>
        </a-tooltip>
        <Button @click.stop="on_delete_session(ss.id)" text rounded style="color:#555" icon="pi pi-trash" />
      </div>
    </div>
  </div>
</template>

<style>

.his-item:hover {
  background: rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.his-item{
  opacity: 0.8;
  height: 40px;
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
  overflow: hidden;
  color:#9BA0AA;
  text-overflow: ellipsis;
  letter-spacing: 0.14px;
  border-radius: 5px;
}

.active {
  background: rgba(0, 0, 0, 0.1);
}

</style>
