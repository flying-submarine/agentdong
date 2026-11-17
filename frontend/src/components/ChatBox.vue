<script setup lang="ts">

import { ref, toRefs, onMounted } from 'vue'
import { Message } from '@/service/ChatClient'
import ChatMessage from './ChatMessage.vue'
import { scrollToBottom, stream_req, json_chunk_handler } from '@/service/utils'
import { ChatSessionService } from '@/service/ChatSession'
import { useUserStore } from "@/stores/user";
import { Ref } from 'vue'
import { watch } from 'vue'
import { nextTick } from 'vue'
import CryptoJS from 'crypto-js';
const { user } = toRefs(useUserStore())


export interface Props {
  input?: string,
}
const props = defineProps<Props>()
watch(props, () => {
  messageContent.value = props.input ?? ''
})

const messages = ref<Message[]>([])

const message_init = () => {
  messages.value = []
  messages.value.push({ role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?" })
}
const messageContent = ref('who is the best palyer in this event')

const answer_loading = ref(false)

const append_message = (data: any) => {
  messages.value.push(data)
}

const append_history = (user, bot) => {
  chat_history.value.push({ user, bot })
}

const sessionId = ref('')
const chat_history = ref([])
let refresh_sessions_handler = () => { };
const init_session = () => {
  message_init()
  ChatSessionService.on_add_session((sid, fn) => {
    console.log('create new session:', sid)
    chat_history.value = []
    message_init()
    sessionId.value = sid
    refresh_sessions_handler = fn // 用于组件间传播事件，添加新的会话用户发送消息后，用来刷新会话组件的列表
  })

  ChatSessionService.on_change_session((ss) => {
    console.log('change to session:', ss)
    chat_history.value = ss.chat
    messages.value = ss.message
    sessionId.value = ss.id
    scrollToBottom(chatArea)
  })
}

onMounted(() => {
  init_session()
})


const emit = defineEmits<{
  (e: "chat", data: any, chat_handler: any): void;
}>()

const submit_chat = (mode = 'TableQA') => {
  const user_chat = messageContent.value
  // append_message('user', user_chat)
  // scrollToBottom(chatArea)
  const data = {
    input: user_chat,
    user: user.value,
    sessionId: sessionId.value,
    history: chat_history.value,
    mode,
  }

  const chat_handler = {
    loading: answer_loading,
    input: messageContent,
    output: generating_content,
    append_message,
    scroll() {
      scrollToBottom(chatArea)
    },
  }
  emit('chat', data, chat_handler)
}

const chatArea = ref<HTMLElement | null>(null);
const generating_content = ref('')
const submitChat = async () => {
  const user_chat = messageContent.value
  messageContent.value = ''

  append_message({ role: 'user', content: user_chat })
  scrollToBottom(chatArea)
  answer_loading.value = true
  const data = {
    input: user_chat,
    user: user.value,
    stream: true,
    increase: true,
    sessionId: sessionId.value,
    history: chat_history.value,
  }

  const response = await stream_req({ url: '/llm/chat', data })
  answer_loading.value = false
  generating_content.value = ''
  for await (let chunk of json_chunk_handler(response)) {
    const status = chunk.status
    if (status === 'generating') {
      generating_content.value += chunk.output ?? ''
      scrollToBottom(chatArea)
    } else if (status === 'stop') {
      append_message({ role: 'agent', content: generating_content.value })
      if (chat_history.value.length < 1) {
        refresh_sessions_handler()
      }
      append_history(user_chat, generating_content.value)
      generating_content.value = ''
      break
    }
  }
}

const clear_context = () => {
  chat_history.value = []
  if (messages.value.length > 0 && messages.value[messages.value.length - 1].role !== 'divider') {
    messages.value.push({
      role: 'divider'
    })
  }
}

const modify_message = (func: any) => {
  func(messages)
}
const truncate=(q)=>{
  var len = q.length;
        if (len <= 20) return q;
        return q.substring(0, 10) + len + q.substring(len - 10, len);
}

const  toEnglish=async ()=>{
        
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

const toArabic=async ()=>{
  if(messageContent.value){
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
defineExpose({
  clear_context,
  submit_chat,
  modify_message,
})
</script>


<template>
  <div id="chatBox">
    <div id="chatContainer">
      <div id="chatArea" ref="chatArea">
        <div v-for="message in messages" :key="message.content" style="width: 100%;">

          <ChatMessage v-if="$slots.chat_message" :message="message">
            <slot name="chat_message" :message="message"></slot>
          </ChatMessage>
          <ChatMessage v-else :message="message" />
        </div>
        <div v-if="generating_content">
          <ChatMessage :message="{ role: 'agent', content: generating_content }" />
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
    <slot name="tools"></slot>
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 5px 10px; height:60px;">
          <div style="display: flex; margin-left: auto;">
            <Button 
                style="height: 36px;" @click="toEnglish" label="TO英语"/>
                &nbsp;
            <Button 
                style="height: 36px;" @click="toArabic" label="TO阿拉伯语"/>
        </div>
      </div>
    <div id="inputArea">
      <Textarea v-model="messageContent" @keyup.enter="submit_chat('TableQA')" id="chatInput" />
      <div class="flex flex-column gap-2">
        <Button :disabled="answer_loading ? true : undefined" @click="submit_chat('TableQA')">TableQA</Button>
        <Button :disabled="answer_loading ? true : undefined" @click="submit_chat('BI')">BI</Button>
      </div>
    </div>
  </div>
</template>



<style scoped>
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