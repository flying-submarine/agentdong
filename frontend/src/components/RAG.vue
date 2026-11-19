<script setup lang="ts">
import { ref, toRefs } from "vue";
import ChatMessage from "./ChatMessage.vue";
import MultiSelect from "primevue/multiselect";
// import Dropdown from "primevue/dropdown";
import Select from "primevue/select";
import { useToast } from "primevue/usetoast";
import Toast from "primevue/toast";
const toast = useToast();
import { onMounted, watch } from "vue";
import { useUserStore } from "@/stores/user";

import MarkdownRenderer from "./MarkdownRenderer.vue"
import CryptoJS from 'crypto-js';


const current_message = ref('')
// const events = ref([
//   { status: 'Ordered', date: '15/10/2020 10:30', icon: 'pi pi-shopping-cart', color: '#9C27B0', image: 'game-controller.jpg' },
//   { status: 'Processing', date: '15/10/2020 14:00', icon: 'pi pi-cog', color: '#673AB7' },
//   { status: 'Shipped', date: '15/10/2020 16:15', icon: 'pi pi-shopping-cart', color: '#FF9800' },
//   { status: 'Delivered', date: '16/10/2020 10:00', icon: 'pi pi-check', color: '#607D8B' }
// ]);

const messages = ref([
  { role: "agent", content: "Hello，I am your Wakeb Copilot. How can I help you?" },
  // { role: "user", content: "Help me summarize the latest news about science and technology please" },
  // { role: "agent", content: "Here's a roundup of recent news about science and technology:", news_summary: events },
])
const answer_loading = ref(false)
const user_content = ref('What is the minimum total cost of a real estate or land for construction, investment, and sale or leasing project allowed by the concerned license?')
const databases = ref([])
const news_selected = ref({})
const edit_database_visiable = ref(false)
const database_data = ref({ label: '', key: '' })

const on_change_database = () => {
  // console.log(Object.keys(news_selected.value)[0])
  console.log(news_selected.value)
}

const on_click_clear_context = () => {
  // chat_history.value = []
  if (messages.value.length > 0 && messages.value[messages.value.length - 1].role !== 'divider') {
    messages.value.push({
      role: 'divider',
      content: '',
    })
  }
}

const selected_knowledge_base = ref({ name: '' })
const on_click_edit_database = (item) => {
  edit_database_visiable.value = true
  selected_knowledge_base.value = item
  knowledge_docs.value = []
  get_docs(item.baseId)

}

const { user } = toRefs(useUserStore())
const get_knowledge_bases = async () => {
  // const userId = user.value
  const userId = ''
  const response = await fetch(`/psllm/retrieval/knowledge-bases?userId=${userId}`)
  const body = await response.json()
  const data = body.data
  if (data) {
    databases.value = data.filter(x => { return x.name && x.name.indexOf('Saudi') != -1; })
  }
  return data
}

const knowledge_docs = ref([])
const add_knowledge_doc_flag = ref(false)
const get_docs = async (baseId) => {
  const response = await fetch(`/psllm/retrieval/docs?baseId=${baseId}`)
  const body = await response.json()
  const data = body.data
  if (data) {
    knowledge_docs.value = data
  }
  return data
}

watch(user, (v) => {
  console.log('user change:', v)
  get_knowledge_bases()
})

onMounted(() => {
  get_knowledge_bases()
})

const selected_knowledge_bases = ref();
const knowledge_change = () => {
  // console.log(selected_knowledge_bases.value)
}

