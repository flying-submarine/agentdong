<script setup lang="ts">
// import { type Message, type ChatResponse } from "ollama";
// import { Ollama,type ChatRequest,type ChatResponse } from 'ollama'
// const ollama = new Ollama({ host: '11.163.70.215:11434' })
import { ChatClient } from '@/service/ChatClient'
const client = new ChatClient()
import { ref, toRefs } from "vue";
import ChatMessage from "./ChatMessage.vue";
import { useModelStore } from "@/stores/model";
import { onMounted } from 'vue';
import { watch,toRaw } from 'vue';
import MarkdownRenderer from "./MarkdownRenderer.vue";
import { useUserStore } from "@/stores/user";
import CryptoJS from 'crypto-js';
const { user } = toRefs(useUserStore())
const modelStore = useModelStore();
const { currentModel } = toRefs(modelStore);
const chatArea = ref<HTMLElement | null>(null);
const answerLoading = ref(false);
const chat_history = ref([])
const popover_flag = ref(true)
import { globalState } from '@/globalState'; 
import { LongReportSummarizationSession } from "@/service/LongReportSummarizationSession";
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
  chatArea.value.scrollTop = chatArea.value.scrollHeight;
};

// const pullModelWithProgress = async (model: string) => {
//   const progress = ref(0);
//   const pullProgress = await ollama.pull({ model, stream: true });
//   for await (const part of pullProgress) {
//     progress.value = part.completed;
//     console.log(part);
//   }
// };

const upload_progress = ref({ process: 0, info: '', flag: false })
// const upload_file = (file, userId) => {
//   if (file) {

//     // 创建 XMLHttpRequest 对象
//     const xhr = new XMLHttpRequest();

//     // 配置 XMLHttpRequest 对象，指定上传请求的 HTTP 方法和 URL
//     xhr.open('POST', `/longReportSummarization/llm/docs?user=${userId}`, true);

//     upload_progress.value = { process: 0, info: 'uploading', error: false, flag: true }
//     // 监听上传进度事件
//     xhr.upload.onprogress = (event) => {
//       if (event.lengthComputable) {
//         const percentComplete = (event.loaded / event.total) * 100;
//         upload_progress.value.process = percentComplete;
//         upload_progress.value.info = `uploading:${percentComplete.toFixed(2)}%`
//         if (percentComplete == 100) {
//           upload_progress.value.info = 'analyzing'
//         }
//         console.log(`Upload progress: ${percentComplete.toFixed(2)}%`);
//       }
//     };

//     xhr.onload = () => {
//       if (xhr.status === 200) {
//         init_docs()
//         console.log('File uploaded successfully');
//         upload_progress.value.info = 'finish'
//         upload_progress.value.flag = false
//         upload_progress.value = 100;
//         console.log(xhr);
        
//         const res = JSON.parse(xhr.response)
//         // setTimeout(() => {
//         const sel = {}
//         sel[res.data[0].docId] = true
//         selectedDocFile.value = sel
//         const customIntro = "# "+res.data[0].fileName+"\n\n";
//         let content = ''
//         //if (!res.data[0].docSummary.toLowerCase().startsWith("summary")) {
//             content += "# Summary\n\n" + res.data[0].docSummary; // 添加Summary标题
//         //}
      
//         markdownContent.value = customIntro+content
//         // }, 1000)
//       } else {
//         const res = JSON.parse(xhr.response)
//         console.log(res)
//         console.error('File upload failed');
//         upload_progress.value.info = res.message
//         upload_progress.value.flag = false
//         upload_progress.value.error = true
//       }
//     };

//     xhr.onerror = () => {
//       console.error('Error while uploading the file');
//     };

//     const formData = new FormData();
//     formData.append('file', file);
//     xhr.send(formData);
//   } else {
//     console.error('No file selected');
//   }
// }

const upload_file = async (file, userId) => {
  markdownContent.value=''
  popover_flag.value = true
  if (file) {
    // 使用 FormData 准备文件数据
    const formData = new FormData();
    formData.append('file', file);

    let request = {
        user:userId,
        file:file,
        prompt_aug: use_prompt_augmentation.value
    }
    upload_progress.value = { process: 0, info: 'uploading', error: false, flag: true }
    let response = await client.upload(request)
    // console.log(response);

    if (!response){console.log("进来了？");
   return};


  for await (const part of response) {
    // console.log(part,333);
    if(part.fileName){
      init_docs()
      console.log('File uploaded successfully');
      // upload_progress.value.info = 'finish'
      // upload_progress.value.flag = false
      // upload_progress.value = 100;
      const sel = {}
      sel[part.docId] = true
      selectedDocFile.value = sel
      const customIntro = "# "+part.fileName+"\n\n";
      let summary = "# Summary:\n\n"
      markdownContent.value += (customIntro+summary)
    }else{
     let content = part.output; // 添加Summary标题
      markdownContent.value+=content;
      upload_progress.value.info = 'finish'
      upload_progress.value.flag = false
      //upload_progress.value = 100;
    }

  }
  console.log('结束了吗');
  
  popover_flag.value = false
  } else {
    console.error('No file selected');
    upload_progress.value.flag = false
    upload_progress.value.error = true
  }
};

