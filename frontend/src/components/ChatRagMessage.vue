<script setup lang="ts">
import type { Message } from '@/service/ChatClient';
import { computed, nextTick } from "vue";
import HtmlRender from "./HtmlRender.vue";
import MarkdownRenderer from "./MarkdownRenderer.vue";
import ChatTimeline from "./ChatTimeline.vue";
import { ref, toRefs,reactive } from "vue";
import { onMounted, onUnmounted ,onBeforeUnmount} from 'vue';
import { watch } from 'vue';
import { useUserStore } from "@/stores/user";
const { user } = toRefs(useUserStore());
import Divider from 'primevue/divider';
import CryptoJS from 'crypto-js';
// import { el } from "element-plus/es/locale";
import { WritingSessionService } from "@/service/WritingSession";
import TurndownService from 'turndown';
import { createApp } from 'vue';
import {stream_req} from '@/service/utils'
import MarkdownIt from "markdown-it";
import userIcon from '@/assets/IconChatUser.png';
import desktopIcon from '@/assets/IconDesktop.png';

import { v4 as uuidv4 } from 'uuid'
import _ from 'lodash';
import htmlToMarkdown from 'html-to-md';
const md = new MarkdownIt();
const chatArea = ref<HTMLElement | null>(null);
interface Props {
  message: Message;
  onTextReplacement?: (row,index) => void; // 假设这是一个可选的 prop
  messageIndex?:Number;
  messageSessionId?:String;
  usePromptAugmentation?: Boolean;
  notNeedHeadImage?: Boolean;
}
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
const turndownService = new TurndownService();
const props = defineProps<Props>();

const messageClass = computed(() => {
  if(props.message.type=="timeline") return "message cardMessage";
  if(props.notNeedHeadImage) return "message cardAgentMessage"
  return props.message.role === "user"
    ? "message userMessage"
    : "message agentMessage";
});

const dropdownVisible = ref(false);
const dropdownPosition = ref({ x: 0, y: 0 });
const popupRef = ref(null);
// typescript 中的类型断言，确保 refInputSearch 是 HTMLElement 类型
const refInputSearch = ref<HTMLElement | null>(null);
const selectMessageValue = ref('-1');
const textMessages = ref('');
const originalText = ref('');
const visible = ref(false);
const textData = ref('')
const highlights = reactive([]);

