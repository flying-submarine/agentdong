<template>
  <Dialog
    :visible="props.visible"
    modal
    header="拉取模型"
    :style="{ width: '32rem' }"
    @update:visible="onVisibleChange"
  >
    <div class="flex flex-column gap-2">
      <label for="pull-model-name">模型名称</label>
      <InputText id="pull-model-name" v-model="modelName" placeholder="例如 llama3" />
    </div>
    <template #footer>
      <Button label="取消" severity="secondary" text @click="emit('cancel')" />
      <Button label="拉取" @click="onCreate" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits(['create', 'cancel'])

const modelName = ref('')

const onCreate = () => {
  if (modelName.value.trim()) {
    emit('create', modelName.value.trim())
  }
}

const onVisibleChange = (val: boolean) => {
  if (!val) emit('cancel')
}
</script>
