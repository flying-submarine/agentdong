<script setup>
import DataTable from 'primevue/datatable'
import Paginator from 'primevue/paginator'
import Column from 'primevue/column'
import Select from 'primevue/select'
import Toast from 'primevue/toast';
import MultiSelect from 'primevue/multiselect'
import { useToast } from 'primevue/usetoast';
import ProgressBar from "primevue/progressbar";
import ProgressSpinner from "primevue/progressspinner";
import Panel from "primevue/panel";
import { get_local_file } from '@/service/utils'
import PopoverConfirm from './PopoverConfirm.vue';
import CryptoJS from 'crypto-js';

const toast = useToast();


import { ref, toRefs, onMounted, onBeforeUnmount, computed, watch } from 'vue';
import { EvaluationService } from '@/service/Evaluation'
import { useUserStore } from "@/stores/user";

const { user } = toRefs(useUserStore())

const confirm = ref(null)
const on_delete_dataset = (event, item) => {
  confirm.value.show({
    accept: () => EvaluationService.delete_data(item.id).then(() => { get_dataset() }),
    event,
  })
}

onMounted(() => {
  get_dataset()
});

const get_dataset = (update = false) => {
  const { page, rows, query } = dataset.value
  EvaluationService.get_data({ page, rows, query }).then(data => {
    if (data.items.length > 0 && (current_preview.value == null || update)) {
      current_preview.value = data.items[0]
      on_data_preview(0)
    }
    dataset.value.items = data.items
    dataset.value.total = data.total
  })
}

const dataset = ref({ items: [], page: 0, total: 0, rows: 5, query: {} });
const upload_flag = ref(false)
const uploading_flag = ref(false)
const upload_data = ref({ name: '', type: '', file: '', user: user.value })
const dataset_type = ref()
EvaluationService.get_data_type().then(data => (dataset_type.value = data))
const on_upload = () => {
  upload_data.value = { name: '', type: '', file: '', user: user.value }
  upload_flag.value = true
  uploading_flag.value = false
  upload_progress.value = 0
}

const select_file = async () => {
  const files = await get_local_file()
  upload_data.value.file = files[0]
  upload_data.value.name = files[0].name
}

const upload_progress = ref(0)
const upload_progress_handler = (pv) => {
  upload_progress.value = pv
}

const do_upload = () => {
  uploading_flag.value = true
  const data = { ...upload_data.value }
  data.type = data.type.name

  EvaluationService.add_data(data, upload_progress_handler).then(_ => {
    get_dataset()
    upload_flag.value = false
    uploading_flag.value = false
    upload_progress.value = 0
  }).catch(status => {
    uploading_flag.value = false
    toast.add({ severity: 'error', summary: 'upload failed', detail: status, life: 3000 });
  })
}
const change_dataset_page = (e) => {
  dataset.value.page = e.page
  dataset.value.rows = e.rows
  get_dataset()
}
const change_preview_content_page = (e) => {
  preview_content.value.page = e.page
  preview_content.value.rows = e.rows
  on_data_preview(0)
}
const current_preview = ref(null)
const on_data_preview = (item) => {
  if (item) {
    current_preview.value = item
  }
  const { page, rows } = preview_content.value
  EvaluationService.get_preview_data(current_preview.value, { page, rows }).then(data => {
    preview_content.value.items = data.items
    preview_content.value.total = data.total
  })
}
const preview_content = ref({ items: [], page: 0, total: 0, rows: 5 })

const type_filter = ref()
watch(type_filter, (v) => {
  dataset.value.query = { type: v.map(x => (x.name)) }
  get_dataset(true)
})

