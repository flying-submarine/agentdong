<script setup lang="ts">
import { serviceFetch } from '@/service/utils';
import { globalState } from '@/globalState';  
import { ref, toRefs, onMounted, watch, computed } from "vue";
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
const WELCOME_TEXT = "你好，我是你的 WakeB 智能助手。\n\n我可以基于企业知识库为你答疑。直接在下方输入问题，或上传文档，自己提问相关问题。"

// 空状态推荐问题：点一下直接提问
const suggestedQuestions = [
  "Prometheus是什么 ？",
  "Kubernetes 安全加固有哪些关键措施？",
  "Rag是什么 ？"
]

const messages = ref([
  { role: "agent", content: WELCOME_TEXT, flag:"writing", welcome: true },
])

const buildFbId = ref("")
const messageContent = ref("");

const sessionId = ref('')

let refresh_sessions_handler = ()=>{};
globalState.initRagChat = ()=>{
  messages.value = []
  messages.value.push({ role: "agent", content: WELCOME_TEXT, flag:"writing", welcome: true })
}

// tryChatStream：流式问答——fetch 拿 ReadableStream，一行行读 SSE，token 回调出去；
// 最后回 done 事件（带 answer / refused / sources / confidence），和原来 /ask_graph 的返回字段对得上。
// 旧的 tryChat（一次拿整段 JSON）删掉，别留两个入口。
const tryChatStream = async (
  model,
  inputMessage,
  onToken,
) => {
  buildFbId.value = uuidv4()
  // 演示站没有登录/历史：sessionId 为空就现场生成一个，每个访客一个会话（session），
  // 记忆（MemorySaver）和限流（每分钟 10 次）都是按它分的；千万别写成固定值
  if (!sessionId.value) sessionId.value = uuidv4()
  try {
    // fetch 调新接口 /ask_graph_stream：SSE 一行行回，先 status，再一串 token，最后 done
    const res = await fetch('/api/agt/ask_graph_stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: inputMessage, session_id: sessionId.value })
    })
    if (!res.ok) return null
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    let doneEv = null
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const parts = buf.split('\n\n')
      buf = parts.pop() ?? ''
      for (const line of parts) {
        if (!line.startsWith('data: ')) continue
        const ev = JSON.parse(line.slice(6))
        if (ev.type === 'token') onToken(ev.text)
        else if (ev.type === 'done') doneEv = ev
        else if (ev.type === 'waiting_confirm') doneEv = { status: 'waiting_confirm' }
        else if (ev.type === 'error') return null
      }
    }
    return doneEv
  } catch (error) {
    console.error('ask_graph_stream failed:', error)
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
  currentOutputMessageContent.value = ''   // 先清空上一次的流式气泡
  let streamed = ''
  const response = await tryChatStream(currentModel.value, inputMessage, (t) => {
    streamed += t
    currentOutputMessageContent.value = streamed   // 每来一块字就刷一次气泡
    scrollToBottom(chatArea)
  })
  currentOutputMessageContent.value = ''   // 流完了清掉气泡，下面按老样子 append 整条
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
  messages.value.push({ role: "agent", content: WELCOME_TEXT, flag:"writing", welcome: true })
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
        <div v-for="(message, idx ) in messages" :key="idx + '-' + message.content">
          <ChatMessage :message="agentParseData(message,'text')" :notNeedHeadImage="message.role==='phrase'" :isPhrase="message.role==='phrase'">
            <MarkdownRenderer :source="agentParseData(message,'text').content" @enterMessage="submitMessage" :isPhrase="message.role==='phrase'"/>

            <!-- 欢迎语：给出可点的推荐问题，不显示毫无意义的点赞/点踩/复制 -->
            <div v-if="message.welcome" class="welcome-suggestions">
              <button
                v-for="q in suggestedQuestions"
                :key="q"
                type="button"
                class="suggestion-chip"
                @click="submitMessage(q)"
              >
                <i class="pi pi-sparkles" aria-hidden="true"></i>
                <span>{{ q }}</span>
              </button>
            </div>

            <!-- 真实回答：引用与反馈 -->
            <div v-else-if="message.role === 'agent'" style="margin-left: 2rem;" class="refrence" >
              <div v-for="ref in agentParseData(message,'refe').content">
                <p dir = "auto" class="ref-title">{{ ref.title }}</p>
                <p :title="ref.content" style='overflow: hidden; white-space:nowrap;font-style: italic; text-overflow: ellipsis' dir = "auto">
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
    <div class="composer">
      <div class="composer-options">
        <label class="kb-toggle">
          <Checkbox v-model="knowBase" :binary="true" inputId="kbCheckbox" />
          <span>检索知识库作答</span>
        </label>
        <span class="kb-hint">开启后，回答会参考知识库中的文档内容</span>
      </div>
      <div id="inputArea">
        <div class="input-wrap">
          <Textarea
            v-model="messageContent"
            @keyup.enter.exact.prevent="submitChat"
            id="chatInput"
            :maxlength="knowBase ? maxTokens : null"
            placeholder="输入你的问题，按 Enter 发送…"
            dir="auto"
          />
          <!-- 计数器 -->
          <span v-if="knowBase" class="char-counter">
            <span :class="messageContent.length > maxTokens && 'overCount'">{{ messageContent.length }}</span>/{{maxTokens}}
          </span>
        </div>
        <Button @click="commonPhrases" id="commonPhrases" label="常用语" icon="pi pi-bookmark" class="composer-btn" text />
        <Button :disabled="generating.status ? true : undefined" @click="submitChat" label="发送" icon="pi pi-send" id="submitButton" class="composer-btn composer-submit"/>
      </div>
      <Dialog v-model:visible="visibleDialog" modal header="常用语" style="width: 650px;z-index:900">
        <PopoverConfirm ref="confirm" id="ragH_p"/>
        <p class="dialog-tip">添加后，点击任意常用语即可快速提问（最多 10 条）</p>
        <div class="i_textA flex items-center gap-4 mb-4" >
          <Textarea v-model="phraseContent" id="phraseInput" dir="auto" placeholder="输入一条常用语…"/>
          <button type="button" class="add_phrase" @click="addPhrases" aria-label="添加常用语">
            <i class="pi pi-plus" aria-hidden="true" />
          </button>
        </div>
        <div class="phrase-list">
          <div
            v-for="(item, index) in phrasesList"
            class="defalut_phrase"
            :key="item.id ?? index"
          >
            <span
              class="phrase-text"
              @click="clickItem(item.phrases)"
              v-tooltip="item.phrases"
              dir="auto"
            >{{ `${index + 1}. ${item.phrases}` }}</span>
            <Button @click.stop="on_delete_session($event,item.id)" rounded text class="phrase-delete" icon="pi pi-trash" aria-label="删除" />
          </div>
          <p v-if="!phrasesList.length" class="phrase-empty">还没有常用语，在上方添加一条吧</p>
        </div>
      </Dialog>
    </div>
  </div>
</template>

<style scoped>
#chatBox {
  display: flex;
  flex: 1;          /* 作为 .rag-content(flex 容器)的子项，必须自己撑满主轴，否则右侧留白 */
  min-width: 0;
  height: 100%;
  flex-direction: column;
}

