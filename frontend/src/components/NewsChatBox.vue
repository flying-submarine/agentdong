<script setup lang="ts">

import { ref, toRefs, onMounted } from 'vue'
import { Message } from '@/service/ChatClient'
import ChatMessage from './ChatMessage.vue'
import MarkdownRendererNew from './MarkdownRendererNew.vue'
import { scrollToBottom, stream_req, json_chunk_handler } from '@/service/utils'
import { ChatSessionService } from '@/service/ChatSession'
import { useUserStore } from "@/stores/user";
import { Ref } from 'vue'
import { watch } from 'vue'
import { retrieveData, storeData } from '@/service/utils';

import SubmitImg from '@/assets/longReportSubmit.png';
import ClearContent from '@/assets/longReportClear.png';

import { serviceFetch } from '@/service/utils';
const { user } = toRefs(useUserStore())


export interface Props {
  input?: string,
}
const props = defineProps<Props>()
watch(props, () => {
  messageContent.value = props.input ?? ''
})

const phrasesList = ref([])

const generateStatus = ref(false);

const messages = ref<Message[]>([])

const controlFlag = ref(true);
const message_init = () => {
  messages.value = []
  messages.value.push({ role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?" })
}
const messageContent = ref('')

const answer_loading = ref(false)
const use_internet_checked = ref(true)

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

const news_chat = async () => {
  if (answer_loading.value || messageContent.value.length < 1) {
    return
  }
  if(generateStatus.value) return;
  const user_chat = messageContent.value
  messageContent.value = ''
  controlFlag.value = true;
  append_message({ role: 'user', content: user_chat })
  answer_loading.value = true
  scrollToBottom(chatArea)
  // /news/qagen
  // const response = await fetch(`/news/qagen`, {
  const response = await serviceFetch(`/gpt/news/retrieve_qagen`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: user_chat,
      user: user.value,
      history: chat_history.value.map(x => ([{ role: 'user', content: x.user }, { role: 'agent', content: x.bot }])).flat(),
      stream: true,
      increase: true,
      web_aug: use_internet_checked.value,
    })
  })
  answer_loading.value = false;
  generateStatus.value = true;
  if(!controlFlag.value) {
    messageContent.value = '';
    generateStatus.value = false;
    return;
  }

  if (!response.ok) {
    console.error('req /news/qagen')
    generateStatus.value = false;
    return
  }

try {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  const res1 = await (async function* () {
      while (true) {
          const { done, value } = await reader.read()
          if (done) break
          yield decoder.decode(value);
      }
  })();
  let questionList = [];
  let questions;
  let retrievals = [];
  let refrence = '';
  for await (let chunk of json_chunk_handler(res1)) {
    const status = chunk.status;
    console.log(chunk);
    if (status === 'generating') {
      generating_content.value += chunk.output ?? ''
      scrollToBottom(chatArea)
    } else if (status === 'stop') {
      if(!chunk?.questions?.error) {
        questions =  chunk?.questions||'';
      }
      if(chunk?.retrievals) {
        retrievals = chunk?.retrievals||[];
      }
      if(retrievals.length>0) {
        refrence = "<div style='padding: 15px'>" + retrievals.map(x => (`<div><a class="alink" style="color: #58A9FC;display:flex" href="${x.url}" title="${x.content}" target="_blank"><div><span style="font-size:20px;line-height: 18px;align-self: flex-start;">·&nbsp;</span>${x.title}</div></a></div>`)).join('\n') + "</div>"
      }
      if(questions) {
        try {
          questionList = Object.values(JSON.parse(questions));
        } catch (error) {
          questionList = Object.values(questions)||[];
          console.log(questions, 'error question');
        }
      }
      generating_content.value += chunk.output ?? ''
      append_message({ 
        role: 'agent', 
        content: storeData(generating_content.value, retrievals, questionList), //generating_content.value, 
        refrence 
      });
      console.log('渲染处理前回答数据：', generating_content.value);
      console.log('渲染处理前引文数据：', retrievals);
      questionList.forEach(item=>{
        messages.value.push({
          role: 'phrase',
          content: item
        });
      });
      // if (chat_history.value.length < 1) {
      //   refresh_sessions_handler()
      // }
      append_history(user_chat, generating_content.value)
      generating_content.value = '';
      generateStatus.value = false;
      scrollToBottom(chatArea);
      break;
    }
  }
} catch (error) {
  generateStatus.value = false;
  console.log(error);
}

}

