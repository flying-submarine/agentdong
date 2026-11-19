<script setup lang="ts">
import { serviceFetch } from '@/service/utils';
import { globalState } from '@/globalState';  
import { ref, toRefs,onMounted,watch} from "vue";
import Checkbox from 'primevue/checkbox';
import ChatMessage from "./ChatMessage.vue";
import MarkdownRenderer from './MarkdownRenderer.vue'
import { useModelStore } from "@/stores/model";
import { RagSessionService } from "@/service/RagChatSession";
import { message } from 'ant-design-vue';
import { useGeneratStore } from "@/stores/generat";
import { scrollToBottom,storeData,retrieveData} from '@/service/utils'
import PopoverConfirm from '@/components/PopoverConfirm.vue'
import { v4 as uuidv4 } from 'uuid'
import FeedBack from "./NewFeedback.vue";

const modelStore = useModelStore();
const generating = useGeneratStore();
const { currentModel } = toRefs(modelStore);
const chatArea = ref<HTMLElement | null>(null);
const answerLoading = ref(false);
const chat_history = ref([])
const phraseContent=ref('')
const knowBase=ref(true)
const visibleDialog = ref(false);
const phrasesList = ref([])
const referList = ref([])
const feedbackList = ref([])
const questionsList  = ref([])
const currentOutputMessageContent = ref("");
const confirm = ref<InstanceType<typeof PopoverConfirm> | null>(null)
const messages = ref([
  { role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?",flag:"writing" },
])

const buildFbId = ref("")
const messageContent = ref("");

const sessionId = ref('')

let refresh_sessions_handler = ()=>{};
globalState.initRagChat = ()=>{
  messages.value = []
  messages.value.push({ role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?",flag:"writing" })
}

const tryChat = async (
  model,
  inputMessage,
) => {
  buildFbId.value = uuidv4()
  // 演示站没有登录/历史：sessionId 为空就现场生成一个，每个访客一个会话（session），
  // 记忆（MemorySaver）和限流（每分钟 10 次）都是按它分的；千万别写成固定值
  if (!sessionId.value) sessionId.value = uuidv4()
  try {
    // 普通 fetch 调咱们的 /ask_graph，一次 POST 返回整段 JSON（非流式）；
    // 不用 RagSessionService.chat() 的 \0 流解析器（那个函数先留着，别的页面可能还在用）
    const res = await fetch('/api/agt/ask_graph', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: inputMessage, session_id: sessionId.value })
    })
    if (!res.ok) return null
    return await res.json()
  } catch (error) {
    console.error('ask_graph failed:', error)
    return null
  }
};