const translationContent = ref('')
const translationIndex = ref({ index: 0, type: '' })
const handleRightClick = (event, row) => {
  console.log(event);
  console.log(row[Object.keys(row)[3]]);
  translationIndex.value.index = row[Object.keys(row)[3]]
  translationIndex.value.type = row[Object.keys(row)[2]]
  //console.log('测试',row.data['gt']);
  if (row[Object.keys(row)[2]] === 'input') {
    translationContent.value = row.data['input']
  } else if (row[Object.keys(row)[2]] === 'gt') {
    translationContent.value = row.data['gt']
  }
  menuPosition.value.x = event.clientX;
  menuPosition.value.y = event.clientY;
  showContextMenu.value = true;
  console.log(`Right-click at pageX: ${event.pageX}, pageY: ${event.pageY}`);

  event.preventDefault();
}
const showContextMenu = ref(false);
const menuPosition = ref({ x: 0, y: 0 })
const menuRef = ref(null);
const menuStyle = computed(() => ({
  position: 'fixed',
  top: `${menuPosition.value.y}px`,
  left: `${menuPosition.value.x}px`,
}));
const closeContextMenu = () => {
  showContextMenu.value = false;
};
// 在组件挂载后添加全局的 click 监听器
onMounted(() => {
  window.addEventListener('click', closeContextMenu);
  window.addEventListener('scroll', closeContextMenu, { passive: true });
});

// 在组件卸载前移除全局的 click 监听器
onBeforeUnmount(() => {
  window.removeEventListener('click', closeContextMenu);
  window.removeEventListener('scroll', closeContextMenu);
});
const getContent = (row) => {
  if (row[Object.keys(row)[2]] === 'input') {
    return row.data['input']
  } else if (row[Object.keys(row)[2]] === 'gt') {
    return row.data['gt']
  }
}
const truncate = (q) => {
  var len = q.length;
  if (len <= 20) return q;
  return q.substring(0, 10) + len + q.substring(len - 10, len);
}
const customFunction = async () => {
  // while (preview_content.value.items[translationIndex.value.index][translationIndex.value.type].includes("(") && preview_content.value.items[translationIndex.value.index][translationIndex.value.type].includes(")")) {
  //   preview_content.value.items[translationIndex.value.index][translationIndex.value.type] = preview_content.value.items[translationIndex.value.index][translationIndex.value.type].replace(/\([^()]*\)/g, '');
  // }
    // 寻找 "\n(" 的位置
    let index = preview_content.value.items[translationIndex.value.index][translationIndex.value.type].indexOf("\n(");

    // 如果找到 "\n("，则裁剪掉这个位置及之后的内容
    if (index !== -1) {
      preview_content.value.items[translationIndex.value.index][translationIndex.value.type] = preview_content.value.items[translationIndex.value.index][translationIndex.value.type].substring(0, index);
    }
    console.log(preview_content.value.items[translationIndex.value.index][translationIndex.value.type]);
    translationContent.value = preview_content.value.items[translationIndex.value.index][translationIndex.value.type]
  let testContent = preview_content.value.items[translationIndex.value.index][translationIndex.value.type]
  // 如果 content 是字符串，进行替换操作
  //console.log(testContent);
if (typeof testContent === 'string') {
  translationContent.value =testContent
} else if (Array.isArray(testContent)) {
  // 如果 content 是数组，对每个元素执行操作或选择一个动作
  // 这里需要根据具体逻辑来处理数组情况
  // 例如，你可能想要处理数组的每一个字符串元素
  
  for (let i = 0; i < testContent.length; i++) {
    //console.log(testContent[i],'内容');
    translationContent.value +=testContent[i]
  }
}

 // console.log('翻译',translationContent.value);
  if (translationContent.value.length < 5000) {

    const appKey = import.meta.env.VITE_APP_KEY;
    const key = import.meta.env.VITE_API_KEY; // 注意：保密
    const salt = (new Date).getTime();
    const curtime = Math.round(new Date().getTime() / 1000);
    //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
    const from = 'auto';
    const to = 'zh-CHS';
    const str1 = appKey + truncate(translationContent.value) + salt + curtime + key;
    //const vocabId = '您的用户词表ID';
    const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
    let param = new URLSearchParams({
      q: translationContent.value.toString(),
      appKey: appKey,
      salt: salt.toString(),
      from: from,
      to: to,
      sign: sign,
      signType: "v3",
      curtime: curtime.toString()
    }).toString();
    try {
      const response = await fetch('/translate/api', {
        method: 'POST', // 或者 'post'
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: param
      });
      if (!response.ok) {
        const errorText = await response.text(); // 尝试读取响应文本
        throw new Error(
          `Network response was not ok. Status: ${response.status} ${response.statusText}. Body: ${errorText}`
        );
      }
      const data = await response.json();
      // console.log(data.translation[0]);
      preview_content.value.items[translationIndex.value.index][translationIndex.value.type] =
        preview_content.value.items[translationIndex.value.index][translationIndex.value.type] + "\n" + "(" + data.translation[0] + ")"
      // messageContent.value = data.translation[0]
    } catch (error) {
      console.error('Error:', error);
    }
  } else {
    // console.log(translationContent.value,'超过字数');
    //字符大于5000的时候
    const paragraphs = translationContent.value.split(/[\n\s]{2,}|\.|。(?<!\b(?:Dr|Mr|Ms|Mrs)\.)/);;
    let splicing = '';
    let newText = [];
    paragraphs.forEach(paragraph => {
      if (splicing.length + paragraph.length > 5000) {
        newText.push(splicing); // 上一段落累积内容达到长度限制，保存起来
        splicing = ''; // 重置累积内容
      }

      splicing += paragraph; // 累积新的段落内容并添加适量分隔
    });
    if (splicing.length > 0) {
      newText.push(splicing); // 添加最后一段可能未满5000字符的内容
    }
    let message = ''
    for (let i = 0; i < newText.length; i++) {
      const appKey = import.meta.env.VITE_APP_KEY;
      const key = import.meta.env.VITE_API_KEY; // 注意：保密
      const salt = (new Date).getTime();
      const curtime = Math.round(new Date().getTime() / 1000);
      //this.query = '您好，欢迎再次使用有道智云文本翻译API接口服务';
      const from = 'auto';
      const to = 'zh-CHS';
      const str1 = appKey + truncate(newText[i]) + salt + curtime + key;
      //const vocabId = '您的用户词表ID';
      const sign = CryptoJS.SHA256(str1).toString(CryptoJS.enc.Hex);
      // console.log('获取到的：',newText[i]);
      let param = new URLSearchParams({
        q: newText[i],
        appKey: appKey,
        salt: salt.toString(),
        from: from,
        to: to,
        sign: sign,
        signType: "v3",
        curtime: curtime.toString()
      }).toString();
      try {
        const response = await fetch('/translate/api', {
          method: 'POST', // 或者 'post'
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: param
        });
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        message += data.translation[0]
        //  console.log(data.translation[0]);
      } catch (error) {
        console.error('Error:', error);
      }
    }
    preview_content.value.items[translationIndex.value.index][translationIndex.value.type] =
      preview_content.value.items[translationIndex.value.index][translationIndex.value.type] + "\n" + "(" + message + ")"

  }
}
</script>

