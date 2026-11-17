<script setup lang="ts">
import { ref, toRefs } from "vue";
import ChatMessage from "./ChatMessage.vue";
import ChatTimeline from "./ChatTimeline.vue";
import { onMounted } from "vue";
import { scrollToBottom } from "@/service/utils";
import { messageEmits } from "element-plus";
import Timeline from "primevue/timeline";
import Popover from 'primevue/popover';
import Card from 'primevue/card';
import Tag from 'primevue/tag'
import { reduce } from "lodash";


const current_message = ref("");
const news_summaries = ref([]);


const chatArea = ref<HTMLElement | null>(null);

const messages = ref([
  // { role: "agent", content: "Hello，I am your Wakeb GPT Copilot. How can I help you?" },
  // {
  //   role: "user",
  //   content: "Help me summarize the latest news about science and technology please",
  // },
  // {
  //   role: "agent",
  //   content: "Here's a roundup of recent news about science and technology:",
  //   news_summary: events,
  // },
]);
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
  const response = await fetch("/news/autogen", {
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
  scrollToBottom(chatArea);
  answer_loading.value = true;
  const req_data = news_chat.value;

  messages.value = []
  messages.value.push({
    role: "user",
    type: "card",
    content: {
      title: "Keywords",
      urls: `<p><b>Url: </b>${req_data.url}</p><p><b>Keywords: </b>${req_data.keywords}</p>`,
      // keywords: req_data.keywords,
    },
  });
  news_chat.value = { url: "", keywords: "" };
  const response = await fetch("/news/querygen", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      urls: req_data.url,
      keywords: req_data.keywords,
    }),
  });
  answer_loading.value = false;
  const res = await response.json();
  if (res && res.contents) {
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
  scrollToBottom(chatArea);
  return response
};

const use_prompt_augmentation = ref(false)

onMounted(async () => {
  init_timeline_topics()
  init_topic_diff()
})

const timeline_topics = ref([
  { label: 'The United States Presidential Election' },
])
const timeline_topic_selected = ref()