const processArray = (inputArray)=>{
  // 如果数组为空，直接返回空数组
  if (!Array.isArray(inputArray) || inputArray.length === 0) {
      return [];
  }

  return inputArray.map(item => {
      // 检查每一项的格式是否正确
      if (item && typeof item.user === 'string' && typeof item.bot === 'string') {
          return [
              { role: "user", content: item.user },
              { role: "assistant", content: item.bot,feedbackId:item.feedbackId }
          ];
      } else {
          // 如果格式不正确，可以抛出错误或跳过此项
          console.error('Invalid item format:', item);
          return null; // 或者 return []; 如果希望跳过此项
      }
  }).filter(item => item !== null).flat();
}
// 处理点击事件
const clickItem = (v) => {
  // clickedItem.value = index
  messageContent.value =  v
  visibleDialog.value = false 
}
const submitChat = async () => {
  if(generating.status) return 
  if(!sessionId.value && !chat_history.value.length && globalState.submitSession)   globalState.submitSession()
  if(!messageContent.value.trim()) return 
  if(messageContent.value.length > maxTokens) return message.warn('Limitation-Maximum input is 1200')
  generating.setStatus(true)
  const content = messageContent.value
 // messages.value.splice(1,2)
  answerLoading.value = true;
  // const content = messageContent.value!=''&&messageContent.value!=null?messageContent.value:initContent.value;
  messageContent.value = "";
  initContent.value = "";
  // const inputMessage = { role: "user", content };
  const inputMessage = content.trim();
  messages.value.push({ role: "user", content:content ,flag:"writing"});
  scrollToBottom(chatArea);
  const response = await tryChat(currentModel.value, inputMessage);
  answerLoading.value = false;
  if (!response) {
    // 请求失败：告诉用户一声，并把 Submit 按钮放开（不然 generating 一直卡住，按钮就点不了了）
    append_message({ role: 'agent', content: storeData('请求失败，后端没响应，稍后再试。', [], []), feedbackId: buildFbId.value })
    generating.setStatus(false)
    return;
  }
  // waiting_confirm：图（graph）冻在删文档的确认关卡，演示站不处理删库操作
  if (response.status === 'waiting_confirm') {
    const text = '这个请求要删文档，演示站不处理删库操作。'
    append_message({ role: 'agent', content: storeData(text, [], []), feedbackId: buildFbId.value })
    if (chat_history.value.length < 1) refresh_sessions_handler()
    append_history(inputMessage, storeData(text, [], []), buildFbId.value)
    generating.setStatus(false)
    return
  }
  // 正常回答：refused=true 显示（已拒答）；来源和置信度直接拼进正文
  let text = response.answer || ''
  if (response.refused) {
    text = '（已拒答）' + text
  } else if (response.sources && response.sources.length) {
    text += '\n\n来源：' + response.sources.join('、') + '（置信度 ' + response.confidence + '）'
  }
  append_message({ role: 'agent', content: storeData(text, [], []), feedbackId: buildFbId.value })
  if (chat_history.value.length < 1) refresh_sessions_handler()
  append_history(inputMessage, storeData(text, [], []), buildFbId.value)
  generating.setStatus(false)
};

const append_message = (data) => {
  messages.value.push(data)
}

const append_history = (user, bot,feedbackId) => {
  chat_history.value.push({ user, bot,feedbackId})
}
const commonPhrases = ()=>{
  visibleDialog.value = true
}

const get_phrases = async () => {
  return (await serviceFetch(`/gpt/commonPhrases/list`, { headers: { 
    'Content-Type': 'application/json',
  }})).json();
}
const initContent = ref('')

const init_phrases = ()=>{
  get_phrases().then((data) => {
    if (data.data) {
      phrasesList.value = data.data
    }
  })
}

