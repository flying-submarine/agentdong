<template>
<div>
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
</div>
</template>

<script setup lang="ts">

interface IMessage {
  content: String;
  type: String;
}

const props = defineProps({
  messages: Array<IMessage>,
  current_message: String,
  answer_loading: Boolean
});


</script>