<script setup lang="ts">
// import { type Message, type ChatResponse } from "ollama";
// import { Ollama,type ChatRequest,type ChatResponse } from 'ollama'
// const ollama = new Ollama({ host: '11.163.70.215:11434' })
import { ChatClient } from '@/service/ChatClient'
import { askGraph, formatAskGraphAnswer, getDemoSessionId } from '@/service/askGraph'
const client = new ChatClient()
import { ref, toRefs } from "vue";
import ChatMessage from "./ChatMessage.vue";
import { useModelStore } from "@/stores/model";
import { WritingSessionService } from "@/service/WritingSession";
import { onMounted } from 'vue';
import { watch,nextTick } from 'vue';
import CryptoJS from 'crypto-js';
import { v4 as uuidv4 } from 'uuid'
import { useUserStore } from "@/stores/user";
const { user } = toRefs(useUserStore())
const modelStore = useModelStore();
const { currentModel } = toRefs(modelStore);
const chatArea = ref<HTMLElement | null>(null);
const answerLoading = ref(false);
const chat_history = ref([])
import {stream_req} from '@/service/utils'
import { globalState } from '@/globalState'; 
// import { scrollToBottom, upload_req, get_local_file } from '@/service/utils'
const scrollToBottom = (force: boolean) => {
  if (!chatArea.value) return;
  // don't scroll if the user has scrolled up
  if (
    !force &&
    chatArea.value.scrollHeight - chatArea.value.scrollTop >
    chatArea.value.clientHeight + 50
  ) {
    return;
  }

  // if(chatArea.value.scrollHeight==0 && chatArea.value.scrollHeight<recordTop.value){
  //   chatArea.value.scrollTop = recordTop.value;
  // }else{
  //   chatArea.value.scrollTop = chatArea.value.scrollHeight;
  //   recordTop.value = chatArea.value.scrollTop
  // }
  chatArea.value.scrollTop = chatArea.value.scrollHeight;
  EventBus.$emit('parent-scroll', chatArea.value.scrollTop);
};
const recordTop = ref(0)
const props = defineProps({
  onEntrySelect: Function
});
// const pullModelWithProgress = async (model: string) => {
//   const progress = ref(0);
//   const pullProgress = await ollama.pull({ model, stream: true });
//   for await (const part of pullProgress) {
//     progress.value = part.completed;
//     console.log(part);
//   }
// };
let refresh_sessions_handler = null;
const upload_progress = ref({ process: 0, info: '', flag: false })
const upload_file = (file, userId) => {
  if (file) {

    // 创建 XMLHttpRequest 对象
    const xhr = new XMLHttpRequest();

    // 配置 XMLHttpRequest 对象，指定上传请求的 HTTP 方法和 URL
    xhr.open('POST', `/llm/docs?user=${userId}`, true);

    upload_progress.value = { process: 0, info: 'uploading', error: false, flag: true }
    // 监听上传进度事件
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = (event.loaded / event.total) * 100;
        upload_progress.value.process = percentComplete;
        upload_progress.value.info = `uploading:${percentComplete.toFixed(2)}%`
        if (percentComplete == 100) {
          upload_progress.value.info = 'analyzing'
        }
        console.log(`Upload progress: ${percentComplete.toFixed(2)}%`);
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        init_docs()
        console.log('File uploaded successfully');
        upload_progress.value.info = 'finish'
        upload_progress.value.flag = false
        upload_progress.value = 100;

        const res = JSON.parse(xhr.response)
        // setTimeout(() => {
        const sel = {}
        sel[res.data[0].docId] = true
        selectedDocFile.value = sel
        // }, 1000)
      } else {
        const res = JSON.parse(xhr.response)
        console.log(res)
        console.error('File upload failed');
        upload_progress.value.info = res.message
        upload_progress.value.flag = false
        upload_progress.value.error = true
      }
    };

    xhr.onerror = () => {
      console.error('Error while uploading the file');
    };

    const formData = new FormData();
    formData.append('file', file);
    xhr.send(formData);
  } else {
    console.error('No file selected');
  }
}


const CHAT_MODE_FREE_CHAT = 'free chat'
const CHAT_MODE_FILE_QA = 'file QA'
const chatMode = ref(CHAT_MODE_FREE_CHAT)
// 统一走线上 /api/agt/ask_graph；产出纯文本块以复用现有 `currentOutput += part` 循环
const tryChat = async (
  model: string,
  inputMessage: string,
) => {
  const res = await askGraph(inputMessage, getDemoSessionId())
  const text = res ? formatAskGraphAnswer(res) : '连不上服务，请稍后再试'
  return (async function* () {
    yield text
  })()
};