const message_init = () => {
  messages.value = []
  messages.value.push({ role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?",flag:"writing" })
}

onMounted(() => {
  RagSessionService.on_add_session((sid, fn) => {
    chat_history.value = []
    message_init()
    sessionId.value = sid
    refresh_sessions_handler = fn
  })

  RagSessionService.on_change_session((ss) => {
    RagSessionService.getFbackList(ss.id).then(data=>{
      feedbackList.value = data
      // console.log(data,'getFbackList')
      chat_history.value = ss.chat // 参数
      let newData = []
      if(Array.isArray(ss.message) && ss.message.length){
        ss.message.forEach(item => {
          newData.push(item);  // 先将当前项添加到新数组中
          if (item.role === 'agent') {
              try {
                  // 解析 content 中的 JSON 字符串
                  const parsedContent = retrieveData(item.content)['ques']
                  if (parsedContent && Array.isArray(parsedContent)) {
                      // 遍历 ques 数组，将每个问题作为一个新的对象插入到当前项之后
                      parsedContent.forEach(ques => {
                          newData.push({
                              role: 'phrase',
                              content: ques
                          });
                      });
                  }
              } catch (error) {
                  console.error('Failed to parse content:', error);
              }
          }
        });
      }else{
        newData = ss.message
      }
      messages.value = newData // 对话
      sessionId.value = ss.id
      scrollToBottom(chatArea)
      globalState.closeConfirm()
    }) 
  })
  init_phrases()
});


const maxTokens = 1200;


const removeItem = async(id)=>{
  const response = await serviceFetch(`/gpt/commonPhrases?id=${id}`, { 
      method:"DELETE",
      headers: { 
        'Content-Type': 'application/json',
      }
  });
  if (response.ok) {
    init_phrases()
  } 
}

const addPhrases=async()=>{
  if(phrasesList.value.length > 9 ) return message.warn('Maximum phrases: 10');
  if(phraseContent.value.trim()) {
    const response = await serviceFetch(`/gpt/commonPhrases`, {
      method: 'POST',
      body:JSON.stringify({
        phrases: phraseContent.value
      }),
      headers: { 
        'Content-Type': 'application/json',
      }
    });

    if (response.ok) {
      phraseContent.value = ""
      init_phrases()
    } 
  }
}

const on_delete_session = (event, sid) => {
  confirm.value.show({
    label: 'Do you want to delete this record?',
    accept: () => removeItem(sid),
    event,
  })
}

const submitMessage = (content)=>{
  if(generating.status) return 
  messageContent.value = content
  scrollToBottom(chatArea);
  submitChat()
}

const agentParseData = (item,type)=>{
  if(item.role !== "agent") return item
  return {
    ...item,
    content:retrieveData(item.content)[type]
  }
}


const getFdInfo = (fbId)=>{
  let infoObj = {}
  if(Array.isArray(feedbackList.value) && feedbackList.value.length){
    infoObj = feedbackList.value.find(i=>i.feedbackId === fbId )
  }
  return {
    ...infoObj,
    feedbackId:fbId,
    ssId:sessionId.value
  }
} 

</script>

<template>
  <div id="chatBox">
    <div id="chatContainer">
      <div id="chatArea" ref="chatArea" class="ragchat_page" >
        <div v-for="(message, idx ) in messages" :key="message.content">
          <ChatMessage :message="agentParseData(message,'text')" :notNeedHeadImage="message.role==='phrase'" :isPhrase="message.role==='phrase'">
            <MarkdownRenderer :source="agentParseData(message,'text').content" @enterMessage="submitMessage" :isPhrase="message.role==='phrase'"/>
            <div class="refrence">
              <div v-for="ref in agentParseData(message,'refe').content">
                <p dir="auto" class="ref-title">{{ ref.title }}</p>
                <p :title="ref.content" class="ref-content" dir="auto">
                  {{ ref.content }}</p>
              </div>
              <div style="padding: 0 15px">
                <FeedBack :info="getFdInfo(message.feedbackId)" :copyContent="agentParseData(message,'text').content" :fbList="feedbackList"/>
              </div>
            </div>
          </ChatMessage>
        </div>
        <div v-if="currentOutputMessageContent">
          <ChatMessage :message="{ role: 'agent', content: currentOutputMessageContent,flag:'writing'}"/>
        </div>
        <div v-else-if="answerLoading">
          <ChatMessage :message="{ role: 'agent', content: '',flag:'writing' }">
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
    <div class="chat-options">
      <Checkbox v-model="knowBase" :binary="true" inputId="knowBase" />
      <label for="knowBase">结合知识库回答</label>
    </div>
    <div id="inputArea">
      <div class="input-wrap">
        <Textarea 
          v-model="messageContent"  
          @keyup.enter="submitChat" 
          id="chatInput" 
          :maxlength="knowBase ? maxTokens : null"
          class="chat-textarea"
          dir="auto"
          placeholder="输入你的问题，Enter 发送…"
        /> 
        <!-- 计数器 -->
        <span v-if="knowBase" class="char-count">
          <span :class="messageContent.length > maxTokens && 'overCount'">{{ messageContent.length }}</span>/{{ maxTokens }}
        </span>
      </div>
      <Button @click="commonPhrases" id="commonPhrases" class="phrase-btn" icon="pi pi-bookmark" label="常用语" text />
      <Button :disabled="generating.status ? true : undefined" @click="submitChat" class="submit-btn" icon="pi pi-send" label="发送" id="submitButton" />
      <Dialog v-model:visible="visibleDialog" modal header="常用语管理" class="phrase-dialog" style="width: 620px;max-width: 92vw;">
        <PopoverConfirm ref="confirm" id="ragH_p"/>
        <div class="i_textA flex items-center gap-4 mb-4" >
          <Textarea v-model="phraseContent" id="phraseInput" dir="auto"/>
          <p class="add_phrase" @click="addPhrases">
            <i class="pi pi-plus" />
          </p>
        </div>
        <div class="phrase-list">
          <div
            v-for="(item, index) in phrasesList"
            class="defalut_phrase"
            :key="index"
          >
            <span
              class="phrase-text"
              @click="clickItem(item.phrases)"
              v-tooltip="`${index + 1}. ${item.phrases}`"
              dir="auto"
            >{{ `${index + 1}. ${item.phrases}` }}</span>
            <Button @click.stop="on_delete_session($event, item.id)" rounded text icon="pi pi-trash" aria-label="删除常用语" />
          </div>
        </div>
      </Dialog>
    </div>
  </div>
</template>

<style scoped>
#chatBox {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  width: 100%;
}

#chatContainer {
  position: relative;
  flex: 1;
  min-height: 0;
  width: 100%;
}

