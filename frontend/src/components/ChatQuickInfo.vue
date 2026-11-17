<script setup lang="ts">
import Timeline from "primevue/timeline";
import { Message } from "@/service/ChatClient";
import { ref, reactive, nextTick } from "vue"
import CryptoJS from 'crypto-js';
import MarkdownIt from "markdown-it";
interface Props {
  message: Message;
}
const markdown = new MarkdownIt();
const props = defineProps<Props>();
const initSummaryData = (summaries) => {
  return summaries.map((summary) => ({
    ...summary,
    popoverVisible: false,
    translateContent: '',
  }));
};

// 然后在你的组件中创建一个新的响应式属性：
const newsSummaries = reactive(props.message.news_summary.map(summary => ({
  ...summary,
  popoverVisible: false,
  translateContent: ''
})));
console.log(newsSummaries, 'newsSummaries');
const read_more = (item) => {
  console.log(item);
};
function escapeMarkdownSpecialChars(text) {
  return text.replace(/([*_\\])/g, "\\$1");
}
const popoverVisible = ref(false)
const translateContent = ref('')
const translate = async (summary) => {
  console.log('翻译', summary.popoverVisible);
  // let index = newsSummaries.value.findIndex(s => s === summary);
  // console.log('索引值',index);

  summary.popoverVisible = !summary.popoverVisible;
  // let content = "**"+summary.title+"**"+'\n'+summary.summary
  let escapedTitle = escapeMarkdownSpecialChars(summary.title);
  let escapedSummary = escapeMarkdownSpecialChars(summary.summary);
  let content = `${escapedTitle}\n\n${escapedSummary}`;
  console.log(content);

  if (summary.popoverVisible) {
    if (content.length < 5000) {
      const appKey = import.meta.env.VITE_APP_KEY;
      const key = import.meta.env.VITE_API_KEY; // 注意：保密
      const salt = (new Date).getTime();
      const curtime = Math.round(new Date().getTime() / 1000);
      //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
      const from = 'auto';
      const to = 'zh-CHS';
      const str1 = appKey + truncate(content) + salt + curtime + key;
      //const vocabId = '您的用户词表ID';
      const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
      let param = new URLSearchParams({
        q: content,
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
        // 找到项目的索引
        let index = newsSummaries.findIndex(s => s === summary);
        console.log('索引值', index);

        // 只有在找到项时才继续
        if (index !== -1) {
          let strContent = data.translation[0].split('\n\n');
          newsSummaries[index].translateContent = "**" + strContent[0] + "**" + "\n\n" + strContent[1];
          console.log('所有值', newsSummaries[index].translateContent);
          await nextTick();

        }
        //summary.translateContent = data.translation[0]
      } catch (error) {
        console.error('Error:', error);
      }
    } else {
      console.log('长文本操作');

      //字符大于5000的时候
      const paragraphs = content.split(/[\n\s]{2,}|\.|。(?<!\b(?:Dr|Mr|Ms|Mrs)\.)/);;
      let splicing = '';
      let newText = [];
      paragraphs.forEach(paragraph => {
        if (splicing.length + paragraph.length > 5000) {
          newText.push(splicing); // 上一段落累积内容达到长度限制，保存起来
          splicing = ''; // 重置累积内容
        }
        console.log(paragraph);

        splicing += paragraph; // 累积新的段落内容并添加适量分隔
      });
      if (splicing.length > 0) {
        newText.push(splicing); // 添加最后一段可能未满5000字符的内容
      }
      let message = ''
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
          message += data.translation[0]
        } catch (error) {
          console.error('Error:', error);
        }
      }
      // 找到项目的索引
      let index = newsSummaries.findIndex(s => s === summary);
      console.log('索引值', index);

      // 只有在找到项时才继续
      if (index !== -1) {
        let strContent = message.split('\n\n');
        newsSummaries[index].translateContent = "**" + strContent[0] + "**" + "\n\n" + strContent[1];
        // console.log('所有值',newsSummaries);
        await nextTick();

      }
    }
  }
}
const truncate = (q) => {
  var len = q.length;
  if (len <= 20) return q;
  return q.substring(0, 10) + len + q.substring(len - 10, len);
}

