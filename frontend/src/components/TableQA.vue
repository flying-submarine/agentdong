<script setup lang="ts">
import { onMounted, toRefs, ref, nextTick } from "vue";
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Paginator from 'primevue/paginator'
import PanelMenu from 'primevue/panelmenu'
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import { TableQAService } from '@/service/TableQA'
import ChatBox from "./ChatBox.vue";
import ChatHistory from '@/components/ChatHistory.vue'
import Drawer from 'primevue/drawer'
import MarkdownRenderer from "./MarkdownRenderer.vue";
import CsvTable from "./CsvTable.vue";
import ProgressSpinner from 'primevue/progressspinner'
import ProgressBar from 'primevue/progressbar'
import Tag from 'primevue/tag'
import MultiSelect from 'primevue/multiselect'
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import "prismjs/themes/prism.css"

// const Prism = require('prismjs');
// const loadLanguages = require('prismjs/components/');
// loadLanguages(['python']);


import { get_local_file, upload_req } from '@/service/utils'
import { useUserStore } from "@/stores/user";

const { user } = toRefs(useUserStore())

const menu_items = ref([])
const current_table = ref()
const multi_table = ref()
const get_menu_items = async () => {
  const d = await TableQAService.get_menu_items()
  menu_items.value = d
  d.length > 0 && (current_table.value = d[0])
  if (current_table.value?.urls) {
    multi_table.value = current_table.value.urls
  }
}



const csv_table = ref<InstanceType<typeof CsvTable> | null>(null)
const show_csv = async () => {
  if (!current_table.value?.urls) {
    multi_table.value = null
  }
  if (multi_table.value == null && current_table.value?.urls) {
    multi_table.value = current_table.value.urls
    await get_question()
  }

  if (current_table.value?.urls) {
    csv_table.value.show_csv(multi_table.value)
  } else {
    csv_table.value.show_csv([current_table.value])
  }
}

const prompt_question = ref([])
const get_question = async () => {
  const table_name = current_table.value?.title ?? ''
  const res = await TableQAService.get_question({ table_name, number_question: 3 })

  chatBoxRef.value.modify_message(messages => {
    const agent_ms = messages.value.filter(x => (x.role === 'agent'))
    if (agent_ms.length > 0) {
      agent_ms[agent_ms.length - 1].news_summary = res?.output ?? []
    }
  })

  if (res?.output && current_table.value?.urls) {
    multi_table.value = current_table.value?.urls.filter(x => (res.output[0]?.table_names.indexOf(x.title) > 0))
    current_table.value.input = res.output[0].input
  }
}

const apply_question = async (q) => {
  const input = q?.input ?? q

  if (q?.table_names) {
    multi_table.value = current_table.value?.urls.filter(x => (q.table_names.indexOf(x.title) > 0))
  }

  if (answer_loading.value) {
    return
  }
  current_table.value.input = input
  await nextTick()
  chatBoxRef.value.submit_chat('TableQA')
}

onMounted(async () => {
  await get_menu_items()
  show_csv()
  get_question()
})


const show_history_view = ref(false)
const use_internet_checked = ref(false)
const answer_loading = ref(false)

const chat_with_table_qa_mode = async (data, { loading, input, output, messages, append_message, scroll }) => {
  let table_name = current_table.value?.title ?? ''
  if (multi_table.value && multi_table.value.length > 1) {
    table_name = multi_table.value.map(x => (x.title))
  }
  loading.value = true
  answer_loading.value = true
  const input_text = input.value
  input.value = ''
  const input_md = `**TABLE:** ${table_name}\n\n ${input_text}`
  append_message({ role: 'user', content: input_md })
  scroll()
  // append_message
  TableQAService.table_qa({ table_name, input: input_text }).then(data => {
    loading.value = false
    answer_loading.value = false

    get_question()
    append_message({ role: 'agent', content: data.answer, details: data })
    output.value = ''
    scroll()
  })
}
const chat_with_bi_mode = async (data, { loading, input, output, messages, append_message, scroll }) => {
  let table_name = current_table.value?.title ?? ''
  if (multi_table.value && multi_table.value.length > 1) {
    table_name = multi_table.value.map(x => (x.title))
  }
  loading.value = true
  answer_loading.value = true
  const input_text = input.value
  input.value = ''
  const input_md = `**TABLE:** ${table_name}\n\n ${input_text}`
  append_message({ role: 'user', content: input_md })
  scroll()
  TableQAService.bi({ table_name, input: input_text }).then(data => {
    loading.value = false
    answer_loading.value = false

    get_question()
    if (data.python_code) {
      data.code = Prism.highlight(data.python_code, Prism.languages.python, 'python');
    }
    append_message({ role: 'agent', content: data.answer, details: data })
    output.value = ''
    scroll()
  })

}
// const chat_table_qa = async (data, { loading, input, output, messages, append_message, scroll }) => {
const chat_table_qa = async (data, handler) => {
  if (data.mode === 'TableQA') {
    chat_with_table_qa_mode(data, handler)
  } else if (data.mode == 'BI') {
    chat_with_bi_mode(data, handler)
  }
}