// 创建一个局部的响应式状态
const localMessage = ref({ ...props.message });
const textContainer = ref(null);
// 监听 props.message 的变化，更新本地状态
watch(() => props.message, (newVal) => {
  localMessage.value = { ...newVal };
});
const htmlLight = ref('')
// 在这里定义显示下拉框的方法
const showSelectionBox = (event: MouseEvent) => {
  return 
  if (props.message.flag === 'writing') {
    console.log('查看',markdownRenderer?.value?.getSelectedText());
    
     const message = markdownRenderer?.value.getSelectedText();
       
    // markdownRenderer?.value.replaceSelectedText("11111111111111111")
    const selection = window.getSelection();
    console.log(222, props.message.flag);
    if (message&&selection?.toString()) {
      markdownRenderer?.value.highlightSelection();
      const chatArea = document.getElementById('chatArea');
      // 获取 chatArea 元素的滚动位置
      const scrollTopOffset = chatArea.scrollTop;
      const scrollLeftOffset = chatArea.scrollLeft; // 增加横向滚动偏移量
      // 考虑chatArea的边缘到页面的边缘距离
      const chatAreaRect = chatArea.getBoundingClientRect(); 
      const rect = selection.getRangeAt(0).getBoundingClientRect();
     // console.log(event.pageY);
      const selectedHtml = getSelectedHtml();
      const markdownFromHtml = htmlToMarkdowns(selectedHtml);
      // 精简和清理文本
      // 执行局部文本清理
      const cleanedSelectedText = cleanTextForMatching(markdownFromHtml);
      const cleanedContent = cleanTextForMatching(localMessage.value.content);
      textMessages.value = message;
      // textMessages.value = markdownFromHtml;

      const range = selection.getRangeAt(0);
    //   const startOffset = range.startOffset;
    //   const endOffset = range.endOffset;
      
    // const selectedNode = range.commonAncestorContainer; // 获取选中内容的共同祖先节点
    // const selectedText = selection.toString(); // 获取选中文本
    //  let ceshi =  md.render(cleanedSelectedText)
    //  console.log('测试',ceshi);
     
    // // 在这里可以根据selectedNode和selectedText来修改DOM
    // // 例如，直接替换选中文本
    // range.deleteContents(); // 删除选中内容
    // // 创建一个新的span元素，用于高亮显示
    // const highlightSpan = document.createElement('span');
    // highlightSpan.style.backgroundColor = '#3399FF'; // 或者应用任何您喜欢的高亮样式
    // htmlLight.value = uuidv4();
    // highlightSpan.setAttribute('data-highlight-id',htmlLight.value);

    // // const newNode = document.createTextNode(ceshi); // 创建新的节点来替代
    // // highlightSpan.appendChild(newNode)
    // // 创建一个临时的DOM元素来解析HTML字符串为DOM树的一部分
    // const tempContainer = document.createElement('div');
    // tempContainer.innerHTML = ceshi; // 使用innerHTML插入HTML字符串
    // const parsedHTMLContent = tempContainer.firstChild; // 获取第一个子元素，即解析后的HTML内容

    // // 将解析后的HTML内容移动到高亮span中
    // while (parsedHTMLContent.firstChild) {
    //   highlightSpan.appendChild(parsedHTMLContent.firstChild);
    // }
    //     range.insertNode(highlightSpan); // 插入新节点
        
        dropdownPosition.value = { x: event.pageX, y: event.pageY   };
        dropdownVisible.value = true;
        writingSearch.value = ''
        console.log(dropdownVisible.value,'获取到的值');
        
        } else {
          dropdownVisible.value = false;

        }
      }
    };
// const showSelectionBox = (event: MouseEvent) => {
//   if (props.message.flag === 'writing') {

//     const selection = document.getSelection();
//     console.log(222, selection?.toString());
//     if (selection?.toString()) {
//       const chatArea = document.getElementById('chatArea');
//       // 获取 chatArea 元素的滚动位置
//       const scrollTopOffset = chatArea.scrollTop;
//       const scrollLeftOffset = chatArea.scrollLeft; // 增加横向滚动偏移量
//       // 考虑chatArea的边缘到页面的边缘距离
//       const chatAreaRect = chatArea.getBoundingClientRect(); 
//       const rect = selection.getRangeAt(0).getBoundingClientRect();
//      // console.log(event.pageY);
//       const selectedHtml = getSelectedHtml();
//       const markdownFromHtml = htmlToMarkdown(selectedHtml);
//       // 精简和清理文本
//       // 执行局部文本清理
//       const cleanedSelectedText = cleanTextForMatching(markdownFromHtml);
//       const cleanedContent = cleanTextForMatching(localMessage.value.content);
//       textMessages.value = cleanedSelectedText;
//       // textMessages.value = markdownFromHtml;
//       console.log(selectedHtml,'获取html格式')

//     let searchIndex;
    
//     if(cleanedSelectedText.indexOf(' ')!==-1){
//       console.log('进入空格',cleanedSelectedText);
//       searchIndex = cleanedContent.indexOf(cleanedSelectedText);
//     }else{
//       console.log('进入');
      
//       const regex = new RegExp(`\\b${cleanedSelectedText}\\b`);

