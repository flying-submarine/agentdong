<script setup lang="ts">
// import { type Message, type ChatResponse } from "ollama";
// import { Ollama,type ChatRequest,type ChatResponse } from 'ollama'
// const ollama = new Ollama({ host: '11.163.70.215:11434' })
import { ChatClient } from '@/service/ChatClient'
import { askGraphStream, getDemoSessionId } from '@/service/askGraph'
const client = new ChatClient()
import { ref, toRefs } from "vue";
import ChatMessage from "./ChatMessage.vue";
import { useModelStore } from "@/stores/model";
import { onMounted, watch } from 'vue';
import { ChatSessionService } from "@/service/ChatSession";
import CryptoJS from 'crypto-js';
import { useUserStore } from "@/stores/user";
const { user } = toRefs(useUserStore())
const modelStore = useModelStore();
const { currentModel } = toRefs(modelStore);
const chatArea = ref<HTMLElement | null>(null);
const answerLoading = ref(false);
const chat_history = ref([])
import { scrollToBottom, upload_req, get_local_file } from '@/service/utils'


const upload_progress = ref()
upload_progress.value = { info: '', flag: false }
const uploadFile = async () => {
  const files = await get_local_file()
  const upload_progress_handler = (v) => {
    upload_progress.value.info = `uploading:${v.toFixed(2)}%`
    if (v == 100) {
      upload_progress.value.info = 'analyzing'
    }
  }
  const response = await upload_req(`/llm/docs?user=${user.value}`, files[0], upload_progress_handler)

  init_docs()
  console.log('File uploaded successfully');
  upload_progress.value.info = 'finish'
  upload_progress.value.flag = false

  const docId = response.data.data[0].docId
  const sel = {}
  sel[docId] = true
  selectedDocFile.value = sel
}

const CHAT_MODE_FREE_CHAT = 'free chat'
const CHAT_MODE_FILE_QA = 'file QA'
const chatMode = ref(CHAT_MODE_FREE_CHAT)
// 统一走线上 /api/agt/ask_graph（agentdong.com）；返回 { output } 流以复用现有渲染循环
const tryChat = async (
  model: string,
  inputMessage: string,
) => {
  if (!sessionId.value || sessionId.value === 'test') {
    sessionId.value = getDemoSessionId()
  }
  return askGraphStream(inputMessage)
};

let i = 0;
const submitChat = async (event: Event) => {
  if (
    event instanceof KeyboardEvent &&
    (event.altKey || event.shiftKey || event.ctrlKey)
  ) {
    return;
  }
  const content = messageContent.value;
  messageContent.value = "";
  // const inputMessage = { role: "user", content };
  const inputMessage = content.trim();

  if (!inputMessage) {
    return
  }

  answerLoading.value = true;
  messages.value.push({ role: "user", content });
  scrollToBottom(chatArea);

  const response = await tryChat(currentModel.value, inputMessage);
  answerLoading.value = false;
  if (!response) return;

  const appendMessage = () => {
    const content = currentOutputMessageContent.value.trim();
    if (content) {
      chat_history.value.push({
        user: inputMessage,
        bot: content
      })
      messages.value.push({
        role: "agent",
        content: content,
      });
      scrollToBottom(chatArea);
      refresh_sessions_handler()
    }
    currentOutputMessageContent.value = "";
  };

  for await (const part of response) {
    const forceScroll = !currentOutputMessageContent.value;
    currentOutputMessageContent.value += (part.output ? part.output : '');
    scrollToBottom(chatArea);
  }
  appendMessage();
  return response
};

const messageContent = ref("Who are you?");
const messages = ref([]);
const message_init = () => {
  messages.value = []
  messages.value.push({ role: "agent", content: "Hello，I am your  GPT Copilot. How can I help you?" })
}
message_init()
const currentOutputMessageContent = ref("");

const sessionId = ref('test')
const uploadFlag = ref(false);
const uploadPdf = async (file, userId) => {
  const formData = new FormData();
  formData.append('file', file);
  uploadFlag.value = true
  const response = await fetch(`/llm/docs?user=${userId}`, {
    method: 'POST',
    body: formData
  });

  if (response.ok) {
    uploadFlag.value = false

    // get_llm_docs(user.value).then((data) => { selectedOptions.value = data?.data.map(x => { return { key: x.docId, label: x.fileName } }) })
    init_docs()
    console.log('File uploaded successfully!');
  } else {
    uploadFlag.value = false
    console.error('Error in file upload:', response.statusText);
  }
  return response
};

const selectedDocFile = ref({})
const selectedOptions = ref(null)
const get_llm_docs = async (userId) => {

  // NodeService.getTreeNodes().then((data) => (nodes.value = data));
  return (await fetch(`/llm/docs?user=${userId}`, { headers: { 'Content-Type': 'application/json' } })).json();
}

