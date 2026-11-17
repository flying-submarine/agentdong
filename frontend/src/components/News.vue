<script setup lang="ts">
import { ref, toRefs, watch } from "vue";
import ChatMessage from "./ChatMessage.vue";
import ChatTimeline from "./ChatTimeline.vue";
import ChatQuickInfo from "./ChatQuickInfo.vue";

import { onMounted } from "vue";
import Splitter from 'primevue/splitter';
import SplitterPanel from 'primevue/splitterpanel';
import { scrollToBottom, scrollToTop, serviceFetch } from "@/service/utils";
import { messageEmits } from "element-plus";
import Timeline from "primevue/timeline";
import Popover from 'primevue/popover';
import Card from 'primevue/card';
import { message } from "ant-design-vue";
import { useTokenStore } from '@/stores/token';
import Tag from 'primevue/tag'
import { reduce } from "lodash";
import ContentBox from './ContentBox.vue';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

import SortImage from '@/assets/sort.png';

import AWSATImage from '@/assets/ASHARQAL-AWSAT.png'
import ArabImage from '@/assets/ARABNEWS.png'
import JPOSTImage from '@/assets/JERUSALEMPOST.png'
import KHALEEJTIMESImage from '@/assets/KHALEEJTIMES.png'
import SAUDIGAZETTEImage from '@/assets/SAUDIGAZETTE.png'
import GULFNEWSImage from '@/assets/GULFNEWS.png'
import CnnImage from '@/assets/CNN.png';
// import moment from 'moment';
import { exportPDF } from '@/assets/exportpdf.min.js';

import { InputSelect } from 'liux-components'


const imageMap = {
  "saudigazette.com.sa": {
    title: 'SAUDI GAZETTE',
    logo: SAUDIGAZETTEImage,
    height: '14px'
  },
  "arabnews.com": {
    title: 'ARAB NEWS',
    logo: ArabImage,
    height: '21px'
  },
  "jpost.com": {
    title: 'JERUSALEM POST',
    logo: JPOSTImage,
    height: '13px'
  },
  "gulfnews.com": {
    title: 'GULF NEWS',
    logo: GULFNEWSImage,
    height: '13px'
  },
  "khaleejtimes.com": {
    title: 'KHALEEJ TIMES',
    logo: KHALEEJTIMESImage,
    height: '13px'
  },
  "english.aawsat.com": {
    title: 'ASHARQ AL-AWSAT',
    logo: AWSATImage,
    height: '18px'
  },
  "edition.cnn.com": {
    title: 'CNN',
    logo: CnnImage,
    height: '17px'
  }
}

const tokenStore = useTokenStore();
const current_message = ref("");
const news_summaries = ref([]);

const isNoneMessage = ref(false);

const nowDate = ref(new Date());
const chatArea = ref<HTMLElement | null>(null);
const rangeList = ref([
  {value: 1, label: 'Past 24 hours'},
  {value: 7, label: 'Past week'},
  {value: 30, label: 'Past month'},
  {value: 360, label: 'Past year'},
])

const selectUrlList = ref([
  'https://edition.cnn.com/', 
  'https://saudigazette.com.sa/',
  'https://www.khaleejtimes.com/',
  'https://gulfnews.com/',
  'https://www.arabnews.com/',
  'https://english.aawsat.com/',
  'https://www.jpost.com/',
  'https://www.bbc.com/'
])

let dailyFlag = true;
let searchFlag = false;
let timelineFlag = false;
let mutiViewFlag = false;
const generatingMessage = ref(false);
const messages = ref([]);
const answer_loading = ref(false);
const user_content = ref("");
const news_urls = ref([
  { label: "English aawsat", key: "https://english.aawsat.com" },
  { label: "Arab News", key: "https://www.arabnews.com" },
  { label: "Saudi gazette", key: "https://saudigazette.com.sa" },
  { label: "gulfnews", key: "https://gulfnews.com" },
  { label: "khaleejtimes", key: "https://www.khaleejtimes.com" },
  { label: "jpost", key: "https://www.jpost.com" },
  { label: "edition", key: "https://edition.cnn.com" },
]);
const news_selected = ref({});
const add_news_url_visiable = ref(false);
const add_news_data = ref({ label: "", key: "" });
const add_news_url = () => {
  news_urls.value.push({
    ...add_news_data.value,
  });
  add_news_url_visiable.value = false;
  // const auto_select = {}
  // auto_select[add_news_data.value.key] = true
  // news_selected.value = auto_select
  add_news_data.value = { label: "", key: "" };
};