const agentParseData = (item,type)=>{
  if(item.role !== "agent") return item
  return {
    ...item,
    content:retrieveData(item.content)[type]
  }
}

const sendMessage =  async (contentMessage)=>{
  if (answer_loading.value) {
    return
  }
  if(generateStatus.value) return;
  controlFlag.value = true;
  answer_loading.value = true;
  append_message({ role: 'user', content: contentMessage })
  scrollToBottom(chatArea);
  const response = await serviceFetch(`/gpt/news/retrieve_qagen`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: contentMessage,
      user: user.value,
      history: chat_history.value.map(x => ([{ role: 'user', content: x.user }, { role: 'agent', content: x.bot }])).flat(),
      stream: true,
      increase: true,
      web_aug: use_internet_checked.value,
    })
  });
  answer_loading.value = false;
  generateStatus.value = true;
  if(!controlFlag.value) {
    messageContent.value = '';
    generateStatus.value = false;
    return;
  }
  if (!response.ok) {
    console.error('req /news/qagen');
    generateStatus.value = false;
    return
  }
try {
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  const res1 = await (async function* () {
      while (true) {
          const { done, value } = await reader.read()
          if (done) break
          yield decoder.decode(value);
      }
  })();

  let questionList = [];
  let questions;
  let retrievals = [];
  let refrence = '';
  for await (let chunk of json_chunk_handler(res1)) {
    const status = chunk.status;
    console.log(chunk);
    if (status === 'generating') {
      generating_content.value += chunk.output ?? ''
      scrollToBottom(chatArea)
    } else if (status === 'stop') {
      if(!chunk?.questions?.error) {
        questions =  chunk?.questions||'';
      }
      if(chunk?.retrievals) {
        retrievals = chunk?.retrievals||[];
      }
      if(retrievals.length>0) {
        refrence = "<div style='padding: 15px'>" + retrievals.map(x => (`<div><a class="alink" style="color: #58A9FC;display:flex" href="${x.url}" title="${x.content}" target="_blank"><div><span style="font-size:20px;line-height: 18px;align-self: flex-start;">·&nbsp;</span>${x.title}</div></a></div>`)).join('\n') + "</div>"
      }
      if(questions) {
        try {
          questionList = Object.values(JSON.parse(questions));
        } catch (error) {
          questionList = Object.values(questions)||[];
          console.log(questions, 'error question');
        }
      }
      generating_content.value += chunk.output ?? ''
      append_message({
       role: 'agent',
       content: storeData(generating_content.value, retrievals, questionList), //generating_content.value, 
       refrence 
      });
      questionList.forEach(item=>{
        messages.value.push({
          role: 'phrase',
          content: item
        });
      });
      // if (chat_history.value.length < 1) {
      //   refresh_sessions_handler()
      // }
      append_history(contentMessage, generating_content.value)
      generating_content.value = ''
      scrollToBottom(chatArea);
      generateStatus.value = false;
      break;
    }
  }
} catch (error) {
  generateStatus.value = false;
  console.log(error);
}
  // const res = await response.json()
  // const content = res?.message?.content
  // const retrievals = res?.retrievals
  // const refs = {}
  // const refrence = "<ul style='padding: 15px'>" + retrievals.map(x => (`<li><a class="alink" style="color: #58A9FC;display:flex" href="${x[1]}" target="${x}"><span style="font-size:20px;line-height: 18px;align-self: flex-start;">·&nbsp;</span><div>${x[1]}</div></a></li>`)).join('\n') + "</ul>"
  // append_message({ role: 'agent', content, refrence });
  // scrollToBottom(chatArea);
  // append_history(contentMessage, content)
}