const init_docs = () => {
  get_llm_docs(user.value).then((data) => {
    if (data.data) {
      selectedOptions.value = data.data.map(x => { return { key: x.docId, label: x.fileName } })
    } else {
      selectedOptions.value = []
    }
  })
}

// const get_session = async () => {
//   const res = await client.create_session()
//   return res
// }

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
  const str1 = appKey + truncate(messageContent.value) + salt + curtime + key;
  //const vocabId = '您的用户词表ID';
  const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
  let param = new URLSearchParams({
    q: messageContent.value.toString(),
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
    messageContent.value = data.translation[0]
  } catch (error) {
    console.error('Error:', error);
  }
}

const toArabic = async () => {
  if (messageContent.value) {
    const appKey = import.meta.env.VITE_APP_KEY;
    const key = import.meta.env.VITE_API_KEY; // 注意：保密
    const salt = (new Date).getTime();
    const curtime = Math.round(new Date().getTime() / 1000);
    //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
    const from = 'auto';
    const to = 'ar';
    const str1 = appKey + truncate(messageContent.value) + salt + curtime + key;
    //const vocabId = '您的用户词表ID';
    const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
    let param = new URLSearchParams({
      q: messageContent.value.toString(),
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
      messageContent.value = data.translation[0]
    } catch (error) {
      console.error('Error:', error);
    }
  }
}

let refresh_sessions_handler = () => { };
onMounted(() => {
  // client.fetchStream()
  // console.log(get_session())
  ChatSessionService.on_add_session((sid, fn) => {
    console.log(sid)
    chat_history.value = []
    message_init()
    sessionId.value = sid
    refresh_sessions_handler = fn
  })

  ChatSessionService.on_change_session((ss) => {
    chat_history.value = ss.chat
    messages.value = ss.message
    sessionId.value = ss.id
    scrollToBottom(chatArea)
  })
  init_docs()
});

watch(user, (v) => {
  console.log('user change:', v)
  init_docs()
})

watch(chatMode, (v) => {
  if (v === CHAT_MODE_FILE_QA) {
    init_docs()
    messageContent.value = "What is in the reference material?"
  } else {
    messageContent.value = ""
  }
})

const use_internet_checked = ref(false)

const on_click_clear_context = () => {
  chat_history.value = []
  if (messages.value.length > 0 && messages.value[messages.value.length - 1].role !== 'divider') {
    messages.value.push({
      role: 'divider'
    })
  }
}

</script>

<template>
  <div id="chatBox">
    <div id="chatContainer">
      <div id="chatArea" ref="chatArea">
        <div v-for="message in messages" :key="message.content">
          <ChatMessage :message="message" />
        </div>
        <div v-if="currentOutputMessageContent">
          <ChatMessage :message="{ role: 'agent', content: currentOutputMessageContent }" />
        </div>
        <div v-else-if="answerLoading">
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
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 5px 10px; height:60px">
      <!-- <InputText v-tooltip.top="'Enter your username'" type="text" placeholder="Top" /> -->
      <Button icon="pi pi-refresh" aria-label="Submit" @click="on_click_clear_context" severity="secondary" />
      <SelectButton v-model="chatMode" size="mini" :options="[CHAT_MODE_FREE_CHAT, CHAT_MODE_FILE_QA]"
        aria-labelledby="basic" />
      <TreeSelect v-if="chatMode === CHAT_MODE_FILE_QA" v-model="selectedDocFile" :options="selectedOptions"
        placeholder="Select Item" style="height: 36px;" />
      &nbsp;
      <Button :icon="upload_progress.flag ? 'pi pi-spin pi-spinner' : 'pi pi-upload'"
        v-if="chatMode === CHAT_MODE_FILE_QA" label="upload" :disabled="upload_progress.flag" severity="info"
        style="height: 36px;" @click="uploadFile" />
      &nbsp;
      <!-- <span v-if="upload_progress.info !== ''">{{ upload_progress.info }}</span> -->
      <span :style="{ color: upload_progress.error ? 'red' : '' }">{{ upload_progress.info }}</span>&nbsp;
      Internet&nbsp;
      <ToggleSwitch v-model="use_internet_checked" />
      <div style="display: flex; margin-left: auto;">
        <Button style="height: 36px;" @click="toEnglish" label="TO英语" />
        &nbsp;
        <Button style="height: 36px;" @click="toArabic" label="TO阿拉伯语" />
      </div>
    </div>
    <div id="inputArea">
      <Textarea v-model="messageContent" @keyup.enter="submitChat" id="chatInput" />
      <Button :disabled="answerLoading ? true : undefined" @click="submitChat" id="submitButton">Submit</Button>
    </div>
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