//       // 执行匹配
//       searchIndex = regex.exec(cleanedContent).index;
//     }
//     console.log('searchIndex',searchIndex);
//   // 如果找到匹配项，计算出原文中对应的索引
//   if (searchIndex !== -1) {
//     // 在原文中找到相同文本的索引
//     let actualIndex = 0;
//     let spaceCount = 0;
//     for (let i = 0; i < localMessage.value.content.length; i++) {
//       if (localMessage.value.content[i] === ' ') {
//         // 计算空格
//         spaceCount++;
//       } else {
//         // 如果遇到非空格字符，重置空格计数器
//         spaceCount = 0;
//       }
//       // 计算除去多余空格后的索引
//       actualIndex = i - spaceCount;
//       if (actualIndex >= searchIndex) {
//         // 找到匹配项的起始位置
//         break;
//       }
//     }
//     console.log('原文',localMessage.value.content);
//     // 执行替换操作
//     // props.message.content = props.message.content.substring(0, actualIndex) +"=="+
//     // textMessages.value+"==" + props.message.content.substring(actualIndex + textMessages.value.length);
//     localMessage.value.content = localMessage.value.content.substring(0, actualIndex) + "=="
//           + textMessages.value + "==" + localMessage.value.content.substring(actualIndex + textMessages.value.length);
//   }else{
//     console.log('没匹配上');
//     console.log('原文',cleanedContent);
    
//   }
//     dropdownPosition.value = { x: event.pageX, y: event.pageY   };
//     dropdownVisible.value = true;
//     writingSearch.value = ''
//     console.log(dropdownVisible.value,'获取到的值');
    
//     } else {
//       dropdownVisible.value = false;

//     }
//   }
// };
// 仅清理匹配过程的文本
function cleanTextForMatching(text) {
  // return text.replace(/\s+/g, ' ').trim();
  return text;
}

function htmlToMarkdowns(html) {
   turndownService.escape = (str) => str; // 禁用实体转义
  return turndownService.turndown(html);
}

const getSelectedHtml = () => {
  const selection = window.getSelection();
  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    const container = document.createElement('div');
    container.appendChild(range.cloneContents());
    console.log(container,'html');
    
    return container.innerHTML;
  }
  return '';
};
const dropdown = ref(null); // 用来访问下拉框的DOM元素
const tryChat = async (
  url: string,
  data: any,
) => {
  let response;
  try {
      response= await stream_req({url:url,data})
  } catch (error: any) {
    console.error(error);
    if (error.status_code === 404) {
      // await pullModelWithProgress(model);
      response = await tryChat(url, data);
      return response;
    }
  }
  return response;
};
async function selectMessage(event) {
  regenerateValue.value = selectMessageValue.value
  if (selectMessageValue.value == '1') {
    textData.value = ''
    visible.value = true
    console.log(props.usePromptAugmentation);

    let content = props.message.content
    //扩写
    // props.message.content=''
    let param = {
      data: {
        userId: user.value,
        all_content: content,
        select_content: textMessages.value,
        prompt_aug: props.usePromptAugmentation
      }
    }

      let response = await tryChat('/writing/psllm/odw/directWriting/expand', param);
      if (!response) {
        return
      }
      for await (const part of response) {
      const forceScroll = !textData.value;
      textData.value += (part ? part : '');
      scrollToBottom(true);
    }
  } else if (selectMessageValue.value == '2') {
    //缩写
    textData.value = ''
    visible.value = true
    console.log(visible);

    let content = props.message.content
    // props.message.content=''
    let param = {
      data: {
        userId: user.value,
        all_content: content,
        select_content: textMessages.value,
        prompt_aug: props.usePromptAugmentation
      }
    }
    let response = await tryChat('/writing/psllm/odw/directWriting/condense', param);
      if (!response) {
        return
      }
      for await (const part of response) {
      const forceScroll = !textData.value;
      textData.value += (part ? part : '');
      scrollToBottom(true);
    }
  } else if (selectMessageValue.value == '3') {
    //润色
    textData.value = ''
    visible.value = true
    console.log(visible);

    let content = props.message.content
    //扩写
    // props.message.content=''
    let param = {
      data: {
        userId: user.value,
        all_content: content,
        select_content: textMessages.value,
        prompt_aug: props.usePromptAugmentation
      }
    }

    let response = await tryChat('/writing/psllm/odw/directWriting/polish', param);
      if (!response) {
        return
      }
      for await (const part of response) {
      const forceScroll = !textData.value;
      textData.value += (part ? part : '');
      scrollToBottom(true);
    }
  }

}