const show_timeline_flag = ref(false)
const show_timeline_data = ref()
const init_show_timeline_data = () => {
  show_timeline_data.value = { storyline_title: 'Loading Please Wait...', context_news_relevance: [], background_summary: '' }
}
init_show_timeline_data()
const show_timeline = async (item) => {
  show_timeline_flag.value = true
  init_show_timeline_data()
  const data = {
    url: item.url,
    title: item.title,
  }
  const data_mock = {
    url: 'https://edition.cnn.com/2024/03/23/world/britain-pompeii-science-newsletter-wt-scn/index.html',
    title: 'An ancient dinner still sits in a Bronze Age village 2,850 years later',
  }
  const response = await fetch(`/news/get_events`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  })

  const res = await response.json()
  // const res2 = [
  //   { id: 'x', title: 'title1', publication_date: '2024-03-28', url: 'http://xx', summary: 'summary' },
  //   { id: 'x', title: 'title2', publication_date: '2024-03-28', url: 'http://xx', summary: 'summary' },
  //   { id: 'x', title: 'title3', publication_date: '2024-03-28', url: 'http://xx', summary: 'summary' },
  // ]
  // const res2 = "{\n  \"storyline_title\": \"SAB and UnionPay's Strategic Alliance Boosts Saudi Digital Payments\",\n  \"context_news_relevance\": [\n    {\n      \"id\": 0,\n      \"date\": \"2024-07-16\",\n      \"related\": true,\n      \"summary\": \"SAB and UnionPay collaboration to expand digital payment solutions in Saudi Arabia, supporting Vision 2030.\",\n      \"url\": \"https://saudigazette.com.sa/article/644238/BUSINESS/Strategic-partnership-between-Saudi-Awwal-Bank-and-UnionPay-International-fuels-Saudi-Vision-2030-tourism-drive\"\n    }\n  ],\n  \"background_summary\": \"In a significant move to modernize Saudi Arabia's payment landscape, Saudi Awwal Bank (SAB) has joined forces with UnionPay [2024-07-16]. This partnership aims to enhance the country's digital payment infrastructure, increasing UnionPay's merchant coverage and enabling UPI payment acceptance across various platforms. The collaboration is in line with Saudi Arabia's Vision 2030, which seeks to promote a cashless society and boost the tourism sector by improving payment convenience for both locals and visitors.\"\n}"
  // const res = JSON.parse(res2)
  try {
    show_timeline_data.value = JSON.parse(res)
  } catch (e) {
    console.error(e)
  }
}

const get_domain = (url) => {
  const pattern = /^(?:https?:\/\/)?(?:www\.)?([^\/\?]+)/i;
  return (url ?? "").match(pattern)[1] ?? ''
}
</script>

<template>
  <div>
    <Dialog v-model:visible="show_timeline_flag" modal :draggable="false" header="Timeline" :style="{ width: '70rem' }">
      <h2>{{ show_timeline_data.storyline_title }}</h2>
      <Timeline :value="show_timeline_data.context_news_relevance" align="left" style="width: 100%">
        <template #content="slotProps">
          <div class="flex flex-column p-2">
            <!-- <b>{{ slotProps.item.title }}</b> -->
            <p>{{ slotProps.item.date }}</p>
            <p>{{ slotProps.item.summary }}</p>
            <div>
              <a :href="slotProps.item.url" :target="slotProps.item.url">Read More</a>
            </div>
          </div>
        </template>
      </Timeline>
      <p v-if="show_timeline_data.background_summary"><b>Background:</b>{{ show_timeline_data.background_summary }}</p>
    </Dialog>
    <Card class="quick-card" style="position: relative;" v-for="newsummary in newsSummaries" :key="newsummary.summary">
      <template #title>
        {{ newsummary.title }}
        <el-popover placement="left" trigger="manual" :visible="newsummary.popoverVisible" width="450">
          <!-- <template #reference>
            <el-button class="translate-button" type="primary"
              @click="() => translate(newsummary)">翻译</el-button>
          </template> -->
          <div style="max-height: 100px; overflow: auto;">
            <div class="markdown-body" v-html="markdown.render(newsummary.translateContent)" />
          </div>
        </el-popover>
      </template>
      <template #subtitle>
        {{ newsummary.publication_date }}
      </template>
      <template #content>
        <p>
          {{ newsummary.summary }}
          <a class="more" :href="newsummary.url" :target="newsummary.url">Read More</a>
        </p>
        <!-- <Button label="Read more" text @click="read_more(slotProps.item)"></Button> -->
        <div class="flex gap-2 source-site">
          <!-- <a class="more" :href="newsummary.url" :target="newsummary.url">Read More</a> -->
          <!-- <a class="pointer" @click.stop="show_timeline(slotProps.item)">Timeline</a> -->
          Sources: {{get_domain(newsummary.site)}}
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.pointer:hover {
  cursor: pointer;
}
.source-site {
  font-weight: 500;
  font-style: italic;
}
.quick-card {
  background-color: #F0F3FC;
  border-radius: 3px;
  margin-top: 14px;
  &:first-child {
    margin-top: 0;
  }
}
:deep(.p-timeline-event-opposite) {
  display: none !important;
}

.time_line {
  position: relative;
}

.translate-button {
  position: absolute !important;
  /* 绝对定位 */
  bottom: 10px;
  /* 距离顶部的距离 */
  right: 0px;
  /* 距离右侧的距离 */
  z-index: 10;
  /* 确保按钮在最上层 */
}

.markdown-body {
  box-sizing: border-box;
  min-width: 200px;
  max-width: 980px;
  margin: 0 1rem;
  padding: 15px;
  background-color: inherit;
  white-space: pre-wrap;
  /* 保留空白符，自动换行 */
}

.more {
    font-size: 12px;
    color: #578BF7;
    &:hover {
      background: transparent;
    }
  }

@media (max-width: 767px) {
  .markdown-body {
    padding: 5px;
  }
}
</style>
