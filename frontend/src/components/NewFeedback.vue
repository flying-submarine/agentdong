<script setup lang="ts">
import { ref, reactive, toRefs,watch,onMounted } from 'vue';
import { v4 as uuidv4 } from 'uuid'
import { serviceFetch } from '@/service/utils';
import { message } from 'ant-design-vue';
import { useRoute } from 'vue-router';
import { RagSessionService } from "@/service/RagChatSession";
import { LongReportSummarizationSession } from "@/service/LongReportSummarizationSession";
import ZanIcon from '@/assets/zan_icon.png';
import CaiIcon from '@/assets/cai_icon.png';
import FeedBack from '@/assets/feedback.png';

import ZanActiveIcon from '@/assets/zan_active_icon.png';
import CaiActiveIcon from '@/assets/cai_active_icon.png';
import FeedBackActive from '@/assets/feedback_active.png';
import { linkEmits } from 'element-plus';
const route = useRoute()
// value 保持英文原文（后端依赖这些值），label 改为中文展示
const feedback1List = [{
  value: 'Did not understand the instructions',
  label: '没有理解指令要求'
}, {
  value: 'Unable to understand the context',
  label: '无法理解上下文'
}, {
  value: 'Answered the question irrelevantly',
  label: '答非所问'
}, {
  value: 'No error found in question',
  label: '问题本身没有问题'
}];
const feedback2List = [{
  value: 'No reference to content in citations',
  label: '引用中没有对应正文'
}, {
  value: 'The answer is inconsistent with the facts',
  label: '回答与事实不符'
}, {
  value: 'The answer logic is confusing',
  label: '回答逻辑混乱'
}, {
  value: 'The correct reference document is not included',
  label: '缺少正确的参考文档'
}, {
  value: 'Wrong answer format',
  label: '回答格式错误'
}, {
  value: 'The answer is repeated',
  label: '回答内容重复'
}, {
  value: 'The answer is garbled',
  label: '回答内容乱码'
}]
const feedback3List = [{
  value: 'Arabic grammar error',
  label: '阿拉伯语语法错误'
}, {
  value: 'The Arabic wording is incorrect',
  label: '阿拉伯语措辞不当'
}, {
  value: 'There are missing words',
  label: '缺少单词'
}, {
  value: 'Does not conform to Arabic expression habits',
  label: '不符合阿拉伯语表达习惯'
}, {
  value: 'The answer contains a mixture of Chinese, English and Arabic words',
  label: '中、英、阿拉伯语混杂'
}]
const feedback4List = [{
  value: 'Sensitive/harmful reply',
  label: '敏感或有害内容'
}, {
  value: 'There is a value problem',
  label: '存在价值观问题'
}]

interface Content{
  feedback4:string,
  feedback3:string,
  feedback2:string,
  feedback1:string,
}
interface Info{
  feedbackId?:string,
  ssId?:string,
  userInput?:string,
  content?:Content,
  score?:string,
}
interface Props{
  info?:Info,
  fbList,
  copyContent
}
const props = defineProps<Props>();
const score = ref('');
const itemFeedback = ref([])

const formState = reactive({
  feedback1: (props.info.content?.feedback1 || '').split(','),
  feedback2: (props.info.content?.feedback2 || '').split(','),
  feedback3: (props.info.content?.feedback3 || '').split(','),
  feedback4: (props.info.content?.feedback4 || '').split(','),
  userInput: props.info.userInput || ''
});

const feedVisible = ref(false);
const fbId = ref(uuidv4());

onMounted(() => {
  score.value = props.info.score
})

onMounted(() => {
  itemFeedback.value = props.fbList
})


const copyEvent = ()=>{
  window.navigator.clipboard.writeText(props.copyContent).then(()=>{
    message.success('复制成功');
  });
}

const updateFbList = ()=>{
  if(route.path.includes('/bussiness/Chat-With-RAG')){
    RagSessionService.getFbackList(props.info.ssId).then(data=>{
      itemFeedback.value = data
    })
  }else{
    LongReportSummarizationSession.getFbackList(props.info.ssId).then(data=>{
      itemFeedback.value = data
    })
  }
} 

const isInitFormState = ()=>{
  if((formState.feedback1.length===0) && (formState.feedback2.length===0) && (formState.feedback3.length===0) && (formState.feedback4.length===0) && 
  (formState.userInput==='')) {
    return true;
  }
  return false;
}

const sendComment = async (params)=>{
  if(itemFeedback.value.some(item=>item.feedbackId === props.info.feedbackId) ){
    const response = await serviceFetch('/gpt/llm/feedback/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        feedbackId: props.info.feedbackId ? props.info.feedbackId : fbId.value,
        ...params,
      })
    });
    const res = await response.json();
    if(res.code === 200){
      updateFbList()
      message.success('感谢反馈！');
      feedVisible.value = false;
    } else {
      message.error(res.message);
    }
  }else{
    const response = await serviceFetch('/gpt/llm/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sessionId:props.info.ssId,
        feedbackId: props.info.feedbackId ? props.info.feedbackId : fbId.value,
        ...params,
      })
    });
    const res = await response.json();
    if(res.code === 200){
      updateFbList()
      message.success('感谢反馈！');
      feedVisible.value = false;
    } else {
      message.error(res.message);
    }
  }
  
}