const knowledge_doc_file_type_options = ref([
  { name: 'law' },
  { name: 'article' },
  { name: 'qa' },
  { name: 'learning' },
  { name: 'mindmap' },
  { name: 'knowledgetree' },
  { name: 'personal' },
])
const add_knowledge_doc_data = ref({ data: { baseId: '', fileType: '', fileAddr: '', fileName: '' } })
const add_knowledge_doc = async () => {
  const data = { ...add_knowledge_doc_data.value.data }
  data.fileType = data.fileType.name
  data.baseId = selected_knowledge_base.value.baseId
  data.fileType = undefined
  console.log(data)
  const response = await fetch(`/psllm/retrieval/docs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  })
  const res = await response.json()
  if (res.code != 200) {
    toast.add({ severity: 'error', summary: 'Error Code ' + res.code, detail: res.message, life: 3000 });
    return
  }
  add_knowledge_doc_flag.value = false
  toast.add({ severity: 'success', summary: 'success', detail: '', life: 3000 });
  get_docs(data.baseId)
  return res
}
const truncate = (q) => {
  var len = q.length;
  if (len <= 20) return q;
  return q.substring(0, 10) + len + q.substring(len - 10, len);
}
const toEnglish = async () => {

  //console.log(str);
  const appKey = import.meta.env.VITE_APP_KEY;
  const key = import.meta.env.VITE_API_KEY; // 注意：保密
  const salt = (new Date).getTime();
  const curtime = Math.round(new Date().getTime() / 1000);
  //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
  const from = 'auto';
  const to = 'en';
  const str1 = appKey + truncate(user_content.value) + salt + curtime + key;
  //const vocabId = '您的用户词表ID';
  const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
  let param = new URLSearchParams({
    q: user_content.value.toString(),
    appKey: appKey,
    salt: salt.toString(),
    from: from,
    to: to,
    sign: sign,
    signType: "v3",
    curtime: curtime.toString()
  }).toString();
  try {
    const response = await fetch('/translate/api', {
      method: 'POST', // 或者 'post'
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: param
    });
    if (!response.ok) {
      const errorText = await response.text(); // 尝试读取响应文本
      throw new Error(
        `Network response was not ok. Status: ${response.status} ${response.statusText}. Body: ${errorText}`
      );
    }
    const data = await response.json();
    console.log(data);
    user_content.value = data.translation[0]
  } catch (error) {
    console.error('Error:', error);
  }
}

const toArabic = async () => {
  if (user_content.value) {
    const appKey = import.meta.env.VITE_APP_KEY;
    const key = import.meta.env.VITE_API_KEY; // 注意：保密
    const salt = (new Date).getTime();
    const curtime = Math.round(new Date().getTime() / 1000);
    //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
    const from = 'auto';
    const to = 'ar';
    const str1 = appKey + truncate(user_content.value) + salt + curtime + key;
    //const vocabId = '您的用户词表ID';
    const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
    let param = new URLSearchParams({
      q: user_content.value.toString(),
      appKey: appKey,
      salt: salt.toString(),
      from: from,
      to: to,
      sign: sign,
      signType: "v3",
      curtime: curtime.toString()
    }).toString();
    try {
      const response = await fetch('/translate/api', {
        method: 'POST', // 或者 'post'
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: param
      });
      if (!response.ok) {
        const errorText = await response.text(); // 尝试读取响应文本
        throw new Error(
          `Network response was not ok. Status: ${response.status} ${response.statusText}. Body: ${errorText}`
        );
      }
      const data = await response.json();
      console.log(data);
      user_content.value = data.translation[0]
    } catch (error) {
      console.error('Error:', error);
    }
  }
}

const delete_knowledge_base_doc = async (item) => {
  // toast.add({ summary: 'test', detail: 'test', life: 1000 })
  const response = await (await fetch(`/psllm/retrieval/docs/${item.fileId}`, { method: 'DELETE' })).json()
  console.log(response)
  if (response.code != 200) {
    // add_knowledge_doc_data.value.error = "Error Code " + response.code
    toast.add({ severity: 'error', summary: 'Error Code ' + response.code, detail: response.message, life: 3000 });
    return
  }
  toast.add({ severity: 'success', summary: 'success', detail: '', life: 3000 });
  get_docs(selected_knowledge_base.value.baseId)
  return response
}



const submitChat = async () => {
  if (selected_knowledge_bases.value == undefined || user_content.value === '' || user_content.value.length == 0) {
    return
  }
  const knowledgeBases = selected_knowledge_bases.value.map(x => { return x.baseId })
  const input = user_content.value
  user_content.value = ''
  messages.value.push({ role: "user", content: input });

  current_message.value = ''
  answer_loading.value = true
  const use_stream = false
  const response = await fetch(`/psllm/retrieval/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      "userId": user.value,
      "sceneIds": [],
      "subSceneIds": [],
      "knowledgeBases": knowledgeBases,
      "input": input,
      "history": [],
      "stream": use_stream,
      "promptAug": use_prompt_augmentation.value,
    })
  })
  // console.log(response)
  if (response.status != 200) {
    // error
  }
  answer_loading.value = false
  if (!use_stream) {
    const res = await response.json()
    if (res.code == 200) {
      const row = res.data.choices[0]
      current_message.value = row.message.content
      messages.value.push({
        role: "agent",
        content: current_message.value,
        refrence: row.retrievals,
      });
      current_message.value = ''
    }
    return
  }

  const reader = response.body.getReader();

  const decoder = new TextDecoder();
  // const contentDiv = document.getElementById('content');

  const readChunk = () => {
    reader.read().then(({ done, value }) => {
      if (done) {
        console.log("Stream complete");
        messages.value.push({
          role: "agent",
          content: current_message.value,
          refrence: [],
        });
        current_message.value = ''
        return;
      }

      const chunk = decoder.decode(value, { stream: true });
      // contentDiv.innerHTML += chunk.replace(/\n/g, '<br>');  // 将新内容添加到页面
      console.log('read stream message:', chunk)
      current_message.value += chunk
      readChunk();
    }).catch(error => {
      console.error("Error reading stream:", error);
    });
  }
  readChunk();
  return response
}

const use_prompt_augmentation = ref(false)
</script>

