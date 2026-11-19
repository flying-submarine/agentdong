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
  <div class="history-panel">
    <div class="history-head">
      <h2 class="history-title">对话历史</h2>
      <span class="history-count">{{ sessions.length }}</span>
    </div>

    <div class="history-actions">
      <Button
        class="new-session-btn"
        icon="pi pi-plus"
        label="新建会话"
        :disabled="generating.status"
        @click="on_add_session"
      />
    </div>

    <div class="history-list">
      <p v-if="!sessions.length" class="history-empty">还没有会话，点击上方新建</p>
      <div
        v-for="ss in sessions"
        :key="ss.id"
        class="his-item"
        :class="{ active: ss.id === current_session?.id, disabled: generating.status }"
        @click="select_session(ss)"
      >
        <a-tooltip placement="rightTop" :title="ss.title">
          <i class="pi pi-comments his-icon"></i>
          <span class="his-label">{{ ss.title }}</span>
        </a-tooltip>
        <Button
          class="his-delete"
          @click.stop="on_delete_session(ss.id)"
          text
          rounded
          icon="pi pi-trash"
          aria-label="删除会话"
        />
      </div>
    </div>
  </div>
</template>

<style>
.history-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-height: 0;
  padding: 18px 12px;
}
.history-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
}
.history-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text);
}
.history-count {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--app-surface-3);
  color: var(--app-text-2);
  font-size: 12px;
  line-height: 20px;
  text-align: center;
}
.history-actions {
  padding: 16px 4px 18px;
}
.new-session-btn.p-button {
  width: 100%;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  height: 40px;
}
.history-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.history-empty {
  padding: 24px 8px;
  text-align: center;
  color: var(--app-text-3);
  font-size: 13px;
}
.his-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 8px 8px 8px 10px;
  border-radius: 8px;
  color: var(--app-text-2);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.his-item:hover {
  background: var(--app-surface-3);
}
.his-item.active {
  background: var(--app-primary-soft);
  color: var(--app-primary);
  font-weight: 600;
}
.his-item.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.his-icon {
  font-size: 13px;
  flex: 0 0 auto;
  opacity: 0.7;
}
.his-label {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.his-delete.p-button {
  width: 26px;
  height: 26px;
  flex: 0 0 26px;
  color: var(--app-text-3);
  opacity: 0;
}
.his-item:hover .his-delete.p-button {
  opacity: 1;
}
.his-delete.p-button:hover {
  color: var(--app-danger);
  background: #fef3f2;
}
</style>