const on_change_news = () => {
  // console.log(Object.keys(news_selected.value)[0])
  // console.log(news_selected.value);
};

const news_chat = ref({
  url: "https://www.arabnews.com/",
  keywords: "world cup",
  data_range: 30
});


const get_date = () => {
  const date = new Date()
  const pad_start = (n) => { return n > 9 ? n : '0' + n }
  const year = date.getFullYear();
  const month = pad_start(date.getMonth() + 1);
  const day = pad_start(date.getDate());
  return `${year}-${month}-${day}`;
  // return '2024-07-08'
}

const get_summaries = async () => {
  scrollToBottom(chatArea);
  const selected_news_urls = news_selected.value;
  // console.log(selected_news_urls)
  if (Object.keys(selected_news_urls).length == 0) {
    return
  }
  answer_loading.value = true;
  const data = {
    urls: Object.keys(selected_news_urls),
    model: 0,
    time: get_date(),
  };

  messages.value = []
  messages.value.push({
    role: "user",
    type: "card",
    content: {
      title: "Get Summaries",
      urls: "<p>" + data.urls.join("</p><p>") + "</p>",
    },
  });
  const response = await serviceFetch("/gpt/news/autogen", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  answer_loading.value = false;
  const res = await response.json();
  if (res && res.contents) {
    // const contents = Object.values(res.contents);
    const contents = res.contents;
    console.log(res)
    messages.value.push({
      role: "agent",
      content: contents.length == 0 ? "No Summaries" : "",
      news_summary: contents,
      type: "timeline",
    });
  } else {
    messages.value.push({
      role: "agent",
      content: JSON.stringify(res),
    });
  }
  scrollToBottom(chatArea);
  return response;
};

const submitChat = async () => {
  const req_data = news_chat.value;
  const submitList = (req_data.url.split('\n')||[]).filter(item=>!!item);
  if(submitList.length>3) {
     message.error("You can only input up to 3 items!");
     return;
  }
  scrollToTop(chatArea);
  answer_loading.value = true;
  messages.value = []
  // messages.value.push({
  //   role: "user",
  //   type: "card",
  //   content: {
  //     title: "Keywords",
  //     urls: `<p><b>Url: </b>${req_data.url}</p><p><b>Keywords: </b>${req_data.keywords}</p>`,
  //   },
  // });
  //news_chat.value = { url: "", keywords: "" };
  
  const response = await serviceFetch("/gpt/news/querygen", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      urls: submitList,
      keywords: req_data.keywords,
      date_range: req_data.data_range
    }),
  });
  answer_loading.value = false;
  const res = await response.json();
  if (res && res.contents && searchFlag) {
    const contents = Object.values(res.contents);
    messages.value.push({
      role: "agent",
      content: contents.length == 0 ? "No Summaries" : "",
      news_summary: contents,
      type: "timeline",
    });
  } else {
    messages.value.push({
      role: "agent",
      content: JSON.stringify(res),
    });
  }
  scrollToTop(chatArea);
  return response
};

const use_prompt_augmentation = ref(false)

onMounted(async () => {
  get_daily_top_news();
  init_timeline_topics();
  init_topic_diff();
})

const timeline_topics = ref([
  { label: 'The United States Presidential Election' },
])
const timeline_topic_selected = ref()

const get_timeline = async (topic, label) => {
  const response = await serviceFetch("/gpt/news/get_topic_timeline", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      topic,
      label,
    }),
  });
  const res = await response.json()
  return res
}

const topics_diff = ref([])
const topic_diff_selected = ref()
const get_topic_diff = async (topic, label) => {
  const response = await serviceFetch("/gpt/news/get_topic_diff", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      topic,
      label,
    }),
  });
  const res = await response.json()
  return res
}