let i = 0;
const submitChat = async () => {
  const content = messageContent.value!=''&&messageContent.value!=null?messageContent.value:initContent.value;
  if(newType.value){
    let data = {
      user: user.value,
      sessionId:sessionId.value,
      input:content,
      output:currentOutputMessageContent.value.trim(),
      history:chat_history.value
    }
   let response =  await WritingSessionService.add_history(data)
   refresh_sessions_handler()
   console.log('清空历史');
  }
 // messages.value.splice(1,2)
  answerLoading.value = true;
  // const content = messageContent.value!=''&&messageContent.value!=null?messageContent.value:initContent.value;
  messageContent.value = "";
  initContent.value = "";
  // const inputMessage = { role: "user", content };
  const inputMessage = content;
  console.log('赋值操作');
  
  messages.value.push({ role: "user", content:content ,flag:"writing"});
  scrollToBottom(true);

  const response = await tryChat(currentModel.value, inputMessage);
  
  answerLoading.value = false;
  if (!response) {console.log("进来了")
   return;}

  if(false){
    console.log(response.output);
    messages.value.push({
        role: "agent",
        content: response.output,
        prompt_aug: use_prompt_augmentation.value,
        flag:"writing"
      });
      scrollToBottom(true);
  }else{
    const appendMessage = () => {
    const content = currentOutputMessageContent.value.trim();
    if (content) {
      chat_history.value.push({
        user: inputMessage,
        bot: content
      })
      console.log(content);
      console.log(messages)
      messages.value.push({
        role: "agent",
        content: content,
        prompt_aug: use_prompt_augmentation.value,
        flag:"writing"
      });
      console.log(messages)
      scrollToBottom(true);
      console.log(refresh_sessions_handler,'刷新值');
      refresh_sessions_handler()
    }
    currentOutputMessageContent.value = "";
  };

  for await (const part of response) {
    //console.log(part,333);
    
    const forceScroll = !currentOutputMessageContent.value;

    currentOutputMessageContent.value += (part ? part : '');
    scrollToBottom(true);
  }
  
  
  if(refresh_sessions_handler === null){
    console.log('没有新数据，新增操作');
    
    //props.onEntrySelect('1')
    refresh_sessions_handler = globalState.refreshSessionHandler
    //sessionId.value = uuidv4()
    let data = {
      user: user.value,
      sessionId:sessionId.value,
      input:content,
      output:currentOutputMessageContent.value.trim(),
      history:chat_history.value
    }
    let response =  await WritingSessionService.add_history(data)
  }else{
    let data = {
      user: user.value,
      sessionId:sessionId.value,
      input:content,
      output:currentOutputMessageContent.value.trim(),
      history:chat_history.value
    }
   let response =  await WritingSessionService.add_history(data)
  }
  appendMessage();
  scrollToBottom(true);
  }
};

const messageContent = ref("");
// const messages = ref([
//   { role: "agent", content: "你好，我是你的 WakeB 智能助手，有什么可以帮你？" },
// ]);

const messages = ref([
  { role: "agent", content: "你好，我是你的 WakeB 智能助手，有什么可以帮你？",flag:"writing" },
])
const currentOutputMessageContent = ref("");