let refresh_sessions_handler = null;
const CHAT_MODE_FREE_CHAT = 'free chat'
const CHAT_MODE_FILE_QA = 'file QA'
const chatMode = ref(CHAT_MODE_FREE_CHAT)
const tryChat = async (
  model: string,
  inputMessage: string,
) => {
  let response;
  try {
    // 构建请求的URL和请求体
    response = await client.longReportSummarization({
        input: inputMessage,
        user: user.value,
        stream: true,
        doc_id: Object.keys(selectedDocFile.value)[0],
        sessionId: sessionId.value,
        history: chat_history.value,
        prompt_aug: use_prompt_augmentation.value
      });
  } catch (error: any) {
    console.error(error);
    if (error.status_code === 404) {
      // await pullModelWithProgress(model);
      response = await tryChat(model, inputMessage);
      return response;
    }
  }
  console.log(response);
  
  return response;
};

let i = 0;
const newType =ref(false)
const submitChat = async (event: Event) => {
  if (
    event instanceof KeyboardEvent &&
    (event.altKey || event.shiftKey || event.ctrlKey)
  ) {
    return;
  }
  if(newType.value){
    let data = {
      user: user.value,
      sessionId:sessionId.value,
      input:messageContent.value,
      output:currentOutputMessageContent.value.trim(),
      history:chat_history.value
    }
   let response =  await LongReportSummarizationSession.add_history('longtext',data)
   refresh_sessions_handler()
   console.log('清空历史');
  }
  answerLoading.value = true;
  const content = messageContent.value;
  messageContent.value = "";
  // const inputMessage = { role: "user", content };
  const inputMessage = content;
  messages.value.push({ role: "user", content:content });
  scrollToBottom(true);

  const response = await tryChat(currentModel.value, inputMessage);
  answerLoading.value = false;
  console.log(222,response);
  
  if (!response){console.log("进来了？");
   return};

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
      });
      console.log(messages)
      scrollToBottom(true);
      refresh_sessions_handler()
    }
    currentOutputMessageContent.value = "";
  };

  for await (const part of response) {
    const forceScroll = !currentOutputMessageContent.value;
    // currentOutputMessageContent.value += part.message.content;
    // if (part.recordId) {
    //   sessionId.value = part.recordId
    // }
    currentOutputMessageContent.value += (part.output ? part.output : '');
    // await client.sleep(50);
    scrollToBottom(true);
    // setTimeout(() => {
    //     scrollToBottom(forceScroll);
    // }, 100);
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
    let response =  await LongReportSummarizationSession.add_history('longtext',data)
  }else{
    let data = {
      user: user.value,
      sessionId:sessionId.value,
      input:content,
      output:currentOutputMessageContent.value.trim(),
      history:chat_history.value
    }
    let response =  await LongReportSummarizationSession.add_history('longtext',data)
  }
  appendMessage();
};