const get_topic_diff_list = async () => {
  const response = await serviceFetch("/gpt/news/get_topic_diff_topic", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    }
  });
  const res = await response.json()
  return res
}

const init_topic_diff = async () => {
  const topics = await get_topic_diff_list()
  topics_diff.value = (topics as string[]).map(x => ({ label: x }))
}



const sentiment_color_map = ref({
  Negative: "red",
  Positive: "green",
  // Neutral: "green",
})
const get_topic_diff_data = async () => {
  const topic = topic_diff_selected.value?.label ?? ""
  if (topic === "") {
    return
  }
  messages.value = []
  // messages.value.push({
  //   role: "user",
  //   type: "card",
  //   content: {
  //     title: "Get Topic Diff",
  //     urls: "<p><b>Topic:</b>" + topic + "</p>",
  //   },
  // });
  scrollToTop(chatArea);
  answer_loading.value = true;
  const data = await get_topic_diff(topic, true)
  // const d = JSON.parse(data)
  answer_loading.value = false;
  if(!mutiViewFlag) return;
  messages.value.push({
    role: "agent",
    content: Object.keys(data).map(url_key => ({ domain: get_domain(url_key), ...data[url_key] })),
    type: "topic_diff",
  });
  scrollToTop(chatArea)
}

const init_timeline_topics = async () => {
  const topics = await get_timeline('', false)
  timeline_topics.value = (topics as string[]).map(x => ({ label: x }))
}

const get_topic_timeline = async () => {
  const topic = timeline_topic_selected.value?.label ?? ""
  if (topic === "") {
    return
  }
  messages.value = []
  // messages.value.push({
  //   role: "user",
  //   type: "card",
  //   content: {
  //     title: "Get Timeline",
  //     urls: topic,
  //   },
  // });
  answer_loading.value = true;
  scrollToTop(chatArea)
  const data = await get_timeline(topic, true)
  // data push to message
  answer_loading.value = false;
  if(!timelineFlag) return;
  //const d = JSON.parse(data)
  const timeline = data?.timeline ?? {}
  messages.value.push({
    role: "user",
    type: "card",
    content: {
      title: "Get Timeline",
      urls: topic,
    },
  });

  const list = [];
  const items = Object.keys(timeline).map(k => ({ title: '', ...timeline[k] }));
  const sortItems = items.sort((a, b) => {
    // return moment(a.date).valueOf() - moment(b.date).valueOf()
    return new Date(a.date).getTime() - new Date(b.date).getTime();
  })
  const itemsrev = sortItems.slice().reverse();
  list.push({
    role: "agent",
    content: { background: data?.background ?? '', items: itemsrev },
    type: "timeline_data",
  })
  const sortList = list.slice().reverse();
  sortList.forEach(item => {
    messages.value.push(item)
  });
  scrollToTop(chatArea);
}

const getDate = (dt)=>{
  const pad_start = (n) => { return n > 9 ? n : '0' + n }
  const year = dt.getFullYear();
  const month = pad_start(dt.getMonth() + 1);
  const day = pad_start(dt.getDate());
  return `${year}-${month}-${day}`;
}

const get_domain = (url) => {
  const pattern = /^(?:https?:\/\/)?(?:www\.)?([^\/\?]+)/i;
  return (url ?? "").match(pattern)[1] ?? ''
}

