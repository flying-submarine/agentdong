<script setup lang="ts">
import { ref, reactive, toRefs,watch, onMounted } from 'vue';
import * as UUID from 'uuid';
import { serviceFetch } from '@/service/utils';
import { useUserStore } from '@/stores/user';
import { message } from 'ant-design-vue';


import ZanIcon from '@/assets/zan_icon.png';
import CaiIcon from '@/assets/cai_icon.png';
import FeedBack from '@/assets/feedback.png';

import ZanActiveIcon from '@/assets/zan_active_icon.png';
import CaiActiveIcon from '@/assets/cai_active_icon.png';
import FeedBackActive from '@/assets/feedback_active.png';

const feedback1List = [{
  value: 'Did not understand the instructions',
  label: 'Did not understand the instructions'
}, {
  value: 'Unable to understand the context',
  label: 'Unable to understand the context'
}, {
  value: 'Answered the question irrelevantly',
  label: 'Answered the question irrelevantly'
}, {
  value: 'No error found in question',
  label: 'No error found in question'
}];
const feedback2List = [{
  value: 'No reference to content in citations',
  label: 'No reference to content in citations'
}, {
  value: 'The answer is inconsistent with the facts',
  label: 'The answer is inconsistent with the facts'
}, {
  value: 'The answer logic is confusing',
  label: 'The answer logic is confusing'
}, {
  value: 'The correct reference document is not included',
  label: 'The correct reference document is not included'
}, {
  value: 'Wrong answer format',
  label: 'Wrong answer format'
}, {
  value: 'The answer is repeated',
  label: 'The answer is repeated'
}, {
  value: 'The answer is garbled',
  label: 'The answer is garbled'
}]
const feedback3List = [{
  value: 'Arabic grammar error',
  label: 'Arabic grammar error'
}, {
  value: 'The Arabic wording is incorrect',
  label: 'The Arabic wording is incorrect'
}, {
  value: 'There are missing words',
  label: 'There are missing words'
}, {
  value: 'Does not conform to Arabic expression habits',
  label: 'Does not conform to Arabic expression habits'
}, {
  value: 'The answer contains a mixture of Chinese, English and Arabic words',
  label: 'The answer contains a mixture of Chinese, English and Arabic words'
}]
const feedback4List = [{
  value: 'Sensitive/harmful reply',
  label: 'Sensitive/harmful reply'
}, {
  value: 'There is a value problem',
  label: 'There is a value problem'
}]
interface Props{
  copyContent?: string;
}
const props = defineProps<Props>();

const { user } = toRefs(useUserStore());
const score = ref('无');
let formState = reactive({
  feedback1: [],
  feedback2: [],
  feedback3: [],
  feedback4: [],
  userInput: '',
});
const feedVisible = ref(false);
const feedBackid = ref(UUID.v4());

const isInitFormState = ()=>{
  if((formState.feedback1.length===0) && (formState.feedback2.length===0) && (formState.feedback3.length===0) && (formState.feedback4.length===0) && 
  (formState.userInput==='')) {
    return true;
  }
  return false;
}

const postScore = async ()=>{

  const response = await serviceFetch('/gpt/llm/feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user: user.value,
      score: score.value,
      sessionId:"dailynews",
      content: null,
      userInput:'',
      feedbackId: feedBackid.value
    })
  });
  const res = await response.json();
  if(res.code != 200){
    message.error(res.message);
  } else {
    message.success('Feedback successfully');
  }
}

const submitFeed = async ()=>{
  if(!isInitFormState()) {
    const userInput = formState.userInput;
    const content = {
      feedback1: formState.feedback1.join(','),
      feedback2: formState.feedback2.join(','),
      feedback3: formState.feedback3.join(','),
      feedback4: formState.feedback4.join(','),
    };
    const response = await serviceFetch('/gpt/llm/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: user.value,
        score: '踩',
        sessionId:"dailynews",
        content,
        userInput,
        feedbackId: feedBackid.value
      })
    });
    const res = await response.json();
    if(res.code == 200){
      message.success('Feedback successfully');
      feedVisible.value = false;
      score.value='踩';
      formState = reactive({
        feedback1: [],
        feedback2: [],
        feedback3: [],
        feedback4: [],
        userInput: '',
      });
    } else {
      message.error(res.message);
    }
  } 
}

