<script setup lang="ts">
import { LongReportSummarizationSession } from "@/service/LongReportSummarizationSession";
import { onMounted, toRefs, ref } from "vue";
import { useUserStore } from '@/stores/user.js'
import PopoverConfirm from '@/components/PopoverConfirm.vue'
import { watch } from "vue";
import { globalState } from '@/globalState'; 
// interface Props {
//   session?: string;
// }

// const props = defineProps<Props>();

const { user } = toRefs(useUserStore())

const count = ref(0)
const sessions = ref([])
const loading = ref(false)
const get_sessions = (change: boolean = true) => {
  loading.value = true
  LongReportSummarizationSession.get('longtext',user.value, change).then(data => {
    console.log('获取到的值：',data);
    
    sessions.value = data
    current_session.value = data.length > 0 ? data[0] : {}
    loading.value = false
  }).catch(_ => {
    loading.value = false
  })
}
globalState.refreshSessionHandler = get_sessions;
const on_add_session = () => {
    LongReportSummarizationSession.add_session(() => {
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
const props = defineProps({
  entry: Object
});

// 要执行的函数
const doSomethingWithEntry = (newValue, oldValue) => {
    LongReportSummarizationSession.add_session(() => {
    get_sessions()
  });
};

// Watcher
watch(() => props.entry, (newEntry, oldEntry) => {
  doSomethingWithEntry(newEntry, oldEntry);
});

const confirm = ref<InstanceType<typeof PopoverConfirm> | null>(null)
const on_delete_session = (event, sid) => {
  confirm.value.show({
    label: 'Do you want to delete this record?',
    accept: () => LongReportSummarizationSession.delete('longtext',sid).then(_ => get_sessions()),
    event,
  })
}

const current_session = ref()
const select_session = (ss,index) => {
  count.value = index
  console.log(count.value);
  
  current_session.value = ss
  LongReportSummarizationSession.change_session({ ...ss })
}

</script>

<template>
  <PopoverConfirm ref="confirm" />
  <div class="flex flex-column align-items-center p-2 w-full">
    <Button class="w-12 mt-5" icon="pi pi-plus" label="Add Session" rounded @click="on_add_session" />
    <div class="flex flex-column mt-5 w-full">
      <div @click="select_session(ss,index)" v-for="(ss,index) in sessions"
        :class="{ 'his-item flex w-full justify-content-between align-items-center pl-2 pr-2 w-full': true, active: ss.id === current_session?.id }"
        style="height: 40px;font-size: 12px;overflow: hidden; text-overflow: ellipsis;">
        <!-- <p style="width: 80%;">{{ ss.title }}</p> -->
        <a-tooltip placement="rightTop" :title="ss.title">
          <p style="width: 80%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{{ ss.title }}</p>
        </a-tooltip>
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