const get_daily_top_news = async () => {
  messages.value = [];
  answer_loading.value = true;
  isNoneMessage.value = false;
  generatingMessage.value = false;
  const time = getDate(nowDate.value);
  const response = await serviceFetch("/gpt/news/get_daily_news", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      time,
    }),
  });
  answer_loading.value = false;
  if(response.status == 200) {
    isNoneMessage.value = false;
    let res1 = await response.json();
    if(!dailyFlag) return;
  // res1 = JSON.parse(res1.replace('\"Mon Truc en Plumes\"', '\\\"Mon Truc en Plumes\\\"'))
    const pattern = /^(?:https?:\/\/)?(?:www\.)?([^\/\?]+)/i;
    let res;
    try {
        res = Object.keys(res1).map(k => {
        const domains = (res1[k]?.cite ?? []).map(x => ((x[1] ?? []).match(pattern)[1] ?? ''))
        res1[k].domains = domains;
        const references = (res1[k]?.source ?? []).map((item,idx)=>{
          return {
            url: item,
            title: (res1[k].refer_title && res1[k].refer_title[idx])??item,
          }
        })
        res1[k].references = references;
        return res1[k]
      })
    } catch (e) {
      console.log(e);
      isNoneMessage.value = false;
      generatingMessage.value=true;
      return;
    }
    generatingMessage.value=false;
    messages.value.push({
      role: "agent",
      content: res,
      type: "daily_news",
    });
    scrollToTop(chatArea)
  } else if(response.status == 400) {
    //let res2 = await response.json();
    isNoneMessage.value = true;
    generatingMessage.value = false;
  }
}

const sortMessage = ()=>{
  let firstMessege=[];
  let messageList = [];
  if(messages.value.length>0) {
    const list = messages.value;
    firstMessege=list.filter((item,idx)=>idx==0);
    const messageContent=list.find((item)=>item.type==="timeline_data");
    messageContent.content.items = messageContent.content.items.slice().reverse();
    messageList.push(messageContent);
  }
  messages.value =firstMessege.concat(messageList);
}

const changeTab = (val)=>{
  isNoneMessage.value=false;
  generatingMessage.value=false;
  if(val==="0") {
    dailyFlag=true;
    searchFlag=false;
    timelineFlag=false;
    mutiViewFlag=false;
    get_daily_top_news();
  } else if(val==="1") {
    dailyFlag=false;
    searchFlag=true;
    timelineFlag=false;
    mutiViewFlag=false;
  } else if(val==="2") {
    dailyFlag=false;
    searchFlag=false;
    timelineFlag=true;
    mutiViewFlag=false;
  } else {
    dailyFlag=false;
    searchFlag=false;
    timelineFlag=false;
    mutiViewFlag=true;
  }
  messages.value=[];
  answer_loading.value = false;
}

const exportPdf = () => {
  exportPDF('chatArea', 'Daily_Newsletter.pdf');
}

const addUrl = ()=>{
  console.log(news_chat.value.url, 'addurl')
  urlList.value.push(news_chat.value.url)
}

const showModal = ()=>{
  console.log("test");
}

const onSelectUrl = ()=>{
  message.error('You can only input up to 3 items!');
}

const urlList = ref([]);


const popoverList = ref(['https://www.arabnews.com/']);

watch(()=>news_chat.value.url, (newVal)=>{
    const list = (newVal.split('\n')||[]).filter(item=>!!item)
    popoverList.value = list;
})
</script>