<template>
  <div id="chatBox">
    <div id="chatContainer">
      <!-- <Toast ref="toast" /> -->
      <div id="chatArea" ref="chatArea">
        <div v-for="message in messages" :key="message.content">
          <ChatMessage :message="message">
            <MarkdownRenderer :source="message.content"></MarkdownRenderer>
            <div style="margin-left: 2rem;">
              <div v-for="ref in message.refrence">
                <a :href="ref.fileAddr" :target="ref.fileAddr">{{ ref.title }}</a>
                <p :title="ref.content" style='width: 70%; overflow: hidden; white-space:nowrap; text-overflow: ellipsis'>
                  {{ ref.content }}</p>
              </div>
            </div>
          </ChatMessage>
        </div>
        <div v-if="current_message">
          <ChatMessage :message="{ role: 'agent', content: current_message }" />
        </div>
        <div v-else-if="answer_loading">
          <ChatMessage :message="{ role: 'agent', content: '' }">
            <div class="flex flex-column ml-4">
              <Skeleton class="mb-2"></Skeleton>
              <Skeleton width="10rem" class="mb-2"></Skeleton>
              <Skeleton width="5rem" class="mb-2"></Skeleton>
              <Skeleton width="2rem" class="mb-2"></Skeleton>
            </div>
          </ChatMessage>
        </div>
      </div>
    </div>
    <div class="card flex justify-content-start align-items-center" style="padding:5px 10px">

      <Button icon="pi pi-refresh" aria-label="Submit" @click="on_click_clear_context" severity="secondary" />
      <span style="line-height: 43px;font-weight: 500;">Database:&ensp;</span>
      <!-- <TreeSelect v-model="news_selected" selectionMode="multiple" @change="on_change_database" :options="databases"
        placeholder="Select News">
        <template #value="slotProps">
        </template>
      </TreeSelect> -->
      <MultiSelect v-model="selected_knowledge_bases" @change="knowledge_change" :options="databases" optionLabel="name"
        placeholder="Select Knowledge Base" class="w-full md:w-20rem">
        <template #option="slotProps">
          <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
            <span>{{ slotProps.option.name }}</span>
            <Button icon="pi pi-pencil" @click.stop="on_click_edit_database(slotProps.option)" severity="secondary" />
          </div>
        </template>
      </MultiSelect>
      <span>&nbsp;Prompt Augmentation&nbsp;</span>
      <ToggleSwitch v-model="use_prompt_augmentation" />
      <!-- <Button icon="pi pi-pencil" @click="on_click_edit_database" severity="secondary" /> -->
      <div style="display: flex; margin-left: auto;">
        <Button style="height: 36px;" @click="toEnglish" label="TO英语" />
        &nbsp;
        <Button style="height: 36px;" @click="toArabic" label="TO阿拉伯语" />
      </div>
    </div>
    <div id="inputArea">
      <Textarea v-model="user_content" @keyup.enter="submitChat" id="chatInput" />
      <Button :disabled="answer_loading ? true : undefined" @click="submitChat" id="submitButton">Submit</Button>
    </div>
    <Dialog v-model:visible="edit_database_visiable" modal :draggable="false" :header="selected_knowledge_base.name"
      position="topright" :style="{ width: '30rem' }">
      <template #header="">
        <div class="flex align-items-center">
          <span class="font-bold">{{ selected_knowledge_base.name }}</span>
          <Button @click="add_knowledge_doc_flag = !add_knowledge_doc_flag" v-show="!add_knowledge_doc_flag"
            icon="pi pi-plus" severity="secondary" />
        </div>
      </template>
      <div class="flex flex-column p-10" v-if="add_knowledge_doc_flag">
        <InputText v-model="add_knowledge_doc_data.data.fileAddr" class="w-full md:w-20rem m-1" placeholder="File Address"
          autocomplete="off" />
        <InputText v-model="add_knowledge_doc_data.data.fileName" class="w-full md:w-20rem m-1" placeholder="File Name"
          autocomplete="off" />
        <Select v-model="add_knowledge_doc_data.data.fileType" :options="knowledge_doc_file_type_options"
          optionLabel="name" placeholder="Select File Type" class="w-full md:w-20rem m-1" />
        <!-- <MultiSelect v-model="add_knowledge_doc_data.fileType" :options="knowledge_doc_file_type_options"
          optionLabel="name" placeholder="Select File Type" :selectionLimit="1" class="w-full md:w-20rem m-1" /> -->
        <div class="flex justify-content-end p-2">
          <Button class="mr-2" severity="secondary" @click="add_knowledge_doc_flag = false">Cancel</Button>
          <Button severity="secondary" @click="add_knowledge_doc">Add</Button>
        </div>
      </div>
      <div class="flex flex-column" v-for="item in knowledge_docs" v-if="!add_knowledge_doc_flag">
        <div class="flex flex-wrap p-2 align-items-center gap-3">
          <!-- <img class="w-4rem flex-shrink-0 border-round"
            :src="'https://primefaces.org/cdn/primevue/images/product/'"
            :alt="'img'" /> -->
          <div class="flex-1 flex flex-column gap-2">
            <span>{{ item.fileName }}</span>
            <div class="flex align-items-center gap-2">
              <!-- <i class="pi pi-tag text-sm"></i> -->
              <!-- <span>{{ item.updatedAt }}</span> -->
            </div>
          </div>
          <Button icon="pi pi-trash" aria-label="Submit" @click="delete_knowledge_base_doc(item)" severity="danger" />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
#chatBox {
  display: flex;
  height: 100%;
  flex-direction: column;
}

.item_padding {
  padding: 5px;
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
