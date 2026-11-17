<template>
  <div>
    <!-- <textarea ref="codemirrorElement" style="display: none;"></textarea>  -->
    <div class="markdown-body" ref="codemirrorContainer" ></div> <!-- 容器 -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick, defineExpose } from 'vue';
import CodeMirror from 'codemirror';
import 'codemirror/lib/codemirror.css';
import 'codemirror/mode/markdown/markdown';
import 'codemirror/addon/edit/continuelist';
import 'codemirror/addon/display/fullscreen';
import 'codemirror/addon/display/placeholder';
import EventBus from '@/service/eventBus'
import { el } from 'element-plus/es/locale';
interface Props {
  source: string;
}

const props = defineProps<Props>();
const emit = defineEmits(['update:source']);
let hasValidSelection = false;
// use <div> as a container
const codemirrorContainer = ref<HTMLDivElement | null>(null);
const codemirrorElement = ref<HTMLTextAreaElement | null>(null);
const editor = ref<CodeMirror.Editor | null>(null);
let marker = ref<CodeMirror.TextMarker | null>(null); // 用来保存高亮选中的内容
  onMounted(() => {
  initializeEditor(props.source);
  EventBus.$on('parent-scroll', onParentScroll);
});
const initializeEditor = async (value) => {
  await nextTick();
  if (codemirrorContainer.value) {
    editor.value = CodeMirror(codemirrorContainer.value, {
      value: value,
      mode: 'markdown',
      lineNumbers: false,
      placeholder: 'Write your markdown here...',
      lineWrapping: true,
      extraKeys: { Enter: 'newlineAndIndentContinueMarkdownList' },
      fullScreen: false,
    });
    editor.value.on('change', () => {
      const value = editor.value?.getValue();
      if (value !== undefined) {
        emit('update:source', value);
      }
    });
  } else {
    console.error('codemirrorContainer is not available');
  }
};
const parentScroll = ref(0)
// 监听 parentScroll 的变化，并执行相应的逻辑
watch(parentScroll, (newVal, oldVal) => {
  console.log('Parent scroll position changed from ', oldVal, ' to ', newVal);
  // 在这里执行你需要的逻辑
  doSomethingWithScrollPosition(newVal);
});
// 定义你的处理逻辑
const doSomethingWithScrollPosition = (scrollTop) => {
  // 在这里处理 scrollTop 值变化后的逻辑
  // 比如：重新赋值或者其他逻辑
  console.log('变化值',scrollTop);
  let scrollInfo = editor.value.getScrollInfo();
  parentScroll.value = scrollTop
  editor.value.scrollTo(scrollInfo.left, parentScroll.value);
};
onBeforeUnmount(() => {
  EventBus.$off('parent-scroll', onParentScroll);
  if (editor.value) {

    editor.value.toTextArea ? editor.value.toTextArea() : editor.value = null;
    editor.value = null;
  }
});

const onParentScroll = (scrollTop) => {
      // console.log('Parent scroll position:', scrollTop);
      if(!flag.value){
        parentScroll.value = scrollTop
      }
      // Do something with the scroll position
    };
const reinitializeEditor = async (newValue) => {
  if (editor.value) {
    // 保存光标位置和滚动位置
    const scrollInfo = editor.value.getScrollInfo();
    const cursor = editor.value.getCursor();
    
  if(flag.value){
    editor.value.toTextArea?.(); // 尽量用?.，确保如果方法不存在不会报错
    editor.value.getWrapperElement().remove(); // 完全删除编辑器的DOM

    // 重新初始化
    await initializeEditor(newValue);
   }else{
    editor.value.setValue(newValue);
   }
    
  // 恢复光标位置和滚动位置
  if (editor.value && flag.value) {
      console.log('恢复位置',parentScroll.value);
      flag.value = false
      editor.value.setCursor(cursor);
      editor.value.scrollTo(scrollInfo.left, parentScroll.value);
    }
  } else {
    await initializeEditor(newValue);
  }
};
watch(() => props.source, async(newValue) => {
  if (editor.value && editor.value.getValue()!=newValue) {
     console.log('开始执行',newValue);
    // 重新初始化编辑器
    await reinitializeEditor(newValue);
  }
});

const getSelectedText = () => {
  
  
  if (editor.value) {
    const selection = editor.value.getSelection();
    return selection;
  }
  return '';
};
const removeLight = ()=>{
  if (marker.value) {
    document.getSelection().removeAllRanges(); // 清除选中范围
        marker.value.clear(); // 清除之前的高亮
      }
      if (editor.value) {
    // 获取编辑器的文档对象
    const doc = editor.value.getDoc();
    // 获取当前光标位置
    const cursor = doc.getCursor();
    // 清除选中范围
    doc.setSelection(cursor, cursor);
  }
}
// 高亮选中内容
const highlightSelection = () => {
  if (editor.value) {
    console.log('进来条用');
    
    const selection = editor.value.getSelection();
    console.log(selection);
    
    if (selection.length>1) {
      const from = editor.value.getCursor("from");
      const to = editor.value.getCursor("to");
      if (marker.value) {
        marker.value.clear(); // 清除之前的高亮
      }
      console.log('执行');
      
      marker.value = editor.value.markText(from, to, { className: 'highlighted-selection' });
      hasValidSelection = true;
    }else{
      if (marker.value) {
        marker.value.clear(); // 清除之前的高亮
      }
    }
  }
};
const flag = ref(false)
// 获取选中内容的位置
const getSelectedTextPosition = () => {
  if (editor.value) {
    const from = editor.value.getCursor("from");
    const to = editor.value.getCursor("to");
    return { from, to };
  }
  return { from: null, to: null };
};

// 替换选中内容
const replaceSelectedText = (replacementText) => {
  if (editor.value) {
    const { from, to } = getSelectedTextPosition();
    if (from !== null && to !== null) {
      editor.value.replaceRange(replacementText, from, to);
      const newValue = editor.value.getValue();
      flag.value = true
      return newValue;
    }
  }
  return null;
};

defineExpose({
  getSelectedText,
  highlightSelection,
  getSelectedTextPosition,
  replaceSelectedText,
  removeLight,
});
</script>
<style scoped>
/* 高亮选中的内容 */
.markdown-body >>> .highlighted-selection {
  background-color: #3399FF !important;
  color: black !important; 
}
.markdown-body {
  box-sizing: border-box !important;
  min-width: 200px !important;
  max-width: 980px !important;
  /* margin: 0 1rem; */
  padding: 15px !important;
  white-space: pre-wrap !important;
  /* white-space: wrap; */
  /* 保留空白符，自动换行 */
}

/* 覆盖 CodeMirror 样式 */
.markdown-body >>> .CodeMirror {
  background-color: inherit !important;
  height: auto;
  overflow: hidden;
}

.markdown-body >>> .CodeMirror-scroll {
  overflow: hidden !important;
}
@media (max-width: 767px) {
  .markdown-body {
    padding: 5px !important;
  }
}
</style>
<!-- <style>
.CodeMirror{
  background-color: inherit !important;
}
</style> -->

