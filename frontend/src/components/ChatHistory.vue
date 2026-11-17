<script setup lang="ts">
import { ChatSessionService } from "@/service/ChatSession";
import { onMounted, toRefs, ref } from "vue";
import { useUserStore } from '@/stores/user.js'
import PopoverConfirm from '@/components/PopoverConfirm.vue'
import { watch } from "vue";
// interface Props {
//   session?: string;
// }

// const props = defineProps<Props>();

const { user } = toRefs(useUserStore())


const sessions = ref([])
const loading = ref(false)
const get_sessions = (change: boolean = true) => {
  loading.value = true
  ChatSessionService.get(user.value, change).then(data => {
    sessions.value = data
    current_session.value = data.length > 0 ? data[0] : {}
    loading.value = false
  }).catch(_ => {
    loading.value = false
  })
}

const on_add_session = () => {
  ChatSessionService.add_session(() => {
    get_sessions()
  });
}

watch(user, () => {
  get_sessions()
  on_add_session()
})

onMounted(() => {
  get_sessions()
})

const confirm = ref<InstanceType<typeof PopoverConfirm> | null>(null)
const on_delete_session = (event, sid) => {
  confirm.value.show({
    label: 'Do you want to delete this record?',
    accept: () => ChatSessionService.delete(sid).then(_ => get_sessions()),
    event,
  })
}

const current_session = ref()
const select_session = (ss) => {
  current_session.value = ss
  ChatSessionService.change_session({ ...ss })
}

</script>

<template>
  <PopoverConfirm ref="confirm" />
  <div class="flex flex-column align-items-center p-2 w-full">
    <Button class="w-12 mt-5" icon="pi pi-plus" label="Add Session" rounded @click="on_add_session" />
    <div class="flex flex-column mt-5 w-full">
      <div @click="select_session(ss)" v-for="ss in sessions"
        :class="{ 'his-item flex w-full justify-content-between align-items-center pl-2 pr-2 w-full': true, active: ss.id === current_session?.id }"
        style="height: 40px;font-size: 12px;overflow: hidden; text-overflow: ellipsis;">
        <p style="width: 80%;">{{ ss.title }}</p>
        <Button @click.stop="on_delete_session($event, ss.id)" text rounded style="color:#555" icon="pi pi-trash" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.his-item:hover {
  background: rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.active {
  background: rgba(0, 0, 0, 0.1);
}
</style>
