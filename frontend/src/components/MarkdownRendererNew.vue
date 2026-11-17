<script setup lang="ts">
import MarkdownIt from "markdown-it";
import markdownItMark from "markdown-it-mark";
import { ref, watch } from 'vue';
interface Props {
  source: string;
  isPhrase?: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits({
  enterMessage: (value:string) => {}
});

const markdown = new MarkdownIt().use(markdownItMark);
const renderedMarkdown = ref(markdown.render(props.source||''));
const getRenderedHTML = () => renderedMarkdown.value;
const container = ref(null);
watch(() => props.source, (newSource) => {
  // if(props.isPhrase) {
  //   newSource = newSource+'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;>'
  // }
  try {
  renderedMarkdown.value = newSource ? markdown.render(newSource) : '';
  } catch (error) {
    console.error('Error rendering Markdown:', newSource);
  }
}, { immediate: true });
// 暴露方法以便父组件访问
defineExpose({
  getContainer: () => {
    return container.value;
  },
  getRenderedHTML, // 新增此行
});

const emitMessge = ()=>{
  if(props.isPhrase) {
    emit('enterMessage',props.source)
  }
}

</script>

<template>
  <div ref="container" :style="props.isPhrase?'cursor: pointer':''" class="markdown-body" dir="auto" v-html="renderedMarkdown" @click="emitMessge"/>
</template>

<style scoped>
.markdown-body {
  box-sizing: border-box;
  /* min-width: 200px; */
  max-width: 980px;
  /* margin: 0 1rem; */
  padding: 4px 15px;
  background-color: inherit;
  /* white-space: pre-wrap; */
  overflow-wrap: break-word;
  font-size: 12px;
  /* white-space: wrap; */
  /* 保留空白符，自动换行 */
  &::v-deep p {
    margin-bottom: 16px;
  }
}

.markdown-body ::v-deep mark {
  background-color: #3399FF !important;
}

@media (max-width: 767px) {
  .markdown-body {
    padding: 5px;
  }
}
</style>