const showFeed = ()=>{
  feedVisible.value = !feedVisible.value;
}

const cancelFeed = ()=>{
   formState = reactive({
    feedback1: [],
    feedback2: [],
    feedback3: [],
    feedback4: [],
    userInput: '',
  });
  feedVisible.value = false;
}
const copyEvent = ()=>{
  window.navigator.clipboard.writeText(props.copyContent).then(()=>{
    message.success('Copy successfully');
  });
}

</script>


<template>
  <div class="feedback">
    <a-space :size="20" style="float: right;padding: 10px 0 4px 15px">
      <img class="back-img" :src="ZanIcon" style="height: 12px;cursor: pointer" v-if="score!=='赞'" @click="score='赞';postScore()"/>
      <img class="back-img" :src="ZanActiveIcon" style="height: 12px;cursor: pointer" v-if="score==='赞'" @click="score='无';postScore()"/>
      <img class="back-img" :src="CaiIcon" style="height: 12px;cursor: pointer" v-if="score!=='踩'" @click="showFeed()"/>
      <img class="back-img" :src="CaiActiveIcon" style="height: 12px;cursor: pointer" v-if="score==='踩'" @click="score='无';postScore()"/>
      <div style="height: 12px;width: 12px"><div class="copy-img"  @click="copyEvent" ></div></div>
    </a-space>
    <Dialog :visible="feedVisible" header="FeedBack" style="width:542px" @update:visible="cancelFeed">
      <div class="feedback-content">
        <a-form layout="vertical" class="feedback-form" :model="formState">
          <a-form-item>
            <template #label>
              <div class="feedback-label">Misunderstanding of the question</div>
            </template>
            <a-checkbox-group v-model:value="formState.feedback1">
              <a-checkbox v-for="item in feedback1List" :key="item.value" :value="item.value" name="feedback1" style="margin:4px 0;">{{item.label}}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>
          <a-form-item>
            <template #label>
              <div class="feedback-label">Poor answer</div>
            </template>
            <a-checkbox-group v-model:value="formState.feedback2">
              <a-checkbox v-for="item in feedback2List" :key="item.value" :value="item.value" name="feedback1" style="margin:4px 0;">{{item.label}}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>
          <a-form-item>
            <template #label>
              <div class="feedback-label">Arabic</div>
            </template>
            <a-checkbox-group v-model:value="formState.feedback3">
              <a-checkbox v-for="item in feedback3List" :key="item.value" :value="item.value" name="feedback1" style="margin:4px 0;">{{item.label}}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>
          <a-form-item>
            <template #label>
              <div class="feedback-label">Harmful information</div>
            </template>
            <a-checkbox-group v-model:value="formState.feedback4">
              <a-checkbox v-for="item in feedback4List" :key="item.value" :value="item.value" name="feedback1" style="margin:4px 0;">{{item.label}}</a-checkbox>
            </a-checkbox-group>
          </a-form-item>
          <a-form-item>
            <template #label>
              <div class="feedback-label">Please enter the answer you think is better：</div>
            </template>
            <a-textarea v-model:value="formState.userInput"></a-textarea>
          </a-form-item>
        </a-form>
        <div style="float:right">
          <a-space>
            <Button severity="secondary" outlined @click="cancelFeed">cancel</Button>
            <Button @click="submitFeed">submit</Button>
          </a-space>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>

.back-img:hover {
  padding: 1px
}

.feedback-content {
  /* width: 400px;
  height: 400px; */
  overflow: auto;
  &::v-deep {
    .title {
      font-size: 14px;
      font-weight: 600;
    }
    .feedback-form {
      .ant-checkbox {
        font-size: 12px;
      }
      .feedback-label {
        font-weight: 600;
        font-size: 12px;
      }
      label {
        font-size: 12px;
      }
    }
  }
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