const chatBoxRef = ref<InstanceType<typeof ChatBox> | null>(null)
const on_click_clear_context = () => {
  chatBoxRef.value?.clear_context()
}

const show_table_qa_detail = ref(false)
const table_qa_detail = ref()
const on_show_table_qa_detail = (m) => {
  show_table_qa_detail.value = true
  const { sql_query, sql_result, answer, sub_table } = m.details
  const CODE = '```'
  const sub_table_md = sub_table ? `- **SUB TABLE:**\n\n  ${sub_table}\n\n` : ''
  const content = `- **SQL:** \n${CODE}sql\n${sql_query}\n${CODE}\n - **RESULT:** ${sql_result}\n\n ${sub_table_md} ${answer}`
  table_qa_detail.value = { content, details: m.details }
}


const upload_table_data = ref({ name: '', url: '', file: '' })
const upload_flag = ref(false)
const uploading_flag = ref(false)
const upload_progress = ref(0)
const upload_table = async () => {
  console.log(upload_table_data.value)
  const { name, url, file } = upload_table_data.value
  await upload_req(`/llm/tableqa/upload?user=${user.value}&url=${url}&name=${name}`, file, (p) => {
    uploading_flag.value = (p != 100)
    upload_progress.value = p
    console.log(uploading_flag.value)
  })
  upload_flag.value = false
  get_menu_items()
}

const select_file = async () => {
  if (upload_table_data.value.file) {
    upload_table_data.value.file = ''
    return
  }
  const files = await get_local_file()
  upload_table_data.value.file = files[0]
  upload_table_data.value.url = ''
  upload_table_data.value.name = files[0].name
}

const add_table_data = () => {
  upload_flag.value = true
  upload_table_data.value = { name: '', url: '', file: '' }
}

const delete_item = async (id) => {
  await TableQAService.delete_menu_item(id)
  menu_items.value = menu_items.value.filter(x => (x.id !== id))
}

const hide_chat = ref(true)
const expand_table = (b) => {
  hide_chat.value = !hide_chat.value
}
</script>

