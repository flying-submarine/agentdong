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
import { askGraph, formatAskGraphAnswer } from '@/service/askGraph';

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

// 线上 /api/agt/ask_graph_stream 会 404（网关未放开），统一走稳定的 /api/agt/ask_graph。
// 返回结构直接就是 submitChat 需要的 { status, answer, refused, sources, confidence }，
// 与旧 SSE done 事件字段一致；onToken 用本地分片模拟逐字效果，复用原有打字机渲染。
const tryChatStream = async (
  model,
  inputMessage,
  onToken,
) => {
  buildFbId.value = uuidv4()
  // 演示站没有登录/历史：sessionId 为空就现场生成一个，每个访客一个会话（session），
  // 记忆（MemorySaver）和限流（每分钟 10 次）都是按它分的；千万别写成固定值
  if (!sessionId.value) sessionId.value = uuidv4()
  const res = await askGraph(inputMessage, sessionId.value)
  if (!res) return null
  // 本地分片喂给气泡，模拟 SSE 的逐字出现（网络仍是一次 POST，观感不变）
  const full = formatAskGraphAnswer(res)
  const chunk = 8
  for (let i = 0; i < full.length; i += chunk) {
    onToken(full.slice(i, i + chunk))
    await new Promise(r => setTimeout(r, 24))
  }
  return res
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
            <div style="margin-left: 2rem;" class="refrence" >
              <div v-for="ref in agentParseData(message,'refe').content">
                <p dir = "auto" style="color: black">{{ ref.title }}</p>
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
    <div style="padding-left: 10px;">
      <Checkbox v-model="knowBase" style="margin-right:10px;" :binary="true" /> 
      <span >Chat with Knowledge Base</span>
    </div>
    <div id="inputArea">
      <div style="position: relative;flex: 1;margin-right: 10px;">
        <Textarea 
          v-model="messageContent"  
          @keyup.enter="submitChat" 
          id="chatInput" 
          :maxlength="knowBase ? maxTokens : null"
          style="padding-bottom: 25px;" 
          dir = "auto"
        /> 
        <!-- 计数器 -->
        <span v-if="knowBase" style="position: absolute; bottom: 5px; right: 10px; font-size: 12px; color: gray;">
          <span :class="messageContent.length>maxTokens && 'overCount' ">{{ messageContent.length }}</span>/{{maxTokens}}
        </span>
      </div>
      <Button  @click="commonPhrases" id="commonPhrases" label="Common Phrases" style="margin-right:5px;width:132px;font-size: 16px;"/>
      <Button :disabled="generating.status ? true : undefined" @click="submitChat" style="width:132px;font-size: 16px;" label="Submit" id="submitButton"/>
      <Dialog v-model:visible="visibleDialog" modal header="Common Phrases" style="width: 650px;z-index:900">
        <PopoverConfirm ref="confirm" id="ragH_p"/>
        <div class="i_textA flex items-center gap-4 mb-4" >
          <Textarea v-model="phraseContent" id="phraseInput" dir="auto"/>
          <p class="add_phrase" @click="addPhrases">
            <i class="pi pi-plus" style="font-size: 1.5rem ; color: #ffffff" />
          </p>
        </div>
        <div style="max-height:460px;overflow-y: hidden;" >
          <p 
            v-for="(item, index) in phrasesList" 
            class="defalut_phrase" 
            :key="index"
          >
          <p 
            @click="clickItem(item.phrases)"  
            v-tooltip="`${index + 1}. ${item.phrases}`"
            style="width: 90%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"
            dir = "auto"
          >
            {{ `${index + 1}. ${item.phrases}` }}
          </p>
            <Button @click.stop="on_delete_session($event,item.id)" rounded text style="font-size: 1rem;color: #666666;" icon="pi pi-trash" />
          </p>
        </div>
      </Dialog>
    </div>
  </div>
</template>

<style scoped>
#chatBox {
  display: flex;
  height: 100%;
  flex-direction: column;
}

.ragchat_page .phrase .refrence{
  display: none;
}

.ragchat_page .userMessage  .refrence{
  display: none;
}

::v-deep .ragchat_page .agentMessage .custom-icon{
  width:36px;
}

::v-deep .ragchat_page  .agentMessage .w-full{
  overflow: auto;
}


/* 悬浮时的背景色 */
.hovered {
  background-color: #f0f0f0;
}
.overCount{
  color:red;
}
/* 点击后的背景色 */
.clicked {
  background-color: #dcdcdc;
}
#chatInput::placeholder {
  color: rgba(0, 0, 0, 0.35);

}
.w-full .markdown-body{
  background-color: transparent;
}
.item_padding {
  padding: 5px;
}
.defalut_phrase{
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.defalut_phrase:hover{
  background: rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

#chatContainer {
  position: relative;
  width: 100%;
  height: 100%;
}

#chatArea {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  right: 0;
  overflow-y: auto;
}
.i_textA{
  position:relative;
  margin-bottom: 10px;
}

#phraseInput{
  width: 100%;
  height: 65px;
  padding-right: 40px;
  background-color: rgba(68,64,255,0.1);
  border-radius: 9px;
}

.add_phrase{
  background-color: rgba(149,148,255,1);
  position: absolute;
  width:32px;
  height:32px;
  border-radius: 16px;
  right:9px;
  top:17px;
  display: flex;
  justify-content: center;
  align-items: center;
}

#inputArea {
  display: flex;
  height: 87px;
  width: 100%;
  padding: 10px;
}

#chatInput {
  width: 100%;
  height: 100%;
  padding: 10px;
  border-color:#BCD2FF;
  resize: none;
}

</style>