<template>
  <div id="chatBox">
    <Tabs class="mytab" value="0" @update:value="changeTab">
      <TabList>
          <Tab value="0" style="font-size: 16px">Daily Newsletter</Tab>
          <Tab value="1" style="font-size: 16px">Quick Search</Tab>
          <Tab value="2" style="font-size: 16px">Event Timeline</Tab>
          <Tab value="3" style="font-size: 16px">Multi-Views</Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="0" >
          <div class="operate-box">
            <div class="date">
              <DatePicker :maxDate="new Date()" style="width: 292px;height: 35px;" v-model="nowDate" showIcon iconDisplay="input" dateFormat="yy/mm/dd"/>
            </div>
            <div class="operate">
              <Button style="margin-left: 5px;height: 35px;font-size: 14px" @click="get_daily_top_news">Get Newsletter</Button>
              <Button style="margin-left: 5px;height: 35px;font-size: 14px" @click="exportPdf">Export as PDF</Button>
            </div>
          </div>
        </TabPanel>
        <TabPanel value="1">
          <div class="operate-box">
            <div class="date" style="position: relative">
              <a-popover>
                <template #content>
                  <p v-for="ele in popoverList">{{ ele }}</p>
                </template>
                <div style="width: 233px;">
                  <InputSelect v-model:value="news_chat.url" :list="selectUrlList" @callback="onSelectUrl"/>
                </div>
              </a-popover>
            </div>
            <div class="date">
              <InputText dir="auto" v-model="news_chat.keywords" placeholder="Keywords" autocomplete="off" style="width: 203px;height: 35px;margin-left:6px;font-size: 14px"/>
            </div>
            <div class="date">
              <Select v-model="news_chat.data_range" optionValue="value" :options="rangeList" optionLabel="label" placeholder="Please select an item" autocomplete="off" style="width: 153px;height: 35px;margin-left:6px;font-size: 14px"/>
            </div>
            <div class="operate" style="width: 92px">
              <Button style="margin-left:5px;height: 35px;font-size: 14px" @click="submitChat">Submit</Button>
            </div>
          </div>
        </TabPanel>
        <TabPanel value="2" >
            <div class="operate-box">
              <div class="date">
                <!-- <TreeSelect style="width: 100%;height: 45px;font-size: 20px" v-model="news_selected" selectionMode="multiple" @change="on_change_news" :options="news_urls"
                  placeholder="Select News">
                  <template #value="slotProps">
                  </template>
                </TreeSelect> -->
                <Select style="width:447px;height: 35px;font-size: 14px" v-model="timeline_topic_selected" :options="timeline_topics" optionLabel="label" placeholder="Select Topic" />
              </div>
              <Button icon="pi pi-plus" style="margin-left: 5px;width: 103px;height: 35px;font-size: 14px" @click="get_topic_timeline">Get
                Timeline</Button>
            </div>
        </TabPanel>
        <TabPanel value="3" >
            <div class="operate-box">
              <div class="date">
                <Select style="width: 422px;font-size: 14px" v-model="topic_diff_selected" :options="topics_diff" optionLabel="label" placeholder="Select Multi-view" />
              </div>
              <Button icon="pi pi-plus" style="margin-left: 5px;height: 35px;width: 126px;font-size: 14px" @click="get_topic_diff_data">
                Get Multi-Views</Button>
            </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
    <div id="chatContainer">
      <div id="chatArea" ref="chatArea" v-if="!isNoneMessage">
        <div v-for="message in messages" :key="message.content">
          <ChatMessage :message="message" :notNeedHeadImage="true">
            <div
              v-if="message.type === 'timeline' && message.news_summary.length == 0">
              {{ message.content }}
            </div>
            <ChatQuickInfo v-if="message.type === 'timeline'" :message="message" />
            <div class="flex flex-column mb-2" style="margin-left: 16px;margin-top:12px" v-if="message.type === 'card'">
              <!-- <h2>{{ message.content.title }}</h2> -->
              <!-- <div v-html="message.content.urls"></div> -->
              <div style="font-size: 14px; color: #333;font-weight: 600">
                {{ message.content.urls }}
                <img @click="sortMessage" class="sort-icon" :src="SortImage" style="float: right;height: 16px;margin-right: 14px;cursor: pointer;"/>
              </div>
            </div>
            <div v-if="message.type === 'timeline_data'" style="margin-left: 16px">
              <!-- <h2>{{ message.content.storyline_title }}</h2> -->
              <Timeline :value="message.content.items" align="left" style="width: 100%">
                <template #content="slotProps">
                  <div class="flex flex-column" style="margin-top:-4px">
                    <!-- <b>{{ slotProps.item.title }}</b> -->
                    <p>{{ slotProps.item.date }}</p>
                    <p>{{ slotProps.item.summary }}</p>
                    <div style="margin-bottom: 29px">
                      <a class="more" :href="slotProps.item.source" :target="slotProps.item.source">Read More</a>
                    </div>
                  </div>
                </template>
              </Timeline>
              <!-- <p v-if="message.content.background"><b>Background:</b>{{ message.content.background
                }}
              </p> -->
            </div>

            <div v-if="message.type === 'topic_diff'" class="flex flex-column" style="background:#fff">
              <Card class="topic-card" v-for="item in message?.content ?? []" align="left">
                <template #content>
                  <div class="flex flex-column" >
                    <!-- <b>{{ slotProps.item.title }}</b> -->
                    <div class="title-box">
                      <div v-if="!!imageMap[item.domain]" class="title-topic" style="margin-bottom: 8px">{{ imageMap[item.domain].title }}</div>
                      <div v-if="!!imageMap[item.domain]" style="width: 100px;text-align: center;"><img :src="imageMap[item.domain].logo" :height="imageMap[item.domain].height"/></div>
                    </div>
                    <!-- <p style=''>{{ item.sentiment }}</p> -->
                    <!-- <div>
                      <Tag :style="{'font-weight': 'bold', color: sentiment_color_map[item?.sentiment] ?? ''}" severity="primary" :value="item?.sentiment ?? ''" rounded></Tag>
                    </div> -->
                    <p>{{ item.views }}</p>
                  </div>
                </template>
              </Card>
              <p v-if="message.content.background_summary"><b>Background:</b>{{ message.content.background_summary
                }}
              </p>
            </div>
            <div v-if="message.type === 'daily_news'" style="background: #fff">

              <Card v-for="e in message?.content ?? []" class="daily-card">
                <!-- <template #title>Simple Card</template> -->
                <template #content>
                  <div class="title">{{ e.title }}</div>
                  <!-- <p class="mb-2 gap-1 flex"><span class="tag" v-for="d in e.domains">{{d}}</span></p> -->
                  <p style="font-size: 12px">{{ e.summary }}</p>
                  <div style="font-size: 12px">Source:</div>
                  <ul>
                    <li v-for="u, i in e?.references ?? []">
                      <!-- <span class="tag">{{ e.domains[i] }}</span> -->
                      <a :href="u.url" target="_blank">[{{i+1}}]&nbsp;{{ u.title}}</a>
                    </li>
                  </ul>
                </template>
              </Card>
            </div>
          </ChatMessage>
        </div>
        <div v-if="current_message">
          <ChatMessage :message="{ role: 'agent', content: current_message }"/>
        </div>
        <div v-else-if="answer_loading">
          <ChatMessage :message="{ role: 'agent', content: '' }" :notNeedHeadImage="true">
              <div class="flex flex-column">
                <Skeleton class="mb-2"></Skeleton>
                <Skeleton width="10rem" class="mb-2"></Skeleton>
                <Skeleton width="5rem" class="mb-2"></Skeleton>
                <Skeleton width="2rem" class="mb-2"></Skeleton>
              </div>
          </ChatMessage>
        </div>
        <!-- <ChatMessage :message="{ role: 'agent', content: '' }">
          <div class="flex flex-column ml-4">
            <div style="padding:30px 5px">Here's a roundup of recent news about science and technology:</div>
          </div>
        </ChatMessage> -->
      </div>

      <div v-if="isNoneMessage">
        No newsletters available from more than a month ago.
      </div>
      <div v-if="generatingMessage">
        Loading your Daily Newsletter now.
      </div>
    </div>
    <Dialog v-model:visible="add_news_url_visiable" modal :draggable="false" header="Add Url"
      :style="{ width: '25rem' }">
      <!-- <span class="p-text-secondary block mb-5">Update your information.</span> -->
      <div class="flex align-items-center gap-3 mb-3">
        <label for="news_name" class="font-semibold w-6rem">Name</label>
        <InputText id="news_name" v-model="add_news_data.label" class="flex-auto" autocomplete="off" />
      </div>
      <div class="flex align-items-center gap-3 mb-5">
        <label for="news_url" class="font-semibold w-6rem">Url</label>
        <InputText id="news_url" v-model="add_news_data.key" class="flex-auto" autocomplete="off" />
      </div>
      <div class="flex justify-content-end gap-2">
        <Button type="button" label="Cancel" severity="secondary" @click="add_news_url_visiable = false"></Button>
        <Button type="button" label="Save" @click="add_news_url"></Button>
      </div>
    </Dialog>
  </div>