.ragchat_page .phrase .refrence,
.ragchat_page .userMessage .refrence {
  display: none;
}

::v-deep .ragchat_page .agentMessage .custom-icon { width: 36px; }

/* 让助手气泡铺满整行（共享组件默认 max-width:74% 会留一大片空白）。
   只在本页覆盖，不影响 News / Writing 等其他共用 ChatMessage 的页面。 */
::v-deep .ragchat_page .agentMessage .w-full {
  flex: 1 1 auto;
  max-width: 100%;
  overflow: auto;
}

.hovered { background-color: var(--app-surface-3); }
.clicked { background-color: var(--app-surface-3); }
.overCount { color: var(--app-danger); }
.w-full .markdown-body { background-color: transparent; }
.item_padding { padding: 5px; }

.ref-title { color: var(--app-text); font-weight: 600; }

/* ---------- 欢迎语 + 空状态推荐问题 ---------- */
.welcome-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 18px 0 6px 2rem;
}
.suggestion-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 15px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 999px;
  color: var(--app-text-2);
  font-size: 13px;
  line-height: 1.4;
  cursor: pointer;
  transition: all 0.15s;
}
.suggestion-chip i { color: var(--app-primary); font-size: 13px; }
.suggestion-chip:hover {
  border-color: var(--app-primary);
  background: var(--app-primary-soft);
  color: var(--app-primary);
  transform: translateY(-1px);
}