<template>
  <Splitter style="width: 100%;" :gutterSize="1">
    <SplitterPanel :size="50">
      <CsvTable @toggle_expand_table="expand_table" ref="csv_table" />
    </SplitterPanel>
    <SplitterPanel v-if="hide_chat" :size="50">
      <ChatBox ref="chatBoxRef" :input="current_table?.input" @chat="chat_table_qa">
        <template #chat_message="{ message }">
          <div class="flex flex-column w-full">
            <div v-if="message?.details" class="flex w-full justify-content-center">
              <Button @click="on_show_table_qa_detail(message)" label="details" rounded icon="pi pi-eye"
                severity="secondary" />
            </div>
            <div v-if='message?.details?.fig_path'
              class="flex flex-column align-items-center">
              <img :src="message?.details?.fig_path" alt="">
              <!-- <div style="display:flex;overflow-y: auto; max-height: 300px;width:90%;">
                <pre style="white-space: pre-wrap;">
                  <code class="language-python" v-html="message?.details.code"></code>
                </pre>
              </div> -->
            </div>
            <MarkdownRenderer :source="message.content"></MarkdownRenderer>
            <div v-if="message.role === 'agent' && (message?.news_summary ?? []).length > 0"
              class="flex flex-column ml-5 mb-4">
              <div class="flex justify-content-between align-items-center">
                <p><b>Suggested Questions:</b></p>
                <Button @click="get_question()" icon="pi pi-refresh" text label="Refresh" />
              </div>
              <div class="flex flex-column gap-2">
                <div v-for="q in message?.news_summary ?? []">
                  <Tag @click="apply_question(q)" :class="{ prompt_item: true, disabled: answer_loading }"
                    style="font-weight: normal;" severity="secondary" :value="q?.input ?? q" rounded></Tag>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template #tools>
          <div style="display:flex;overflow-x: auto; padding:20px">
            <div class="flex flex-row align-items-center justify-content-start gap-2 pl-2">
              <Button icon="pi pi-refresh" aria-label="Submit" @click="on_click_clear_context" severity="secondary" />
              <span>Table:&ensp;</span>
              <Dropdown v-model="current_table" @change="show_csv" :options="menu_items" optionLabel="title"
                placeholder="Select Table" class="w-full md:w-15rem m-1">
                <template #option="{ option }">
                  <div class="flex justify-content-between align-items-center w-full">
                    <span>{{ option.title }}</span>
                    <Button v-if="option.id" @click.stop="delete_item(option.id)" icon="pi pi-minus-circle"
                      severity="contrast" text style="color:red" aria-label="Delete" />
                  </div>
                </template>
              </Dropdown>
              <MultiSelect v-if='current_table?.urls' v-model="multi_table" @change="show_csv"
                :options="current_table.urls" optionLabel="title" placeholder="Select Knowledge Base"
                class="w-full md:w-20rem"></MultiSelect>
              <Button @click="add_table_data" icon="pi pi-upload" text />
              <span>Prompt Augmentation:&nbsp;</span>
              <ToggleSwitch v-model="use_internet_checked" />
              <Button icon="pi pi-history" text rounded @click="show_history_view = true" />
            </div>
          </div>
        </template>
      </ChatBox>
      <Dialog v-model:visible="show_table_qa_detail" modal :draggable="false" :header="'Details'"
        :style="{ width: '70rem' }">
        <div class="flex flex-column">
          <div v-if='table_qa_detail?.details?.code' style="display:flex;overflow-y: auto; max-height: 300px;">
            <pre style="white-space: pre-wrap;">
              <code class="language-python" v-html="table_qa_detail?.details?.code"></code>
            </pre>
          </div>
          <MarkdownRenderer :source="table_qa_detail?.content"></MarkdownRenderer>
        </div>
      </Dialog>
      <Dialog v-model:visible="upload_flag" modal header="Add Table Data" :style="{ width: '25rem' }"
        :closeOnEscape="false">
        <div class="flex flex-column gap-2">
          <div class="flex align-items-center gap-4">
            <label class="font-semibold w-24">Name</label>
            <InputText :disabled="uploading_flag" v-model="upload_table_data.name" class="flex-auto"
              autocomplete="off" />
          </div>
          <div class="flex align-items-center">
            <label class="font-semibold w-24 mr-5">File&ensp;</label>
            <InputText :disabled="uploading_flag || upload_table_data.file !== ''" v-model="upload_table_data.url"
              class="flex-auto" autocomplete="off" placeholder="Upload local file or use url" />
            <!-- <div> -->
            <Button v-show="!uploading_flag" @click="select_file" text
              :icon="upload_table_data.file === '' ? 'pi pi-upload' : 'pi pi-minus-circle'"
              :style="{ color: upload_table_data.file === '' ? '' : 'red' }" />
            <ProgressSpinner v-show="uploading_flag" fill="transparent" style="width: 30px; height: 30px" />
            <!-- </div> -->
          </div>
          <ProgressBar v-show="uploading_flag" :value="upload_progress" :showValue="false" style="height: 6px;" />
          <div v-show="!uploading_flag" style="height: 6px;" />

          <div class="flex justify-end gap-2">
            <Button type="button" label="Cancel" :disabled="uploading_flag" severity="secondary"
              @click="upload_flag = false"></Button>
            <Button type="button" label="Save" :disabled="uploading_flag" @click="upload_table"></Button>
          </div>
        </div>
      </Dialog>
      <Drawer v-model:visible="show_history_view" header="History" position="right">
        <ChatHistory />
      </Drawer>
    </SplitterPanel>
  </Splitter>
</template>

<style scoped>
.disabled {
  cursor: none !important;
  background-color: #ccc !important;
}

.prompt_item:hover {
  cursor: pointer;
  background-color: var(--p-primary-200);
}

.his-item {
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.his-item:hover {
  background: rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.active {
  background: rgba(0, 0, 0, 0.1);
}

#chatBox {
  display: flex;
  height: 100%;
  flex-direction: column;
}

#chatContainer {
  position: relative;
  width: 100%;
  height: 70vh;
}

#chatArea {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  overflow-y: auto;
}

#inputArea {
  display: flex;
  height: 100px;
  width: 100%;
  padding: 10px;
  align-items: space-between;
}

#chatInput {
  width: calc(100% - 82px);
  height: 100%;
  padding: 10px;
  margin-right: 10px;
}
</style>