</template>

<style scoped>
#chatBox {
  box-shadow: 0 0 5px 2px rgba(87,79,215,0.10);
  background-color: #fff;
  &::v-deep .p-tabpanels {
    padding-left: 0;
    padding-top: 11px;
    padding-bottom: 20px;
  }

  &::v-deep .p-tabpanel:focus-visible {
    outline: none;
  }
  &::v-deep .mytab {
    padding: 0 18px;
  }
  &::v-deep .p-tablist-tab-list {
    border: none;
  }
  &::v-deep .p-tab {
    border-width: 0;
    padding-left: 0;
    padding-right: 0;
    margin-right: 38px;
  }
  &::v-deep .p-tab.p-tab-active {
    border-width: 0 0 3px 0;
  }
  &::v-deep .p-tab:not(.p-disabled):focus-visible {
    outline:none;
  }
}
#chatContainer {
  background: #fff;
  padding: 0 25px 11px 17px;
}

.daily-card {
  background: #F0F3FC;
  padding: 12px 16px;
  border-radius: 3px;
  margin-top: 24px;
  box-shadow: none;
  &:first-child {
    margin-top: 0;
  }
  &::v-deep .p-card-body {
    padding: 0;
    .title {
      font-size: 14px;
      font-weight: 600;
      line-height: 16px;
    }
    ul li a{
      font-size: 12px;
      color: #58A9FC;
      &:hover {
        background: transparent;
      }
    }
  }
}