#chatContainer {
  position: relative;
  width: 100%;
  flex: 1;
  min-height: 0;
}
#chatArea {
  position: absolute;
  inset: 0;
  overflow-y: auto;
  padding: 22px 24px 8px;
}

/* ---------- 输入区 ---------- */
.composer {
  flex: 0 0 auto;
  padding: 0 14px 14px;
}
.composer-options {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding-left: 2px;
}
.kb-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: var(--app-text);
  cursor: pointer;
  user-select: none;
}
.kb-hint {
  font-size: 12px;
  color: var(--app-text-3);
}
#inputArea {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  width: 100%;
}
.input-wrap {
  position: relative;
  flex: 1;
  min-width: 0;
}
#chatInput {
  width: 100%;
  min-height: 72px;
  max-height: 180px;
  padding: 12px 14px 26px;
  border: 1px solid var(--app-border-strong);
  border-radius: var(--app-radius);
  background: var(--app-surface);
  color: var(--app-text);
  resize: none;
  line-height: 1.6;
  transition: border-color 0.15s, box-shadow 0.15s;
}
#chatInput:focus {
  outline: none;
  border-color: var(--app-primary);
  box-shadow: 0 0 0 3px var(--app-primary-ring);
}
#chatInput::placeholder { color: var(--app-text-3); }
.char-counter {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 12px;
  color: var(--app-text-3);
  pointer-events: none;
}
.composer-btn.p-button {
  height: 44px;
  flex: 0 0 auto;
  font-size: 14px;
  font-weight: 600;
}
.composer-submit.p-button { min-width: 104px; }

/* ---------- 常用语弹窗 ---------- */
.dialog-tip { font-size: 12px; color: var(--app-text-2); margin-bottom: 12px; }
.i_textA { position: relative; margin-bottom: 12px; }
#phraseInput {
  width: 100%;
  height: 62px;
  padding: 10px 48px 10px 12px;
  border: 1px solid var(--app-border-strong);
  border-radius: var(--app-radius-sm);
  background: var(--app-surface);
  color: var(--app-text);
  resize: none;
}
#phraseInput:focus { outline: none; border-color: var(--app-primary); box-shadow: 0 0 0 3px var(--app-primary-ring); }
.add_phrase {
  position: absolute;
  right: 10px;
  top: 15px;
  width: 32px;
  height: 32px;
  border: none;
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
.phrase-list { max-height: 340px; overflow-y: auto; }
.defalut_phrase {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 8px;
  border-bottom: 1px solid var(--app-border);
  border-radius: 6px;
}
.defalut_phrase:hover { background: var(--app-primary-soft); cursor: pointer; }
.phrase-text {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
  color: var(--app-text);
}
.phrase-delete.p-button { color: var(--app-text-3); flex: 0 0 auto; }
.phrase-delete.p-button:hover { color: var(--app-danger); background: #fef3f2; }
.phrase-empty { text-align: center; color: var(--app-text-3); font-size: 13px; padding: 24px 0; }

@media (max-width: 600px) {
  .kb-hint { display: none; }
  .composer-btn.p-button { padding: 0 12px; }
}
</style>