const messageContent = ref("What topic is this document about?");
const messages = ref([
  { role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?" },
]);
const currentOutputMessageContent = ref("");

const sessionId = ref('')
const uploadFlag = ref(false);
const markdownContent = ref('')
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

  // NodeService.getTreeNodes().then((data) => (nodes.value = data));
  return (await fetch(`/longReportSummarization/llm/docs?user=${userId}`, { headers: { 'Content-Type': 'application/json' } })).json();
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
const selectText = async ()=>{
    console.log(selectedDocFile.value);
    console.log(Object.keys(selectedDocFile.value)[0]);
    let res = await fetch(`/longReportSummarization/llm/docs/${Object.keys(selectedDocFile.value)[0]}?user=${user.value}`, { headers: { 'Content-Type': 'application/json' } })
    const jsonResult = await res.json();
    
    const customIntro = "# "+jsonResult.data.fileName+"\n";
        let content = ''
        //if (!jsonResult.data.docSummary.toLowerCase().startsWith("summary")) {
            content += "# Summary:\n" + jsonResult.data.docSummary; // 添加Summary标题
      //}
        console.log(content);
        markdownContent.value = customIntro+content
    // let res = await getDocSummary(Object.keys(selectedDocFile.value)[0], user.value);
    popover_flag.value = false
}
// const getDocSummary = async (id,user)=>{

// }
const translateContent = ref('')
const translate =async ()=>{
        const appKey = import.meta.env.VITE_APP_KEY;
        const key = import.meta.env.VITE_API_KEY; // 注意：保密
        const salt = (new Date).getTime();
        const curtime = Math.round(new Date().getTime() / 1000);
        //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
        const from = 'auto';
        const to = 'zh-CHS';
        const str1 = appKey + truncate(markdownContent.value) + salt + curtime + key;
        //const vocabId = '您的用户词表ID';
        const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
        let param = new URLSearchParams({
          q: markdownContent.value,
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
          translateContent.value = data.translation[0]
        } catch (error) {
          console.error('Error:', error);
        }
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
  messages.value.push({ role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?" })
}

onMounted(() => {
  LongReportSummarizationSession.get.on_add_session((sid, fn) => {
    refresh_sessions_handler=null
    console.log(sid)
    chat_history.value = []
    message_init()
    sessionId.value = sid
    refresh_sessions_handler = fn
    console.log(chat_history.value);
    newType.value = true
  })

  LongReportSummarizationSession.on_change_session((ss) => {
    chat_history.value = ss.chat
    messages.value = ss.message
    sessionId.value = ss.id
    
    // // 假设 use_prompt_augmentation 是一个 ref
    // const updatedMessages = messages.value.map((message) => {
    //   // 对于角色是 'agent' 的消息，添加 prompt 增强和标记
    //   if (message.role === 'agent') {
    //     return {
    //       ...message,
    //       prompt_aug: use_prompt_augmentation.value,
    //       flag: "writing"
    //     };
    //   }
    //   // 对于不需改变的消息，保持原样返回
    //   return message;
    // });

    // // 一次性更新 messages 的值
    // messages.value = updatedMessages;
    if(newType.value){
      messages.value = messages.value.splice(0,1)
      chat_history.value = []
      newType.value = false
    }
    console.log('进来了',messages.value);
    scrollToBottom(true)
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

const use_prompt_augmentation = ref(false)
</script>

<template>
  <div id="mainContainer">
    <!-- Markdown文档显示区域 -->
    <div id="markdownContainer">
        <el-popover :disabled="popover_flag" placement="left" :width="600" class="long-popover"  trigger="click">
          <template #reference>
            <el-button class="translate-button" type="primary" @click="translate">翻译</el-button>
          </template>
          <div style="height: 300px;overflow: auto;">
            <MarkdownRenderer  :source="translateContent"></MarkdownRenderer>
          </div>
        
      </el-popover>
        <!-- 这里使用您喜欢的Vue Markdown组件或者任何其他方式来展示markdown文档 -->
        <div id="chatArea" ref="chatArea">
          <MarkdownRenderer :source="markdownContent"></MarkdownRenderer>
        </div>
    </div>
    <div id="chatBox">
        <div id="chatContainer">
        <div id="chatArea" ref="chatArea">
            <div v-for="message in messages" :key="message.content">
            <ChatMessage  :message="message" />
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
        <div style="display: flex; align-items: center; justify-content: space-between; padding: 5px 10px; height:60px;">

        <TreeSelect @change="selectText" v-model="selectedDocFile" :options="selectedOptions"
            placeholder="Select Item" style="height: 36px;" />
        &nbsp;
        <Button :icon="upload_progress.flag ? 'pi pi-spin pi-spinner' : 'pi pi-upload'"
            label="upload" :disabled="upload_progress.flag" severity="info"
            style="height: 36px;" @click="uploadFile" />
        &nbsp;
            <div style="display: flex; margin-left: auto;">
              <Button 
                  style="height: 36px;" @click="toEnglish" label="TO英语"/>
                  &nbsp;
              <Button 
                  style="height: 36px;" @click="toArabic" label="TO阿拉伯语"/>
          </div>
          <span>&nbsp;Prompt Augmentation&nbsp;</span>
        <ToggleSwitch v-model="use_prompt_augmentation" />
        </div>
        <div id="inputArea">
        <Textarea v-model="messageContent" @keyup.enter="submitChat" id="chatInput" />
        <Button :disabled="answerLoading ? true : undefined" @click="submitChat" id="submitButton">Submit</Button>
        </div>
    </div>
  </div>
</template>

<style scoped>
html,
body {
  height: 100%;
  margin: 0;
}
#chatBox {
  width: 50%; /* 聊天框区域占据50%宽度 */
  display: flex;
  height: 100%;
  flex-direction: column;
  border-bottom: 1px solid #ccc;
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
#mainContainer {
  display: flex;
  height: 100%;
}

#markdownContainer {
  position: relative;
  width: 50%; /* Markdown区域占据50%宽度 */
  overflow-y: auto; /* 如果内容超出高度，显示滚动条 */
  border-right: 1px solid #ccc; /* 添加分隔线 */
  border-bottom: 1px solid #ccc;
  border-left: 1px solid #ccc;
}
.translate-button {
  position: absolute !important; /* 绝对定位 */
  top: 10px; /* 距离顶部的距离 */
  right: 10px; 
  z-index: 10; /* 确保按钮在最上层 */
}
</style>
