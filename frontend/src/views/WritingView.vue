<script setup>
import Writing from '@/components/Writing.vue'
import WritingHistory from '@/components/WritingHistory.vue'

import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import { ref, toRefs } from "vue";

// 假设我们需要传递一个选择的历史条目来实现此功能
const selectedEntry = ref(null);

// 更新选择的条目的方法
const updateSelectedEntry = (entry) => {
  selectedEntry.value = entry;
};

</script>

<template>
  <Splitter style="width: 100%;" :gutterSize="0" >
    <SplitterPanel style="max-width: 200px; min-width: 200px;">
      <WritingHistory :entry="selectedEntry" />
    </SplitterPanel>
    <SplitterPanel>
      <Writing :onEntrySelect="updateSelectedEntry"/>
    </SplitterPanel>
  </Splitter>
</template>