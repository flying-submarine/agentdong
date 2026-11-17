<script setup lang="ts">
import Popover from "primevue/popover";
import { ref } from "vue";

const confirm = ref<InstanceType<typeof Popover> | null>(null)

interface Setting {
  event?: any,
  accept?: any,
  reject?: any,
  label?: string,
  icon?: string,
}


const hide = () => {
  confirm.value?.hide()
}

const confirm_setting = ref<Setting>()
const show = (setting: Setting) => {
  confirm_setting.value = {
    accept: hide,
    reject: hide,
    label: 'Do you want to delete this record?',
    icon: 'pi pi-info-circle',
    ...setting,
  }
  confirm.value?.show(setting.event)
}

defineExpose({
  show,
  hide,
})


</script>

<template>
  <Popover ref="confirm" dismissable>
    <div class="flex flex-column gap-2">
      <p class="m-0 flex align-items-center gap-2">
        <i :class="confirm_setting?.icon" style="font-size: 2rem;color: orange"></i>
        <span>{{ confirm_setting?.label }}</span>
      </p>
      <div class="flex justify-content-end w-full gap-2">
        <Button @click="confirm_setting?.reject" severity="secondary">Cancel</Button>
        <Button @click="confirm.hide(); confirm_setting?.accept()" severity="danger">Delete</Button>
      </div>
    </div>
  </Popover>
</template>

<style scoped></style>
