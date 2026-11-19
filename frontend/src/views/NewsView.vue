<script setup>
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";

import News from "@/components/News.vue";
import NewsChatBox from "@/components/NewsChatBox.vue";


</script>

<template>
  <Splitter class="news-box" :gutterSize="0">
    <SplitterPanel :size="60" class="news-left">
      <News />
    </SplitterPanel>
    <SplitterPanel :size="40" class="news-right">
      <NewsChatBox />
    </SplitterPanel>
  </Splitter>
</template>

<style>
 .news-box {
  width: 100%;
  height: calc(100vh - 100px);
  background: var(--app-bg) !important;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  overflow: hidden;
  box-shadow: var(--app-shadow-sm);
}
.news-box .p-splitter-gutter { background: var(--app-border); width: 1px; }
.news-left, .news-right { background: var(--app-surface); min-width: 0; }

</style>
