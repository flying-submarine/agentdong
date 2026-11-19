<script setup>
import RagChat from '@/components/RagChat.vue'
import RagHistory from '@/components/RagHistory.vue'
import { ref } from "vue";

const selectedEntry = ref(null);
const updateSelectedEntry = (entry) => {
  selectedEntry.value = entry;
};
</script>

<template>
  <div class="rag-page">
    <aside class="rag-sidebar">
      <RagHistory :entry="selectedEntry" />
    </aside>
    <section class="rag-content">
      <RagChat :onEntrySelect="updateSelectedEntry" />
    </section>
  </div>
</template>

<style scoped>
.rag-page {
  display: flex;
  gap: 16px;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.rag-sidebar {
  width: 240px;
  flex: 0 0 240px;
  min-height: 0;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  box-shadow: var(--app-shadow-sm);
  overflow: hidden;
  display: flex;
}

.rag-content {
  flex: 1;
  min-width: 0;
  min-height: 0;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  box-shadow: var(--app-shadow-sm);
  overflow: hidden;
  display: flex;
}

@media (max-width: 960px) {
  .rag-page {
    flex-direction: column;
  }
  .rag-sidebar {
    width: 100%;
    flex: 0 0 auto;
    max-height: 240px;
  }
}
</style>