const submitFeed = ()=>{
  if(!isInitFormState()) {
    const userInput = formState.userInput;
    const content = {
      feedback1: formState.feedback1.join(','),
      feedback2: formState.feedback2.join(','),
      feedback3: formState.feedback3.join(','),
      feedback4: formState.feedback4.join(','),
    };
    const params = {
      score:"踩",
      content,
      userInput,
    } 
    score.value='踩';
    sendComment(params) 
  }
}

const showFeed = ()=>{
  feedVisible.value = !feedVisible.value;
}

const cancelFeed = ()=>{
  feedVisible.value = false;
}

const sendLike = (type)=>{
  const params = {
    score:type ,
  }
  sendComment(params)
}

</script>


<template>
  <div class="feedback">
    <a-space :size="20" style="float: right;padding: 10px 0 4px 15px">
      <img class="back-img" :src="ZanIcon" style="height: 12px;cursor: pointer" v-if="score!=='赞'" @click="score='赞';sendLike('赞')" />
      <img class="back-img" :src="ZanActiveIcon" style="height: 12px;cursor: pointer" v-if="score==='赞'" @click="score='无';sendLike('无')"/>
      <img class="back-img" :src="CaiIcon" style="height: 12px;cursor: pointer" v-if="score!=='踩'" @click="showFeed()"/>
      <img class="back-img" :src="CaiActiveIcon" style="height: 12px;cursor: pointer" v-if="score==='踩'" @click="score='无';sendLike('无')"/>
      <div style="height: 12px;width: 12px"><div class="copy-img" @click="copyEvent" ></div></div>
    </a-space>
    <Dialog v-model:visible="feedVisible" header="问题反馈" modal class="feedback-dialog" style="width:560px;max-width:94vw">
      <p class="feedback-intro">请告诉我们这个回答哪里不够好，帮助我们改进。</p>
      <div class="feedback-content">
        <a-form layout="vertical" class="feedback-form" :model="formState">
          <a-form-item>
            <template #label>
              <div class="feedback-label">问题理解</div>
            </template>
            <a-checkbox-group v-model:value="formState.feedback1" class="feedback-group">
              <a-checkbox v-for="item in feedback1List" :key="item.value" :value="item.value" name="feedback1" class="feedback-option">{{item.label}}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>
          <a-form-item>
            <template #label>
              <div class="feedback-label">回答质量</div>
            </template>
            <a-checkbox-group v-model:value="formState.feedback2" class="feedback-group">
              <a-checkbox v-for="item in feedback2List" :key="item.value" :value="item.value" name="feedback2" class="feedback-option">{{item.label}}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>
          <a-form-item>
            <template #label>
              <div class="feedback-label">阿拉伯语</div>
            </template>
            <a-checkbox-group v-model:value="formState.feedback3" class="feedback-group">
              <a-checkbox v-for="item in feedback3List" :key="item.value" :value="item.value" name="feedback3" class="feedback-option">{{item.label}}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>
          <a-form-item>
            <template #label>
              <div class="feedback-label">有害信息</div>
            </template>
            <a-checkbox-group v-model:value="formState.feedback4" class="feedback-group">
              <a-checkbox v-for="item in feedback4List" :key="item.value" :value="item.value" name="feedback4" class="feedback-option">{{item.label}}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>
          <a-form-item>
            <template #label>
              <div class="feedback-label">你认为更好的回答（选填）</div>
            </template>
            <a-textarea v-model:value="formState.userInput" :rows="3" placeholder="写下你期望的回答…" class="feedback-textarea" />
          </a-form-item>
        </a-form>
        <div class="feedback-footer">
          <a-space>
            <Button severity="secondary" outlined @click="cancelFeed">取消</Button>
            <Button @click="submitFeed">提交反馈</Button>
          </a-space>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>

.back-img:hover {
  padding: 1px;
}

.feedback-intro {
  margin: 0 0 14px;
  font-size: 13px;
  color: var(--app-text-2);
}
.feedback-content {
  max-height: 66vh;
  overflow-y: auto;
  padding-right: 4px;
}
.feedback-label {
  font-weight: 600;
  font-size: 13px;
  color: var(--app-text);
}
/* 选项排成整齐的两列网格，每列等宽 */
.feedback-group {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 18px;
  row-gap: 4px;
  width: 100%;
}
/* a-checkbox 是子组件，需 :deep 命中内部 wrapper，统一左对齐与行高 */
:deep(.feedback-group .ant-checkbox-wrapper) {
  display: flex;
  align-items: center;
  margin: 0 !important;
  padding: 5px 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--app-text-2);
  white-space: normal;
}
:deep(.feedback-group .ant-checkbox-wrapper .ant-checkbox) {
  align-self: flex-start;
  margin-top: 2px;
}
@media (max-width: 520px) {
  .feedback-group { grid-template-columns: 1fr; }
}
.feedback-textarea {
  border-color: var(--app-border-strong);
  border-radius: 8px;
}
.feedback-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid var(--app-border);
}
.feedback-dialog {
  color: var(--app-text);
}

.copy-img {
  background-image: url('../assets/copy.png');
  width: 12px;
  height: 12px;
  background-size: cover;
  cursor: pointer;
  &:hover {
    width: 10px;
    height: 10px;
    background-image: url('../assets/copy_active.png');
  }
}
</style>