// 阻止鼠标按下事件的默认行为来保持文本选择的高亮状态
function preventDeselect(event) {

    // 如果点击的是弹窗内的元素，则不做任何处理，即不关闭弹窗也不清除文本选择
    if (dropdownVisible.value && popupRef.value && popupRef.value.contains(event.target)) {
        return;
    }

    // 如果点击的是弹窗以外的元素，关闭弹窗并清除选择
    if (dropdownVisible.value && !visible.value && (!popupRef.value || !popupRef.value.contains(event.target))) {
      dropdownVisible.value = false;
      clearSelection();
    }
}
// 阻止指定元素失去焦点时清除文本选择
function preventBlurClearingSelection(element) {
  element.addEventListener('mousedown', (event) => {
    // 阻止 blur 事件导致的文本选择清除
    event.preventDefault();
  });
}
const isReplacing = ref(false);
function clearSelection() {
  markdownRenderer?.value.removeLight()
  if (window.getSelection) {
    const selection = window.getSelection();
    if (selection.empty) {
      selection.empty();
    } else if (selection.removeAllRanges) {
      selection.removeAllRanges();
    }
  }
}
const markdownRenderer = ref(null);
const updateContent = () => {
     const container = markdownRenderer?.value.getContainer();
     if (container) {
       const newContent = container.innerHTML;
      
       console.log('更新后的Markdown内容:', newContent);
       // 进行进一步的处理，如存储或替换等
       return newContent;
     }
     return null;
   };

async function handleOk() {
  if(commentCount.value == 2){
    await comment();
    return;
  }
  isReplacing.value = true
  let content = markdownRenderer?.value.replaceSelectedText(textData.value)
  console.log('原文',content);
  localMessage.value.content = content
  props.onTextReplacement(content, props.messageIndex);
  visible.value = false;
  textData.value = ''
  selectMessageValue.value = '-1'
  writingSearch.value = ''
  isReplacing.value = false
  dropdownVisible.value = false
  commentFlag.value = true
  clearSelection();
  scrollToBottom(true);
  return
  localMessage.value.content = localMessage.value.content.replace(/==/g, '');
// 去除 Markdown 格式化字符（比如 '**'）以及多余的空白符
// const stripMarkdown = (md) => md.replace(/(\*\*|__)(.*?)\1/g, '\$2').replace(/\s+/g, ' ');

// const normalizedContent = stripMarkdown(props.message.content);
// const normalizedSearch = stripMarkdown(textMessages.value).trim();
//   console.log('选中内容',textMessages.value);
//   console.log('原文',props.message.content);
  // 通过正则表达式找到第一个匹配项的索引
  const searchIndex = localMessage.value.content.indexOf(textMessages.value);
  
  // 如果找到匹配项，计算出原文中对应的索引
  if (searchIndex !== -1) {
    // 在原文中找到相同文本的索引
    let actualIndex = 0;
    let spaceCount = 0;
    for (let i = 0; i < localMessage.value.content.length; i++) {
      if (localMessage.value.content[i] === ' ') {
        // 计算空格
        spaceCount++;
      } else {
        // 如果遇到非空格字符，重置空格计数器
        spaceCount = 0;
      }
      // 计算除去多余空格后的索引
      actualIndex = i - spaceCount;
      if (actualIndex >= searchIndex) {
        // 找到匹配项的起始位置
        break;
      }
    }
    
    // 执行替换操作
    localMessage.value.content = localMessage.value.content.substring(0, actualIndex) +
      textData.value + localMessage.value.content.substring(actualIndex + textMessages.value.length);
      //给父组件传值
    props.onTextReplacement(localMessage.value.content,props.messageIndex)
  } else {
    console.log("无匹配项，无法替换。");
  }
  //console.log(props.message.content,'替换后');
  visible.value = false;
  textData.value = ''
  selectMessageValue.value = '-1'
  writingSearch.value = ''
}

