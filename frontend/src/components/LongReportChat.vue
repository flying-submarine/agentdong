
<script setup lang="ts">
import { v4 as uuidv4 } from 'uuid'
import { ref, toRefs } from "vue";
import ChatMessage from "./ChatMessage.vue";
import { useModelStore } from "@/stores/model";
import { LongReportSummarizationSession } from "@/service/LongReportSummarizationSession";
import { askGraph, formatAskGraphAnswer, getDemoSessionId } from '@/service/askGraph'
import { onMounted } from 'vue';
import MarkdownRenderer from './MarkdownRenderer.vue'
import { useRoute } from 'vue-router';
import LongReportClear from '@/assets/longReportClear.png';
import LongReportSubmit from '@/assets/longReportSubmit.png';
import { scrollToBottom,retrieveData,storeData} from '@/service/utils'
import { useRouter } from 'vue-router';
import FeedBack from "./NewFeedback.vue";
import { useGeneratStore } from "@/stores/generat";


const modelStore = useModelStore();
const { currentModel } = toRefs(modelStore);
const chatArea = ref<HTMLElement | null>(null);
const answerLoading = ref(false);
const chat_history = ref([])
const route = useRoute()
const router = useRouter();
const generatStore = useGeneratStore();
const feedbackList = ref([])
const referList = ref([])
const questionsList  = ref([])
const ssCreateid=ref("")
const buildFbId = ref("")
const messages = ref([
  { role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?",flag:"writing" },
])
// 获取路径中的 ID

const docId = route.params.docId ;
const emit = defineEmits({
  changePage: (value) => {}
});

// 统一走线上 /api/agt/ask_graph；产出兼容原循环的 generating/stop 块
const tryChat = async (
  model: string,
  inputMessage: string,
) => {
  buildFbId.value = uuidv4()
  const res = await askGraph(inputMessage, getDemoSessionId())
  const text = res ? formatAskGraphAnswer(res) : '连不上服务，请稍后再试'
  const retrievals = res?.sources?.length
    ? res.sources.map(sid => ({ title: sid, url: '#', content: '知识库来源块 ' + sid }))
    : []
  const self = (async function* () {
    yield { status: 'generating', output: text, retrieval: retrievals, suggestQuestions: {} }
    yield { status: 'stop', output: '' }
  })()
  return self
};
// 处理鼠标悬浮事件

const isClear = ref(false)

const clear_context = () => {
  if(generatStore.status) return 

  chat_history.value = []
  isClear.value = true 
  if (messages.value.length > 0 && messages.value[messages.value.length - 1].role !== 'divider') {
    messages.value.push({
      role: 'divider',
      content: '',
      flag: ''
    })
    scrollToBottom(chatArea);
  }
}

const replaceLastPathSegment = () => {
  // 获取当前路径
  const currentPath = router.currentRoute.value.path;
  if (!currentPath.endsWith("/x")) return 
  // 使用正则表达式替换最后一个斜杠后的路径部分为 '123456'
  const newPath = currentPath.replace(/\/[^/]*$/, `/${ssCreateid.value}`);
  // 导航到新路径
  router.push(newPath);
};
const submitChat = async () => {
  if(generatStore.status) return 
  if(!messageContent.value.trim()) return 
  const content = messageContent.value
  generatStore.setStatus(true)

 // messages.value.splice(1,2)
  answerLoading.value = true;
  // const content = messageContent.value!=''&&messageContent.value!=null?messageContent.value:initContent.value;
  messageContent.value = "";
  // const inputMessage = { role: "user", content };
  const inputMessage = content.trim();
  
  messages.value.push({ role: "user", content:content ,flag:"writing"});
  scrollToBottom(chatArea);

  const response = await tryChat(currentModel.value, inputMessage);
  answerLoading.value = false;
  if (!response) {
    return;
  }

 
  for await (const chunk of response) {
    // console.log(chunk,'chunk')
    const status = chunk.status
    if (status === 'generating') {
      if(chunk?.retrieval?.length){
        referList.value= chunk.retrieval || [] // 引用
      }
      if(chunk?.suggestQuestions && Object.values(chunk?.suggestQuestions).length){
        questionsList.value= Object.values(chunk?.suggestQuestions) || [] // 快捷问答
      }
    
      currentOutputMessageContent.value += chunk.output ?? '';
      scrollToBottom(chatArea)
    } else if (status === 'stop') {
      currentOutputMessageContent.value += chunk.output ?? '';
      // console.log(questionsList.value,'questionsList.value')
      append_message({ 
        role: 'agent',
        content: storeData(currentOutputMessageContent.value,referList.value,questionsList.value),
        feedbackId:buildFbId.value
      })
      replaceLastPathSegment()
      if(questionsList.value.length){
        questionsList.value.map(item=>{
          messages.value.push({
            role: 'phrase',
            content: item
          });
        });
      }
      if (chat_history.value.length < 1 && !isClear.value) {
        initHistory()
      }
      append_history(inputMessage,storeData(currentOutputMessageContent.value,referList.value,questionsList.value),buildFbId.value)
      currentOutputMessageContent.value = ''
      questionsList.value = []
      referList.value = []
      generatStore.setStatus(false)
      break
    }
  }
};

const append_message = (data) => {
  messages.value.push(data)
}

const append_history = (user, bot,feedbackId) => {
  chat_history.value.push({ user, bot,feedbackId })
}
const messageContent = ref("");
const currentOutputMessageContent = ref("");

// const sessionId = ref('')

const initHistory = ()=>{
  LongReportSummarizationSession.getFbackList(ssCreateid.value).then(data=>{
    feedbackList.value = data
    LongReportSummarizationSession.getHistoryChat(ssCreateid.value).then(ss => {
      if(!ss.message.length){
        return 
      }
      // console.log('longchat获取到的值：', ss);
      chat_history.value = ss.chat
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
      messages.value = newData
      scrollToBottom(chatArea)
    })
  })
}

onMounted(() => {
  ssCreateid.value = route.params.ssid === "x" ? uuidv4() : route.params.ssid ;
  route.params.ssid !== "x" && initHistory()
});


const agentParseData = (item,type)=>{
  if(item.role !== "agent") return item
  return {
    ...item,
    content:retrieveData(item.content)[type]
  }
}
const submitMessage = (content)=>{
  if(generatStore.status) return 
  messageContent.value = content
  submitChat()
}

const cP= (i)=>{
  emit("changePage",i)
}

const getFdInfo = (fbId)=>{
  let infoObj = {}
  if(Array.isArray(feedbackList.value)&& feedbackList.value.length){
    infoObj = feedbackList.value.find(i=>i.feedbackId === fbId )
  }
  return {
    ...infoObj,
    feedbackId:fbId,
    ssId:ssCreateid.value
  }
} 
</script>

<template>
  <div id="chatBox">
    <div id="chatContainer">
      <div id="chatArea" ref="chatArea" class="longr_chat_page">
        <div v-for="(message,index) in messages" :key="message.content">
          <ChatMessage 
            :messageSessionId="ssCreateid" 
            :messageIndex="index" 
            :message="agentParseData(message,'text')" 
            :notNeedHeadImage="message.role==='phrase'" :isPhrase="message.role==='phrase'"
          >
            <MarkdownRenderer 
              :source="agentParseData(message,'text').content" 
              @enterMessage="submitMessage" 
              :isPhrase="message.role==='phrase'"
            />
            <div style="margin-left: 2rem;" class="refrence">
              <div v-for="ref in agentParseData(message,'refe').content">
                Page&nbsp;&nbsp;{{ ref.page }} <a style="color:#58A9FC;text-decoration: underline" @click="cP(ref.page)">Click to Read</a>
              </div>
            </div>
            <div v-if="message.role==='agent' && index!==0" style="padding: 0 15px">
              <FeedBack :info="getFdInfo(message.feedbackId)" :copyContent="agentParseData(message,'text').content" :fbList="feedbackList"/>
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
    <div style="padding:5px 0 0 10px;" @click="clear_context">
      <img :src="LongReportClear" alt="Long Report Icon" style="width: 14px; height: 14px;margin-right:5px">
      <span>Clear Context</span>
    </div>
    <div id="inputArea">
      <div style="position: relative;flex: 1;margin-right: 10px;">
        <Textarea 
          v-model="messageContent"  
          @keyup.enter="submitChat" 
          id="chatInput" 
          style="padding-bottom: 25px;" 
          dir="auto"
        /> 
      </div>
      <Button :disabled="generatStore.status ? true : undefined" @click="submitChat" style="width:132px" label="Submit" id="submitButton">
        <img :src="LongReportSubmit" alt="Long Report Icon" style="width: 34px; height: 34px;">
      </Button>
    </div>
  </div>
</template>

<style scoped>
#chatBox {
  display: flex;
  height: 100%;
  flex-direction: column;
}

.w-full .markdown-body{
  background-color: transparent;
}

.longr_chat_page .phrase .refrence{
  display: none;
}

.longr_chat_page .userMessage  .refrence{
  display: none;
}
::v-deep .longr_chat_page .agentMessage .phrase{
   flex:1;
   width:100%!important;
}

::v-deep .longr_chat_page .agentMessage .custom-icon{
  width:36px;
}

::v-deep .longr_chat_page  .agentMessage .w-full{
  overflow: auto;
}

.refrence a:hover{
  cursor: pointer;
  background-color: rgba(88, 169, 252, 0.2);
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
  margin-bottom: 28px;
}

#phraseInput{
  width: 100%;
  height: 65px;
  padding-right: 40px;
  background-color: var(--app-primary-soft);
  border-radius: 9px;
}

.add_phrase{
  background-color: var(--app-primary);
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
