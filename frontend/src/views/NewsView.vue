<script setup>
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import News from "@/components/News.vue";
import NewsChatBox from "@/components/NewsChatBox.vue";


</script>

<template>
  <Splitter  class="news-box" :gutterSize="0">
    <SplitterPanel :size="60" style="min-width: 594px;border-top-left-radius: 5px;border-bottom-left-radius: 5px;box-shadow: 0 0 5px 2px rgba(87,79,215,0.10);">
      <News />
    </SplitterPanel>
    <SplitterPanel :size="40" style="background: #fff;border-top-right-radius: 5px;border-bottom-right-radius: 5px;">
      <NewsChatBox />
    </SplitterPanel>
  </Splitter>
</template>

<style>
 .news-box {
  width: 100%;
  height: calc(100vh - 94px);
  background: transparent !important;
  .p-splitter-gutter {
    background: transparent;
  }
 }

</style>
