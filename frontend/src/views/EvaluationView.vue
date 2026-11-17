<script setup>
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import EvaluationResult from '@/components/EvaluationResult.vue';
import Evaluation from '@/components/Evaluation.vue';

</script>

<template>
  <Tabs value="Dataset">
    <TabList>
      <Tab value="Dataset">Dataset</Tab>
      <Tab value="Result">Result</Tab>
    </TabList>
    <TabPanels>
      <TabPanel value="Dataset">
        <Evaluation />
      </TabPanel>
      <TabPanel value="Result">
        <EvaluationResult />
      </TabPanel>
    </TabPanels>
  </Tabs>
</template>