const sessionId = ref('')
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
    init_docs()
    console.log('File uploaded successfully!');
  } else {
    uploadFlag.value = false
    console.error('Error in file upload:', response.statusText);
  }
  return response
};
const uploadFile = () => {
  const el = document.createElement('input')
  el.type = 'file'
  el.click()
  el.addEventListener('change', (e) => {
    console.log(el.files)
    const file = el.files[0]
    const res = upload_file(file, user.value)
    console.log(res)

  })
}
const selectedDocFile = ref({})
const selectedOptions = ref(null)
const get_llm_docs = async (userId) => {

  return (await fetch(`/writing/psllm/odw/directWriting/example`, { headers: { 'Content-Type': 'application/json' } })).json();
}
const initContent = ref('')
const init_docs = () => {
  get_llm_docs(user.value).then((data) => {
    if (data.data) {
      console.log(data);
      
      initContent.value = data.data.choices[0].message.content
        //messages.value.push({ role: "user", content:data.data.choices[0].choices[0].content });
        //submitChat()
    } else {
      initContent.value = ''
        //messages.value.push({ role: "user", content:'' });
    }
  })
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
const message_init = () => {
  messages.value = []
  messages.value.push({ role: "agent", content: "你好，我是你的 WakeB 智能助手，有什么可以帮你？",flag:"writing" })
}
const newType = ref(false)
onMounted(() => {
  WritingSessionService.on_add_session((sid, fn) => {
    refresh_sessions_handler=null
    console.log(sid)
    chat_history.value = []
    message_init()
    init_docs()
    sessionId.value = sid
    refresh_sessions_handler = fn
    console.log(chat_history.value);
    newType.value=true
  })

  WritingSessionService.on_change_session((ss) => {
    chat_history.value = ss.chat
    messages.value = ss.message
    sessionId.value = ss.id
    // 假设 use_prompt_augmentation 是一个 ref
    const updatedMessages = messages.value.map((message) => {
      // 对于角色是 'agent' 的消息，添加 prompt 增强和标记
      if (message.role === 'agent') {
        return {
          ...message,
          prompt_aug: use_prompt_augmentation.value,
          flag: "writing"
        };
      }
      // 对于不需改变的消息，保持原样返回
      return message;
    });

    // 一次性更新 messages 的值
    messages.value = updatedMessages;

    console.log('进来了',messages.value);
    if(newType.value){
      messages.value = messages.value.splice(0,1)
      chat_history.value = []
      newType.value = false
    }
    scrollToBottom(true)
  })
  init_docs()
});

watch(user, (v) => {
//   console.log('user change:', v)
//   init_docs()
  // 当角色改变时执行的代码，比如刷新界面
  window.location.reload();
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

const use_prompt_augmentation = ref(false)

//写作替换更新到数据库
const textReplacement = async (row,index) => {
  console.log(chat_history.value,'获取到的值');
  console.log(index,'获取到的索引');
  let commentHistory = [...chat_history.value]
  commentHistory.pop(); // 移除数组中的最后一个元素
  if(index>commentHistory.length){
    let data = {
      user: user.value,
      sessionId:sessionId.value,
      input:messages.value[index-1].content,
      output:row.trim(),
      history:commentHistory
    }
   let response =  await WritingSessionService.add_history(data)
   let commentHistoryMessage = {
        bot:row.trim(),
        user:messages.value[index-1].content
   }
   commentHistory.push(commentHistoryMessage)
   chat_history.value= commentHistory
  //  if(refresh_sessions_handler === null){
  //   refresh_sessions_handler = globalState.refreshSessionHandler
  //  }
  //   refresh_sessions_handler()   
  }else{
    commentHistory[index-1].bot = row
    let data = {
      user: user.value,
      sessionId:sessionId.value,
      input:messages.value[messages.value.length-2].content,
      output:messages.value[messages.value.length-1].content,
      history:commentHistory
    }
   let response =  await WritingSessionService.add_history(data)
    commentHistory.push(chat_history.value[chat_history.value.length-1])
    chat_history.value= commentHistory
    console.log(chat_history.value);
  }
  
   
};

// watch(currentOutputMessageContent, async () => {
//   console.log('执行');
  
//   await nextTick();
//   if (chatArea.value) {
//     console.log('执行',chatArea.value.scrollHeight);
//     chatArea.value.scrollTop = chatArea.value.scrollHeight;
//   }
// });
import EventBus from '@/service/eventBus'
const handleScroll = (event)=>{
  const scrollTop = event.target.scrollTop;
  // console.log(scrollTop);
  chatArea.value.scrollTop = scrollTop;
  // // Emit the scroll event to the event bus
   EventBus.$emit('parent-scroll', scrollTop);
}
</script>

<template>
  <div id="chatBox">
    <div id="chatContainer">
      <div id="chatArea" ref="chatArea" @scroll="handleScroll">
        <div v-for="(message,index) in messages" :key="message.content">
          <ChatMessage :usePromptAugmentation="use_prompt_augmentation" :onTextReplacement="textReplacement" :messageSessionId="sessionId" :messageIndex="index" :message="message" />
        </div>
        <div v-if="currentOutputMessageContent">
          <ChatMessage :message="{ role: 'agent', content: currentOutputMessageContent,flag:'writing' }" />
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
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 5px 10px; height:60px;">
            <div style="display: flex; margin-left: auto;">
              <Button 
                  style="height: 36px;" @click="toEnglish" label="TO英语"/>
                  &nbsp;
              <Button 
                  style="height: 36px;" @click="toArabic" label="TO阿拉伯语"/>
          </div>
          <div class="flex align-items-center pl-2">
            <span>&nbsp;Prompt Augmentation&nbsp;</span>
            <ToggleSwitch v-model="use_prompt_augmentation" />
          </div>
        </div>
    <div id="inputArea">
      <Textarea :placeholder="initContent" v-model="messageContent" @keyup.enter="submitChat" id="chatInput" />
      <Button :disabled="answerLoading ? true : undefined" @click="submitChat" id="submitButton">发送</Button>
    </div>
  </div>
</template>

<style scoped>
#chatBox {
  display: flex;
  height: 100%;
  flex-direction: column;
}
#chatInput::placeholder {
  color: rgba(0, 0, 0, 0.35);
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
  height: 150px;
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