const get_timeline = async (topic, label) => {
  const response = await fetch("/news/get_topic_timeline", {
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
  const response = await fetch("/news/get_topic_diff", {
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


const init_topic_diff = async () => {
  const topics = await get_topic_diff('', false)
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
  messages.value.push({
    role: "user",
    type: "card",
    content: {
      title: "Get Topic Diff",
      urls: "<p><b>Topic:</b>" + topic + "</p>",
    },
  });
  scrollToBottom(chatArea)
  const data = await get_topic_diff(topic, true)
  // const d = JSON.parse(data)
  messages.value.push({
    role: "agent",
    content: Object.keys(data).map(url_key => ({ domain: get_domain(url_key), ...data[url_key] })),
    type: "topic_diff",
  });
  scrollToBottom(chatArea)
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
  messages.value.push({
    role: "user",
    type: "card",
    content: {
      title: "Get Timeline",
      urls: "<p><b>Topic:</b>" + topic + "</p>",
    },
  });
  scrollToBottom(chatArea)
  const data = await get_timeline(topic, true)
  // data push to message

  const d = JSON.parse(data)
  const timeline = d?.timeline ?? {}
  messages.value.push({
    role: "agent",
    content: { background: d?.background ?? '', items: Object.keys(timeline).map(k => ({ title: k, ...timeline[k] })) },
    type: "timeline_data",
  });
  scrollToBottom(chatArea)
}

// const timeline_popover = ref<InstanceType<typeof Popover> | null>(null)
// const popover_timeline = (e) => {
//   timeline_popover.value.toggle(e)
// }

const get_domain = (url) => {
  const pattern = /^(?:https?:\/\/)?(?:www\.)?([^\/\?]+)/i;
  return (url ?? "").match(pattern)[1] ?? ''
}

const get_daily_top_news = async () => {
  messages.value = []
  const response = await fetch("/news/get_daily_news", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      time: get_date(),
    }),
  });
  let res1 = await response.json()
  // res1 = JSON.parse(res1.replace('\"Mon Truc en Plumes\"', '\\\"Mon Truc en Plumes\\\"'))
  const pattern = /^(?:https?:\/\/)?(?:www\.)?([^\/\?]+)/i;
  const res = Object.keys(res1).map(k => {
    const domains = (res1[k]?.cite ?? []).map(x => ((x[1] ?? []).match(pattern)[1] ?? ''))
    res1[k].domains = domains
    return res1[k]
  })


  messages.value.push({
    role: "agent",
    content: res,
    type: "daily_news",
  });
  scrollToBottom(chatArea)
}
</script>

<template>
  <div id="chatBox">
    <div style="overflow-x: auto; display: flex; padding:5px; height:60px;">
      <div class="card flex justify-content-start gap-2" style="padding-bottom: 10px;">
        <span style="line-height: 43px; font-weight: 500">News:&ensp;</span>
        <TreeSelect v-model="news_selected" selectionMode="multiple" @change="on_change_news" :options="news_urls"
          placeholder="Select News">
          <template #value="slotProps">
            <!-- {{slotProps.value}} -->
          </template>
        </TreeSelect>
        <Button icon="pi pi-plus" class="mr-2" severity="secondary" @click="add_news_url_visiable = true" />
        <Button icon="pi pi-plus" class="mr-2" severity="info" style="width: 140px" @click="get_summaries">Get
          Summaries</Button>
        <span style="line-height: 43px; font-weight: 500">Topic:&ensp;</span>
        <Select v-model="timeline_topic_selected" :options="timeline_topics" optionLabel="label"
          placeholder="Select Topic" />
        <Button icon="pi pi-plus" class="mr-2" severity="info" style="width: 140px" @click="get_topic_timeline">Get
          Topic</Button>
        <span style="line-height: 43px; font-weight: 500;width:95px">Multi view:&ensp;</span>
        <Select v-model="topic_diff_selected" :options="topics_diff" optionLabel="label" placeholder="Select Multi-view" />
        <Button icon="pi pi-plus" class="mr-2" severity="info" style="width: 140px" @click="get_topic_diff_data">Get
          Multi-view</Button>
        <Button class="mr-2" severity="info" @click="get_daily_top_news">Daily Top News</Button>

        <!-- <Button icon="pi pi-plus" class="mr-2" severity="info" style="width: 140px"
          @click="popover_timeline">Timeline</Button>
        <Popover ref="timeline_popover">
          test
        </Popover> -->
      </div>
    </div>
    <div id="chatContainer">
      <div id="chatArea" ref="chatArea">
        <div v-for="message in messages" :key="message.content">
          <ChatMessage :message="message">
            <div class="ml-4" style="padding: 10px;"
              v-if="message.type === 'timeline' && message.news_summary.length == 0">
              {{ message.content }}
            </div>
            <ChatTimeline class="ml-4" v-if="message.type === 'timeline'" :message="message" />
            <div class="flex flex-column ml-4 mb-2" v-if="message.type === 'card'">
              <h2>{{ message.content.title }}</h2>
              <div v-html="message.content.urls"></div>
            </div>
            <div v-if="message.type === 'timeline_data'" class="ml-4">
              <!-- <h2>{{ message.content.storyline_title }}</h2> -->
              <Timeline :value="message.content.items" align="left" style="width: 100%">
                <template #content="slotProps">
                  <div class="flex flex-column p-2">
                    <b>{{ slotProps.item.title }}</b>
                    <p>{{ slotProps.item.date }}</p>
                    <p>{{ slotProps.item.summary }}</p>
                    <div>
                      <a :href="slotProps.item.source" :target="slotProps.item.source">Read More</a>
                    </div>
                  </div>
                </template>
              </Timeline>
              <p v-if="message.content.background"><b>Background:</b>{{ message.content.background
                }}
              </p>
            </div>

            <div v-if="message.type === 'topic_diff'" class="flex flex-column ml-4 gap-2">
              <Card v-for="item in message?.content ?? []" align="left" style="width: 100%">
                <template #content>
                  <div class="flex flex-column p-2">
                    <!-- <b>{{ slotProps.item.title }}</b> -->
                    <h2>{{ item.domain }}</h2>
                    <!-- <p style=''>{{ item.sentiment }}</p> -->
                    <div>
                      <Tag :style="{'font-weight': 'bold', color: sentiment_color_map[item?.sentiment] ?? ''}" severity="primary" :value="item?.sentiment ?? ''" rounded></Tag>
                    </div>
                    <p>{{ item.views }}</p>
                  </div>
                </template>
              </Card>
              <p v-if="message.content.background_summary"><b>Background:</b>{{ message.content.background_summary
                }}
              </p>
            </div>
            <div v-if="message.type === 'daily_news'" class="ml-4">

              <Card v-for="e in message?.content ?? []" class="p-2 mb-2">
                <!-- <template #title>Simple Card</template> -->
                <template #content>
                  <h2>{{ e.title }}</h2>
                  <!-- <p class="mb-2 gap-1 flex"><span class="tag" v-for="d in e.domains">{{d}}</span></p> -->
                  <p>{{ e.summary }}</p>
                  <ul>
                    <li v-for="u, i in e?.cite ?? []">
                      <span class="tag">{{ e.domains[i] }}</span>
                      <a :href="u[1]" :target="u[1]">{{ u[0] }}</a>
                    </li>
                  </ul>
                </template>
              </Card>
            </div>
          </ChatMessage>
        </div>
        <div v-if="current_message">
          <ChatMessage :message="{ role: 'agent', content: current_message }" />
        </div>
        <div v-else-if="answer_loading">
          <ChatMessage :message="{ role: 'agent', content: '' }">
            <div class="flex flex-column ml-4">
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
    </div>
    <div class="flex flex-column">
      <div class="flex justfiy-content-center pl-4">
        Prompt Augmentation&nbsp;
        <ToggleSwitch v-model="use_prompt_augmentation" />
      </div>
      <div class="horizontal_scroll">
        <div style="display: flex; padding: 10px; height: 60px; width: 50vw">
          <InputText v-model="news_chat.url" class="flex-auto w-5rem mr-2" placeholder="Url" autocomplete="off" />
          <InputText v-model="news_chat.keywords" class="flex-auto  w-5rem" placeholder="Keywords" autocomplete="off" />
        </div>
        <div style="height: 60px; padding: 10px">
          <Button style="height: 40px" @click="submitChat">Submit</Button>
        </div>
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
.tag {
  border-radius: 1rem;
  padding: 0 0.5rem;
  background-color: var(--p-primary-200);
}

ul li {
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
</style>
