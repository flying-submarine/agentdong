<script setup>
import Chat from '@/components/Chat.vue'
import ChatHistory from '@/components/ChatHistory.vue'

import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
</script>

<template>
  <Splitter style="width: 100%;" :gutterSize="0">
    <SplitterPanel style="max-width: 200px; min-width: 200px;">
      <ChatHistory />
    </SplitterPanel>
    <SplitterPanel>
      <Chat />
    </SplitterPanel>
  </Splitter>
</template>
