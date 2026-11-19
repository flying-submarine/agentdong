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
import { askGraph, formatAskGraphAnswer } from '@/service/askGraph';
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

// 统一发送：走线上 /api/agt/ask_graph（替代已失效的 /gpt/news/retrieve_qagen 流）
const callAskGraph = async (question: string) => {
  if (answer_loading.value || generateStatus.value) return
  if (!question || !question.trim()) return
  const user_chat = question.trim()
  append_message({ role: 'user', content: user_chat })
  answer_loading.value = true
  scrollToBottom(chatArea)

  const res = await askGraph(user_chat)
  answer_loading.value = false
  generateStatus.value = true

  const text = res ? formatAskGraphAnswer(res) : '连不上服务，请稍后再试'
  const retrievals = res?.sources?.length
    ? res.sources.map(sid => ({ title: sid, url: '#', content: '知识库来源块 ' + sid }))
    : []
  append_message({
    role: 'agent',
    content: storeData(text, retrievals, []),
    refrence: '',
  })
  append_history(user_chat, text)
  generating_content.value = ''
  generateStatus.value = false
  scrollToBottom(chatArea)
}

const news_chat = async () => {
  const q = messageContent.value
  messageContent.value = ''
  await callAskGraph(q)
}

const agentParseData = (item,type)=>{
  if(item.role !== "agent") return item
  return {
    ...item,
    content:retrieveData(item.content)[type]
  }
}

const sendMessage = async (contentMessage: string) => {
  await callAskGraph(contentMessage)
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
  await callAskGraph(messageContent.value)
  messageContent.value = ''
}

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
    <div class="chat-toolbar">
      <button class="clear-btn" type="button" @click="clear_context">
        <i class="pi pi-refresh"></i><span>清空上下文</span>
      </button>
    </div>
    <div id="inputArea">
      <div class="input-wrap">
        <Textarea v-model="messageContent" @keyup.enter="news_chat" id="chatInput" dir="auto"
          placeholder="输入你的问题，Enter 发送…" />
      </div>
      <Button :disabled="answer_loading ? true : undefined" @click="news_chat" id="submitButton"
        icon="pi pi-send" aria-label="发送" />
    </div>
  </div>
</template>



<style scoped>
#chatBox {
  display: flex;
  flex-direction: column;
  height: calc(100% - 24px);
  min-height: 0;
  margin: 12px 14px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  box-shadow: var(--app-shadow-sm);
  overflow: hidden;
}
#chatContainer {
  position: relative;
  flex: 1;
  min-height: 0;
}
#chatAreaBox {
  position: absolute;
  inset: 0;
  overflow-y: auto;
  padding: 14px 10px 18px;
}
#chatAreaBox ::v-deep(.alink) { word-break: break-word; }
#chatAreaBox ::v-deep(.alink:hover) { background: transparent; }

.chat-toolbar {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  border-top: 1px solid var(--app-border);
}
.clear-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  color: var(--app-text-2);
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  transition: background 0.15s, color 0.15s;
}
.clear-btn:hover { background: var(--app-surface-3); color: var(--app-primary); }
.clear-btn i { font-size: 12px; }

#inputArea {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 10px 14px 14px;
}
.input-wrap { position: relative; flex: 1; min-width: 0; }
#chatInput {
  width: 100%;
  min-height: 72px;
  max-height: 160px;
  resize: vertical;
  padding: 11px 13px;
  border: 1px solid var(--app-border-strong);
  border-radius: var(--app-radius-sm);
  background: var(--app-surface);
  color: var(--app-text);
  font-size: 14px;
  line-height: 1.6;
}
#chatInput:focus { border-color: var(--app-primary); box-shadow: 0 0 0 3px var(--app-primary-ring); }
#chatInput::placeholder { color: var(--app-text-3); }
#submitButton.p-button {
  height: 42px;
  min-width: 42px;
  width: 42px;
  flex: 0 0 42px;
  border-radius: var(--app-radius-sm);
}
</style>