function handleCancel(e) {
  isReplacing.value = true
  markdownRenderer?.value.removeLight()
  visible.value = false;
  textData.value = ''
  selectMessageValue.value = '-1'
  writingSearch.value = ''
  isReplacing.value = false
  dropdownVisible.value = false
  commentFlag.value = true
}

const translateContent = ref('')
const translate = async () => {
  let startTranslateContent;
  if(props.message.type=="timeline_data"){
    startTranslateContent='# '+props.message.content.storyline_title+'\n'
    for (let i = 0; i < props.message.content.context_news_relevance.length; i++) {
      startTranslateContent+=props.message.content.context_news_relevance[i].date+'\n'
      startTranslateContent+=props.message.content.context_news_relevance[i].summary+'\n'
    }
    startTranslateContent += 'Background:'+props.message.content.background_summary
  }else if (props.message.type=="card"){
    startTranslateContent='# '+props.message.content.title+'\n'
    startTranslateContent+=props.message.content.urls.replace(/<\/?[^>]+(>|$)/g, "")
  }else{
    startTranslateContent = props.message.content
  }
  // console.log(props.message, '字符长度');
  if (popoverVisible.value) {
    popoverVisible.value = false
    return;
  }
  popoverVisible.value = true
  // return
  if (startTranslateContent.length < 5000) {
    const appKey = import.meta.env.VITE_APP_KEY;
    const key = import.meta.env.VITE_API_KEY; // 注意：保密
    const salt = (new Date).getTime();
    const curtime = Math.round(new Date().getTime() / 1000);
    //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
    const from = 'auto';
    const to = 'zh-CHS';
    const str1 = appKey + truncate(startTranslateContent) + salt + curtime + key;
    //const vocabId = '您的用户词表ID';
    const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
    let param = new URLSearchParams({
      q: startTranslateContent,
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
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      console.log(data);
      translateContent.value = data.translation[0]
    } catch (error) {
      console.error('Error:', error);
    }
  } else {
    console.log('长文本操作');

    //字符大于5000的时候
    const paragraphs = startTranslateContent.split(/[\n\s]{2,}|\.|。(?<!\b(?:Dr|Mr|Ms|Mrs)\.)/);;
    let splicing = '';
    let newText = [];
    paragraphs.forEach(paragraph => {
      if (splicing.length + paragraph.length > 5000) {
        newText.push(splicing); // 上一段落累积内容达到长度限制，保存起来
        splicing = ''; // 重置累积内容
      }
      console.log(paragraph);

      splicing += paragraph + '\n\n'; // 累积新的段落内容并添加适量分隔
    });
    if (splicing.length > 0) {
      newText.push(splicing); // 添加最后一段可能未满5000字符的内容
    }
    translateContent.value = ''
    for (let i = 0; i < newText.length; i++) {
      const appKey = import.meta.env.VITE_APP_KEY;
      const key = import.meta.env.VITE_API_KEY; // 注意：保密
      const salt = (new Date).getTime();
      const curtime = Math.round(new Date().getTime() / 1000);
      //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
      const from = 'auto';
      const to = 'zh-CHS';
      const str1 = appKey + truncate(newText[i]) + salt + curtime + key;
      //const vocabId = '您的用户词表ID';
      const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
      let param = new URLSearchParams({
        q: newText[i],
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
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        console.log(data);
        translateContent.value += data.translation[0]
      } catch (error) {
        console.error('Error:', error);
      }
    }
  }
}
const truncate = (q) => {
  var len = q.length;
  if (len <= 20) return q;
  return q.substring(0, 10) + len + q.substring(len - 10, len);
}
const popoverVisible = ref(false)
watch(dropdownVisible, (v) => {
  console.log(v,'1111');
  if (v) {
    nextTick(()=>{
      retainTextSelectionOnInputFocus('#ceshi');
    })
    document.addEventListener('mousedown', preventDeselect, true);
  } else {
    // 当不显示弹出窗口时移除监听器
    document.removeEventListener('mousedown', preventDeselect, true);
  }
})

const avatarClass = computed(() => {
  return props.message.role === "user" ? "userAvatar" : "agentAvatar";
});

const avatarIconClass = computed(() => {
  return props.message.role === "user" ? userIcon : desktopIcon
});
const regenerateSearchValue = ref('')
const writingSearch = ref('');
const initSearch = ref('Please rephrase this paragraph in a more formal language and keep the overall number of words unchanged');
const onSearch = async (searchValue: string) => {
  regenerateValue.value = '4'
  regenerateSearchValue.value = searchValue
  // console.log('use value', searchValue);
  // console.log('or use this.value', writingSearch.value);
  // console.log('选中内容',textMessages.value);
  // console.log('原文:',props.message.content);
  // let data = {
  //   userId:user.value,
  //   all_content:props.message.content,
  //   select_content:textMessages.value,
  //   feedback:writingSearch.value,
  //   prompt_aug:props.message.prompt_aug,
  // }
    textData.value = ''
    visible.value = true
    console.log(visible);

    let content = props.message.content
    //扩写
    // props.message.content=''
    let param = {
      data: {
        userId: user.value,
        all_content: content,
        select_content: textMessages.value,
        feedback:writingSearch.value,
        prompt_aug: props.usePromptAugmentation
      }
    }
    let response = await tryChat('/writing/psllm/odw/directWriting/localEdit', param);
      if (!response) {
        return
      }
      for await (const part of response) {
      const forceScroll = !textData.value;
      textData.value += (part ? part : '');
      scrollToBottom(true);
    }
    // let response = await fetch(`/writing/psllm/odw/directWriting/localEdit`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' }, // 设置Content-Type头
    //   body: JSON.stringify(param), // 将对象转换为JSON字符串
    // });
    // if (response.ok) {
    //   textData.value = await response.text(); // 获取纯文本数据
    //   // console.log(textData.value,"新数据");
    // }
};

function retainTextSelectionOnInputFocus(inputSelector) {
  console.log(inputSelector);
  
  const inputElement = document.querySelector(inputSelector);
  console.log(inputElement,'阻止');
  const restoreSelection = saveAndRestoreSelection();
  inputElement.onblur = () => {
    // 输入框失去焦点时恢复文本选择
    restoreSelection();
  };
  inputElement.onfocus = (event) => {
    // 确保上一个失去焦点的元素不会破坏我们的选择
    event.preventDefault();
    // 可以放置其他处理焦点逻辑
  };
  // 阻止默认的mousedown行为，因为它可能触发blur和文本选择的丢失
  inputElement.onmousedown = (event) => {
    restoreSelection()
    //event.preventDefault();
  };
}

function saveAndRestoreSelection() {
  // 保存当前选择的范围
  let savedRange = null;
  if (window.getSelection) {
    const sel = window.getSelection();
    if (sel.rangeCount > 0) {
      savedRange = sel.getRangeAt(0);
    }
  }

  // 在输入框失去焦点之后恢复选择
  function restoreSelection() {
    const sel = window.getSelection();
    if (savedRange && sel) {
      sel.removeAllRanges();
      sel.addRange(savedRange);
    }
  }
  return restoreSelection;
}
const regenerateValue = ref('-1')
const regenerate = ()=>{
  console.log('重新生成');
  if(regenerateValue.value=='1' || regenerateValue.value == '2' || regenerateValue.value == '3'){
    selectMessage(regenerateValue.value)
  }else if (regenerateValue.value == '4'){
    onSearch(regenerateSearchValue.value)
  }
}
const commentCount = ref(1)
const commentText = ref('')
const comment = async ()=>{
  if(commentCount.value==1){
    commentFlag.value = false
    commentText.value = textData.value
    commentCount.value++;
  }else if(commentCount.value == 2){
    commentCount.value = 1
    commentFlag.value = true
    
    //提交后端
    let commentContent = {
      originalText:props.message.content, //原文
      localText:commentText.value,//局部修改文
      selectText:textMessages.value,//选中文
      inputText:textData.value,//手动修改文
      evaluate:evaluate.value,//评价
    }
    let data = {
      user:user.value,
      score:rateValue.value+"",
      sessionId:props.messageSessionId,
      content:commentContent
    }
    const response = await fetch("/llm/writing/feedback", {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(data) 
          })
    console.log(response.ok,'修改后');
    await handleOk()
    rateValue.value = 0
  }
  console.log('打分');
  
}
const commentFlag = ref(true)
const rateValue = ref<number>(0);
const evaluate = ref('')
</script>
<template>
  <div :class="messageClass" v-if="props.message.role !== 'divider'">
    <Avatar :class="avatarClass" v-if="!notNeedHeadImage">
      <!-- <i :class="avatarIconClass" style="font-size: 1rem" /> -->
      <img :src="avatarIconClass" alt="User Icon" class="custom-icon" />
    </Avatar>
    <div class="w-full" v-if="$slots.default">
      <slot></slot>
    </div>
    <div v-else-if="props.message.content == ''">
      <div class="flex flex-column ml-4">
        <Skeleton class="mb-2"></Skeleton>
        <Skeleton width="10rem" class="mb-2"></Skeleton>
        <Skeleton width="5rem" class="mb-2"></Skeleton>
        <Skeleton width="2rem" class="mb-2"></Skeleton>
      </div>
    </div>
    <div class='w-full' v-else>
      <MarkdownRenderer v-if="props.message.flag !== 'writing'"  :source="localMessage.content" @mouseup="showSelectionBox"></MarkdownRenderer>
      <HtmlRender v-else ref="markdownRenderer" :source="localMessage.content" @mouseup="showSelectionBox"></HtmlRender>
      <ChatTimeline v-if="$props.message.news_summary && $props.message.news_summary.length > 0"
        :message="$props.message" />
    </div>
    <!-- <el-popover placement="left" :width="600" class="long-popover"  trigger="click">
      <template #reference>
        <el-button class="translate-button" type="primary" @click="translate">翻译</el-button>
      </template>
      <div style="max-height: 100px;overflow: auto;">
        <MarkdownRenderer  :source="translateContent"></MarkdownRenderer>
      </div>
    </el-popover> -->
    <!-- <el-popover v-if="!$props.message.news_summary" placement="left" :visible="popoverVisible" :width="450">
      <template #reference>
        <el-button class="translate-button" type="primary" @click="translate">翻译</el-button>
      </template>
      <div class="dynamic-width-popover" style="max-height: 100px;overflow: auto;">
        <MarkdownRenderer v-if="translateContent" :source="translateContent"></MarkdownRenderer>
      </div>
    </el-popover> -->
  </div>
  <Divider align="center" type="solid" v-if="props.message.role === 'divider'">
    <span>Context Cleared</span>
  </Divider>
  <a-modal style="width: 80%;" v-model:open="visible" okText="replace" cancelText="cancel" title="Generate Summary"
    @ok="handleOk" @cancel="handleCancel"
    >
    <template v-slot:footer>
      <!-- <a-button @click="handleCancel">cancel</a-button> -->
      <a-button type="primary" style="background-color:#67c23a" @click.stop="handleOk">accept</a-button>
      <a-button type="primary" @click="regenerate">regenerate</a-button>
      <a-button type="primary" danger @click="handleCancel">adandon</a-button>
      <a-button type="primary" style="background-color:#e6a23c" @click="comment">comment</a-button>
    </template>
    <div style="display: flex;">
        <!-- 左侧内容区域 -->
        <div style="flex: 1; padding: 10px; border-right: 1px solid #f0f0f0;">
          <h3 style="text-align: center; margin-bottom: 10px;">original content</h3>
            <MarkdownRenderer :source="textMessages"></MarkdownRenderer>
        </div>
        <!-- 右侧现有内容区域 -->
        <div style="flex: 1; padding: 10px;">
          <h3 style="text-align: center; margin-bottom: 10px;">rewriting result</h3>
            <a-spin v-if="commentFlag" :spinning="textData == ''">
                <MarkdownRenderer :source="textData"></MarkdownRenderer>
            </a-spin>
            <div v-else>
                <a-textarea style="overflow: auto;" v-model:value="textData" placeholder="textarea with clear icon" allow-clear auto-size/>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
                    <label style="display: flex; align-items: center;">
                        <span style="width: 40px">评价:</span>
                        <a-input v-model:value="evaluate" style="margin-left: 8px; width: 400px;" />
                    </label>
                    <div>
                        <el-rate v-model="rateValue" show-score score-template="{value} 分" :max="10"></el-rate>
                    </div>
                </div>
            </div>
        </div>
    </div>
  </a-modal>
  <teleport to="body">
    <div v-if="dropdownVisible" class="popup"
        :style="{ position: 'absolute', left: `${dropdownPosition.x}px`, top: `${dropdownPosition.y}px`, zIndex: 1000 }"
        ref="popupRef">
        <select v-model="selectMessageValue" @change="selectMessage">
          <option value="-1">--please select--</option>
          <option value="1">expand</option>
          <option value="2">abbreviation</option>
          <option value="3">Polishing</option>
        </select>
        <a-input-search
          id="ceshi"
          v-model:value="writingSearch"
          :placeholder="initSearch"
          enter-button="Send"
          size="large"
          @search="onSearch"
          ref="refInputSearch"
        />
    </div>
  </teleport>
</template>

<style scoped>
.message {
  display: flex;
  align-items: flex-start;
  padding: 12px 14px;
  margin: 8px 0;
  border-radius: var(--app-radius);
  position: relative;
}
.message.cardMessage { padding: 0; margin: 0; }
.message.cardAgentMessage { margin: 0; padding: 0; }

.userAvatar,
.agentAvatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  flex: 0 0 34px;
  object-fit: cover;
  margin-right: 12px;
}

.w-full {
  flex: 1;
  min-width: 0;
}

/* 用户消息：靛蓝气泡 + 白字，高对比 */
.userMessage .w-full {
  background: var(--app-primary);
  color: #fff;
  border-radius: 4px 14px 14px 14px;
  padding: 12px 16px;
  box-shadow: var(--app-shadow-sm);
}
.userMessage .w-full,
.userMessage .w-full .markdown-body {
  color: #fff;
}
.userMessage .w-full code {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}
.userMessage .w-full pre {
  background: rgba(0, 0, 0, 0.25);
}

/* 助手消息：白底卡片 + 深色文字 */
.agentMessage .w-full,
.cardAgentMessage .w-full {
  background: var(--app-surface);
  color: var(--app-text);
  border: 1px solid var(--app-border);
  border-radius: 4px 14px 14px 14px;
  padding: 12px 16px;
  box-shadow: var(--app-shadow-sm);
}
.w-full .markdown-body {
  background-color: transparent;
}

.agentMessage .phrase {
  margin-top: -20px;
  border-radius: 14px;
  margin-left: 46px;
}

.translate-button {
  position: absolute !important;
  bottom: 10px;
  right: 10px;
  z-index: 10;
}
.dynamic-width-popover {
  min-height: 50px;
  max-height: 200px;
  overflow: auto;
}
.popup { position: absolute; }
.highlighted-text { background-color: #fde68a; }
</style>