const chat = () => {
  const user_chat = messageContent.value
  // append_message('user', user_chat)
  // scrollToBottom(chatArea)
  const data = {
    input: user_chat,
    user: user.value,
    sessionId: sessionId.value,
    history: chat_history.value,
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
  controlFlag.value = false;
  answer_loading.value = false;
  chat_history.value = []
  if (messages.value.length > 0 && messages.value[messages.value.length - 1].role !== 'divider') {
    messages.value.push({
      role: 'divider'
    })
  }
}
import CryptoJS from 'crypto-js';
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


// const get_phrases = async () => {
//   return (await serviceFetch(`/gpt/commonPhrases/list`, { headers: { 
//     'Content-Type': 'application/json',
//   }})).json();
// }

// const init_phrases = ()=>{
//   get_phrases().then((data) => {
//     if (data.data) {
//       phrasesList.value = data.data;
//       (data.data||[]).forEach(item=>{
//         messages.value.push({
//           role: 'phrase',
//           content: item.phrases
//         })
//       })
//     }
//   })
// }

// init_phrases()

defineExpose({
  clear_context,
})

const submitMessage = (content)=>{
  sendMessage(content);
}

import FeedBack from "./FeedBack.vue";
</script>

<template>
  <div id="chatBox">
    <div id="chatContainer">
      <div id="chatAreaBox" ref="chatArea">
        <div v-for="(message, idx ) in messages" :key="message.content" style="width: 100%;">
          <ChatMessage :message="agentParseData(message, message.role)" :notNeedHeadImage="message.role==='phrase'" :isPhrase="message.role==='phrase'">
            <div class="flex flex-column">
              <MarkdownRendererNew :source="agentParseData(message, 'text').content" @enterMessage="submitMessage" :isPhrase="message.role==='phrase'"></MarkdownRendererNew>
              <!-- <div dir="auto" v-html="message.refrence"></div> -->
              <div style="padding: 15px" v-if="message.role =='agent'">
                <div v-for="ref in agentParseData(message,'refe').content">
                  <a class="alink" :href="ref.url" style="color: #58A9FC;" dir="auto" :title="ref.content" target="_blank">{{ ref.title }}</a>
                </div>
              </div>
              <div v-if="message.role==='agent' && idx!==0" style="padding: 0 15px">
                <FeedBack :copyContent="agentParseData(message,'text').content" />
              </div>
            </div>
          </ChatMessage>
        </div>
        <div v-if="generating_content">
          <ChatMessage :message="{ role: 'agent', content: generating_content }" />
        </div>
        <div v-else-if="answer_loading">
          <ChatMessage :message="{ role: 'agent', content: '' }">
            <div class="flex flex-column ml-4" style="padding: 8px 8px 0 0;">
              <Skeleton class="mb-2" ></Skeleton>
              <Skeleton width="10rem" class="mb-2"></Skeleton>
              <Skeleton width="5rem" class="mb-2"></Skeleton>
              <Skeleton width="2rem" class="mb-2"></Skeleton>
            </div>
          </ChatMessage>
        </div>
      </div>
    </div>
    <!-- <slot name="tools"></slot> -->
    <div class="flex flex-row align-items-center justify-content-start gap-2 pl-2">
      <!-- <Button icon="pi pi-refresh" aria-label="Submit" @click="clear_context" severity="secondary" /> -->
      <div style="padding:5px 0 0 10px;cursor: pointer" @click="clear_context">
        <img :src="ClearContent" style="width: 14px; height: 14px;margin-right:5px;">
        <span>Clear Context</span>
      </div>
      <!-- <span>Internet:&nbsp;</span>
      <ToggleSwitch v-model="use_internet_checked" /> -->
      <!-- <Button icon="pi pi-history" text rounded @click="show_history_view = true" /> -->
      &nbsp;
            <!-- <div style="display: flex; margin-left: auto;">
              <Button 
                  style="height: 36px;" @click="toEnglish" label="TO英语"/>
                  &nbsp;
              <Button 
                  style="height: 36px;" @click="toArabic" label="TO阿拉伯语"/>
          </div> -->
    </div>
    <div id="inputArea">
      <Textarea v-model="messageContent" @keyup.enter="news_chat" id="chatInput" dir="auto" />
      <Button :disabled="answer_loading ? true : undefined" @click="news_chat" id="submitButton"><img :src="SubmitImg"></Button>
    </div>
  </div>
</template>



<style scoped>

/* #chatAreaBox {
  position: absolute;
  top: 0;
  left: 17px;
  bottom: 11px;
  right: 25px;
  overflow-y: auto;
  .more {
    font-size: 12px;
    color: #578BF7;
    &:hover {
      background: transparent;
    }
  }
} */
#chatBox {
  display: flex;
  height: 100%;
  flex-direction: column;
  background: #fff;
  margin: 13px 16px;
  box-shadow: var(--app-shadow-sm);
  border-radius: 5px;
  height: calc(100% - 26px);
}

#chatContainer {
  position: relative;
  width: 100%;
  height: 100%;
}

#chatAreaBox {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  overflow-y: auto;
  &::v-deep .alink {
    word-break: break-word;
  }
  &::v-deep .alink:hover {
    background-color: transparent;
  }
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