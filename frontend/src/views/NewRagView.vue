<script setup>
import RagChat from '@/components/RagChat.vue'
import RagHistory from '@/components/RagHistory.vue'

import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import { ref } from "vue";

const selectedEntry = ref(null);

const updateSelectedEntry = (entry) => {
  selectedEntry.value = entry;
};
</script>

<template>
  <Splitter style="width: 100%;background: transparent;" class="rag_page" :gutterSize="25">
    <SplitterPanel 
      style="max-width: 220px; 
      min-width: 220px;
      box-shadow: 0 0 5px 2px rgba(87,79,215,0.10);
      background-image: linear-gradient(160deg, #FEFFFF 0%, rgba(245,248,255,0.90) 100%);">
      <RagHistory :entry="selectedEntry" />
    </SplitterPanel>
    <SplitterPanel class="ragContent">
      <RagChat :onEntrySelect="updateSelectedEntry"/>
    </SplitterPanel>
  </Splitter>
</template>

<style>

  .rag_page {
    height: calc(100vh - 94px);
  }

  .rag_page .p-splitterpanel {
    border-radius: 5px;
  }

  .rag_page > div:nth-child(2){
    background: #D9D4FC;;
  }
  .ragContent {
    background-image: url('@/assets/IconRagContent.png'); /* 使用@作为绝对路径的起点 */
    box-shadow: 0 0 5px 2px rgba(87,79,215,0.10);
    border-radius: 5px;
    background-color: #fff;
  }
 
</style>