.topic-card {
  background: #F0F3FC;
  padding: 12px 16px;
  border-radius: 3px;
  margin-top: 24px;
  box-shadow: none;
  &:first-child {
    margin-top: 0;
  }
  &:nth-child(7n+1) {
    background: #FDFFF8;
  }
  &:nth-child(7n+2) {
    background: #F3F4FF;
  }
  &:nth-child(7n+3) {
    background: #ECF5FF;
  }
  &:nth-child(7n+4) {
    background: rgba(220,245,250,.63);
  }
  &:nth-child(7n+5) {
    background: rgba(120,120,232,.14);
  }
  &:nth-child(7n+6) {
    background: rgba(52,230,118,0.09);
  }
  &:nth-child(7n) {
    background: rgba(124,209,255,.21);
  }
  .title-box {
    display: flex;
    justify-content: space-between;
    &::v-deep .title-topic {
      width: 230px;
      font-size: 14px;
      color: #333;
      letter-spacing: 0.12px;
      font-weight: 600;
      line-height: 20px;
    }
  }
  &::v-deep .p-card-body {
    padding: 0;
    .title {
      font-size: 22px;
      font-weight: 600;
      line-height: 24px;
    }
    ul li a{
      font-size: 14px;
      color: #58A9FC;
      &:hover {
        background: transparent;
      }
    }
  }
}

.sort-icon:hover {
  padding: 1px;
}

.tag {
  border-radius: 1rem;
  padding: 0 0.5rem;
  background-color: var(--p-primary-200);
}
.operate-box {
  display: flex;
  &::v-deep .date {
    margin-right: 10px;
    /* .p-inputtext {
      font-size: 12px;
    } */
     
  }
  /* .operate {
    flex-grow: 0;
  } */
}

.operate-box ::v-deep .date .input-select textarea {
  color: #334155;
}

ul li{
  list-style: none;
}

.horizontal_scroll {
  display: flex;
  overflow-x: auto;
  padding: 10px
}

.horizontal_scroll::-webkit-scrollbar {
  height: 12px;
}

.horizontal_scroll::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.horizontal_scroll::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 6px;
}

.horizontal_scroll::-webkit-scrollbar-thumb:hover {
  background: #555;
}

:deep(.p-timeline-event-opposite) {
  display: none !important;
}

#chatBox {
  display: flex;
  height: 100%;
  flex-direction: column;
}

.item_padding {
  padding: 5px;
}

#chatContainer {
  position: relative;
  width: 100%;
  height: 100%;
}

#chatArea {
  position: absolute;
  top: 0;
  left: 17px;
  bottom: 11px;
  right: 25px;
  overflow-y: auto;
  .more {
    font-size: 12px;
    color: #578BF7;
    &:hover {
      background: transparent;
    }
  }
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

</style>