<template>
  <div class="flex flex-column pt-5">
    <PopoverConfirm ref="confirm" />
    <div class="flex gap-2">
      <Button icon="pi pi-upload" label="Upload" rounded @click="on_upload" />
      <MultiSelect v-model="type_filter" :options="dataset_type" optionLabel="name" placeholder="Select Type" />
    </div>
    <DataTable class="compact-table" size="mini" :value="dataset.items" tableStyle="min-width: 50rem">
      <template #empty> No customers found. </template>
      <template #loading> Loading customers data. Please wait. </template>
      <Column field="name" header="Name"></Column>
      <Column field="type" header="Type">
        <template #body="{ data }">
          {{ data.type }}
        </template>
      </Column>
      <Column field="time" header="Time"></Column>
      <Column>
        <template #body="{ data, index }">
          <div class="flex gap-2">
            <Button @click="on_delete_dataset($event, data)" rounded style="color: red;" icon="pi pi-trash" text
              size="small" />
            <Button @click="on_data_preview(data)" rounded v-tooltip.top="'detail'" icon="pi pi-align-center" text
              size="small" />
          </div>
        </template>
      </Column>
      <template #footer>
        <Paginator :totalRecords="dataset.total" @page="change_dataset_page" :rows="dataset.rows"
          :rowsPerPageOptions="[5, 10, 20, 50]">
          <template #start>
            <Button @click="get_dataset()" rounded type="button" icon="pi pi-refresh" text />
          </template>
          <template #end>
            {{ `Total: ${dataset.total}` }}
          </template>
        </Paginator>
      </template>
    </DataTable>
    <Toast />
    <Dialog v-model:visible="upload_flag" modal header="Add Dataset" :style="{ width: '25rem' }" :closeOnEscape="false">
      <div class="flex flex-column gap-2">
        <div class="flex align-items-center gap-4">
          <label class="font-semibold w-24">Name</label>
          <InputText :disabled="uploading_flag" v-model="upload_data.name" class="flex-auto" autocomplete="off" />
          <div>
            <Button v-show="!uploading_flag" @click="select_file" text icon="pi pi-upload" />
            <ProgressSpinner v-show="uploading_flag" fill="transparent" style="width: 30px; height: 30px" />
          </div>
        </div>
        <ProgressBar v-show="uploading_flag" :value="upload_progress" :showValue="false" style="height: 6px;" />
        <div v-show="!uploading_flag" style="height: 6px;" />
        <div class="flex align-items-center gap-5">
          <label class="font-semibold w-24">Type</label>
          <Select :disabled="uploading_flag" v-model="upload_data.type" :options="dataset_type" optionLabel="name"
            placeholder="Select Type" class="flex-auto" />
        </div>
        <div class="flex justify-end gap-2">
          <Button type="button" label="Cancel" :disabled="uploading_flag" severity="secondary"
            @click="upload_flag = false"></Button>
          <Button type="button" label="Save" :disabled="uploading_flag" @click="do_upload"></Button>
        </div>
      </div>
    </Dialog>
  </div>

  <Panel header="Data Preview">
    <DataTable class="compact-table" :value="preview_content.items" tableStyle="min-width: 50rem">
      <template #empty> No customers found. </template>
      <template #loading> Loading customers data. Please wait. </template>
      <template #header>
        <div class="flex align-items-center justify-content-between">
          <div class="flex flex-column">
            <span><b>Name:</b> {{ current_preview?.name }}</span>
            <span><b>Type:&ensp;</b> {{ current_preview?.type }}</span>
          </div>
          <span>Total: {{ preview_content.total }}</span>
        </div>
      </template>
      <Column field="id" header="#"></Column>
      <Column field="input" header="Input">
        <template v-slot:body="slotProps">
          <div @contextmenu.prevent="handleRightClick($event, slotProps)" class="pre-wrap">
            {{ getContent(slotProps) }}
          </div>
        </template>
      </Column>
      <Column field="gt" header="GT">
        <template v-slot:body="slotProps">
          <div @contextmenu.prevent="handleRightClick($event, slotProps)" class="pre-wrap">
            {{ getContent(slotProps) }}
          </div>
        </template>
      </Column>
      <template #footer>
        <Paginator :totalRecords="preview_content.total" :rows="preview_content.rows" @page="change_preview_content_page"
          :rowsPerPageOptions="[5, 10, 20, 50]" />
      </template>
      <!-- 自定义右键菜单，使用v-if或者v-show来控制显示和隐藏 -->
      <div v-if="showContextMenu" :style="menuStyle" class="custom-context-menu">
        <ul>
          <li @click="customFunction">翻译</li>
        </ul>
      </div>
    </DataTable>
  </Panel>
</template>

<style scoped>
.custom-context-menu {
  /* 自定义菜单的样式 */
  width: 200px;
  z-index: 10;
}

.custom-context-menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
  background-color: #fff;
  border: 1px solid #ccc;
  /* 更多样式 ... */
}

.custom-context-menu li {
  padding: 8px 12px;
  cursor: pointer;
  /* 更多样式 ... */
}

.custom-context-menu li:hover {
  background-color: #f0f0f0;
}
.pre-wrap {
  white-space: pre-wrap;
}
</style>