#chatArea {
  position: absolute;
  inset: 0;
  overflow-y: auto;
  padding: 8px 4px 20px;
}

.refrence {
  margin: 10px 0 4px 50px;
  border-left: 2px solid var(--app-border);
  padding-left: 12px;
}
.ref-title {
  color: var(--app-text-2);
  font-size: 12px;
  font-weight: 600;
  margin: 2px 0;
}
.ref-content {
  color: var(--app-text-3);
  font-size: 12px;
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0 0 6px;
}

.chat-options {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px 6px;
  font-size: 13px;
  color: var(--app-text-2);
  user-select: none;
}
.chat-options label {
  cursor: pointer;
}

#inputArea {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px 12px 14px;
}
.input-wrap {
  position: relative;
  flex: 1;
  min-width: 0;
}
.chat-textarea {
  width: 100%;
  min-height: 76px;
  max-height: 180px;
  resize: vertical;
  padding: 12px 14px 26px;
  border: 1px solid var(--app-border-strong);
  background: var(--app-surface);
  color: var(--app-text);
  font-size: 14px;
  line-height: 1.6;
}
.chat-textarea:focus {
  border-color: var(--app-primary);
  box-shadow: 0 0 0 3px var(--app-primary-ring);
}
#chatInput::placeholder {
  color: var(--app-text-3);
}
.char-count {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 11px;
  color: var(--app-text-3);
  pointer-events: none;
}
.overCount {
  color: var(--app-danger);
  font-weight: 600;
}

.phrase-btn.p-button {
  height: 42px;
  flex: 0 0 auto;
  font-size: 13px;
}
.submit-btn.p-button {
  height: 42px;
  flex: 0 0 auto;
  min-width: 96px;
  font-size: 13px;
  font-weight: 600;
}

/* 常用语弹窗 */
.i_textA {
  position: relative;
  margin-bottom: 16px;
}
#phraseInput {
  width: 100%;
  min-height: 64px;
  padding: 10px 48px 10px 12px;
  background: var(--app-surface-2);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-sm);
  font-size: 14px;
}
.add_phrase {
  position: absolute;
  right: 8px;
  top: 16px;
  width: 32px;
  height: 32px;
  margin: 0;
  border-radius: 50%;
  background: var(--app-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s;
}
.add_phrase:hover { background: var(--app-primary-hover); }
.add_phrase i { font-size: 14px; color: #fff; }
.defalut_phrase {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin: 0 0 6px;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--app-text);
}
.defalut_phrase:hover { background: var(--app-surface-3); }
.phrase-list { max-height: 460px; overflow-y: auto; }
.phrase-text {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.hovered { background-color: var(--app-surface-3); }
.clicked { background-color: var(--app-surface-3); }
.item_padding { padding: 5px; }
.w-full .markdown-body { background-color: transparent; }

:deep(.ragchat_page .agentMessage .custom-icon) { width: 36px; }
:deep(.ragchat_page .agentMessage .w-full) { overflow: auto; }
</style>
