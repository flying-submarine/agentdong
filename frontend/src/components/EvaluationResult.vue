<script setup>
import DataTable from 'primevue/datatable'
import Paginator from 'primevue/paginator'
import Column from 'primevue/column'
import Select from 'primevue/select'
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import MultiSelect from 'primevue/multiselect';
import Panel from "primevue/panel";
import CryptoJS from 'crypto-js';
import PopoverConfirm from './PopoverConfirm.vue';
import IconField from 'primevue/iconfield'
import Echarts from './Echarts.vue'
import { ref, toRefs, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue';
import { EvaluationService } from '@/service/Evaluation.ts'
import { useUserStore } from "@/stores/user";
const { user } = toRefs(useUserStore())

onMounted(() => {
  get_result()
  get_dataset()
});

const confirm = ref(null)
const on_delete_result = (event, item) => {
  confirm.value.show({
    accept: () => EvaluationService.delete_evaluation_result(item.ID, item.Type).then(get_result),
    event,
  })
}


const dataset = ref({ items: [] })
const dataset_selected = ref([])
const get_dataset = () => {
  dataset.value = { items: [] }
  let query = {}
  const type = dataset_type_selected.value
  if (type && type.name != 'Any') {
    query = { type: type.name }
  }
  EvaluationService.get_data({ page: 0, rows: 100, query }).then(data => {
    dataset.value.items = data.items;
  })
}


const on_add_evaluation = () => {
  if (dataset_selected.value.length == 0) {
    return
  }
  do_add_evaluation()
}

const do_add_evaluation = () => {
  const selected = dataset_selected.value.map(x => ({ id: x.id, type: x.type }))
  const data = {
    id: selected.length > 0 ? selected[0].id : undefined,
    type: selected.length > 0 ? selected[0].type : undefined,
    user: user.value,
    promptAug: promptFlag.value,
  }
  EvaluationService.add_evaluation(data).then(x => {
    get_result()
  })
}

const get_result = (change_preview_force = false) => {
  const { page, rows } = result.value
  let query = {}
  const type = dataset_type_selected.value
  query = { taskType: type?.name ?? '' }
  query.search = search.value
  query.sort = result_sort.value
  EvaluationService.get_result({ query, page, rows }).then(data => {
    if (data.items.length > 0 && (!current_preview.value || change_preview_force)) {
      on_result_preview(data.items[0])
    }
    result.value.items = data.items
    result.value.total = data.total
    result.value.columns = data.columns
    column_options.value = data.columns.length > 0 ? data.columns.map(x => ({ label: x })) : []
  })
}

const result = ref({ items: [], page: 0, total: 0, rows: 5 });

const change_result_page = (e) => {
  result.value.page = e.page
  result.value.rows = e.rows
  get_result()
}
const change_preview_content_page = (e) => {
  preview_content.value.page = e.page
  preview_content.value.rows = e.rows
  on_result_preview(0)
}
const current_preview = ref(null)
const on_result_preview = (item) => {
  if (item) {
    current_preview.value = item
    init_preview_content()
  }
  const { page, rows } = preview_content.value
  EvaluationService.get_preview_result({ query: current_preview.value, page, rows }).then(data => {
    preview_content.value.items = data.items
    preview_content.value.total = data.total
    preview_content.value.columns = data.columns
  })
}
const preview_content = ref()
const init_preview_content = (columns = []) => {
  preview_content.value = { items: [], page: 0, total: 0, rows: 5, columns }
}

init_preview_content()

const dataset_type_selected = ref({ name: 'News' })
const dataset_type_options = ref()
EvaluationService.get_data_type().then(data => (dataset_type_options.value = data))
const task_type_change = () => {
  dataset_selected.value = []
  init_preview_content()
  get_result(true)
  get_dataset()
  reset_search()
}

const translationContent = ref('')
const translationIndex = ref({ index: 0, type: '' })
const handleRightClick = (event, row) => {
  console.log(event);
  console.log(row[Object.keys(row)[3]]);
  translationIndex.value.index = row[Object.keys(row)[3]]
  translationIndex.value.type = row[Object.keys(row)[2]]
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
  const key = row[Object.keys(row)[2]];
  return row.data[key];
}
const truncate = (q) => {
  var len = q.length;
  if (len <= 20) return q;
  return q.substring(0, 10) + len + q.substring(len - 10, len);
}

const ceshi = (row) => {
  let content = row
  function removeEnclosingBrackets(text) {
    // 匹配含有连续中文字符的字符串
    const chineseRegex = /[\u4e00-\u9fa5]+/g;
    let match;

    while ((match = chineseRegex.exec(text)) !== null) {
      // 获取中文字符串的起始和终止索引
      let leftIndex = match.index;
      let rightIndex = chineseRegex.lastIndex - 1;
      let balance = 0;

      // 向左寻找最外层左括号
      // 向左寻找最外层左括号
      while (leftIndex >= 0) {
        if (balance == 0 && text[leftIndex] == '(') {
          leftIndex--;
          balance++;
        } else if (balance == 0 && text[leftIndex] != '(') {
          leftIndex--;
        } else if (balance > 0 && text[leftIndex] == '(') {
          leftIndex--;
          balance++;
        } else if (balance > 0 && text[leftIndex] != '(') {
          break
        }

      }
      console.log(text.substring(0, leftIndex), 1);
      // 向右寻找最外层右括号
      balance = 0;
      while (rightIndex < text.length) {
        if (balance == 0 && text[rightIndex] == ')') {
          rightIndex++;
          balance++;
        } else if (balance == 0 && text[rightIndex] != ')') {
          rightIndex++;
        } else if (balance > 0 && text[rightIndex] == ')') {
          rightIndex++;
          balance++;
        } else if (balance > 0 && text[rightIndex] != ')') {
          break
        }
      }
      console.log(text.substring(rightIndex + 1), 2);
      console.log(text.length, rightIndex, '长度');
      // 如果找到了匹配的最外层括号，移除这对括号和它们之间的内容
      if (leftIndex >= 0 && rightIndex <= text.length) {
        text = text.substring(0, leftIndex) + text.substring(rightIndex + 1);
        console.log(text, 3);
        chineseRegex.lastIndex = leftIndex; // 更新后续查找的起始位置
      } else {
        break; // 如果没有匹配的括号，结束循环
      }
    }
    return text;
  }

  // 移除包含中文字符的最外层括号和该括号内的内容
  content = removeEnclosingBrackets(content);

  // 移除末尾的换行符
  content = content.replace(/\n+$/, '');

  // 更新原始数据结构
  return content;
}
const customFunction = async () => {
  // while (preview_content.value.items[translationIndex.value.index][translationIndex.value.type].includes("(") && preview_content.value.items[translationIndex.value.index][translationIndex.value.type].includes(")")) {
  //   preview_content.value.items[translationIndex.value.index][translationIndex.value.type] = preview_content.value.items[translationIndex.value.index][translationIndex.value.type].replace(/\([^()]*\)/g, '').replace(/\n+$/, '');;
  // }
  //preview_content.value.items[translationIndex.value.index][translationIndex.value.type] = ceshi(preview_content.value.items[translationIndex.value.index][translationIndex.value.type])

  // 寻找 "\n(" 的位置
  let index = preview_content.value.items[translationIndex.value.index][translationIndex.value.type].indexOf("\n(");

  // 如果找到 "\n("，则裁剪掉这个位置及之后的内容
  if (index !== -1) {
    preview_content.value.items[translationIndex.value.index][translationIndex.value.type] = preview_content.value.items[translationIndex.value.index][translationIndex.value.type].substring(0, index);
  }
  console.log(preview_content.value.items[translationIndex.value.index][translationIndex.value.type]);
  translationContent.value = preview_content.value.items[translationIndex.value.index][translationIndex.value.type]
  //console.log('翻译',translationContent.value);
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
const promptFlag = ref(false)
const onChange = (event) => {
  console.log(event.target.checked);
  promptFlag.value = event.target.checked
}


const column_options = ref([])
const search = ref({ column: { label: '' }, keywords: '' })
const reset_search = () => {
  search.value = { column: { label: '' }, keywords: '' }
  result_selected.value = []
  result_sort.value = {}
  get_result()
}
const result_selected = ref([])
const show_compare_dialog = ref(false)
const on_result_compare = async () => {
  if (result_selected.value.length === 0) {
    return
  }
  let item_num = 0
  const compare_data = result_selected.value.map((x, i) => {
    const fk = Object.keys(x).filter(k => (Number.isFinite(x[k])))
    const ret = {}
    fk.forEach(k => (ret[k] = x[k]))
    item_num = fk.length
    return { name: x.Model + "_" + i, ...ret }
  })
  show_compare_dialog.value = true

  const type = dataset_type_selected.value?.name
  const dset_map = {
    "Long Report Summarization/S": {
      Relevance: 10,
      ResponseTime: 20,
      RougeL: 1,
    },
    "Long Report Summarization/QA": {
      Relevance: 10,
      ResponseTime: 20,
      RougeL: 1,
      F1Score: 1,
    },
    "Writting": {
      WordErr: 1,
      KeywordRecall: 1,
    },
    "TableQA": {
      Accuracy: 1,
    },
    "CopilotWritting": {
      EditRatio: 1,
      InstructionFollowingRate: 1,
    }
  }

  const is_show_with_radar = item_num >= 3
  show_data_with_chart(compare_data, dset_map[type], is_show_with_radar)
}


const compare_charts = ref(null)
const show_data_with_chart = async (data, data_max_set, is_radar) => {
  await nextTick()
  if (is_radar) {
    compare_charts.value.show_data_with_radar(data, { data_max_set })
  } else {
    compare_charts.value.show_data_with_bar(data)
  }
}


const result_sort = ref()
const on_sort = (event) => {
  const { sortField, sortOrder } = event
  result_sort.value = { sortField, sortOrder }
  get_result()
}
</script>

<template>
  <div class="flex flex-column pt-5">
    <PopoverConfirm ref="confirm" />

    <Dialog v-model:visible="show_compare_dialog" modal header="Analysis" :closeOnEscape="true">
      <Echarts :config="{ width: '600px', height: '600px' }" ref="compare_charts" />
    </Dialog>
    <div class="flex justify-content-between">
      <div class="flex gap-2 align-items-center2">
        <Select v-model="dataset_type_selected" @change="task_type_change" :options="dataset_type_options"
          optionLabel="name" placeholder="Select Type" />
        <MultiSelect v-model="dataset_selected" :options="dataset.items" optionLabel="name" filter
          placeholder="Select Dataset" :maxSelectedLabels="3" class="mr-2 md:w-80" />
        <a-checkbox style="top: 100px;" @change="onChange">
          Is it prompt
        </a-checkbox>
        <Button label="Evaluate" rounded @click="on_add_evaluation" />
        <Button label="Result Compare" rounded @click="on_result_compare" />
      </div>
      <div class="flex align-items-center justify-content-start gap-1">
        <p>Search:</p>
        <Select v-model="search.column" :options="column_options" optionLabel="label" placeholder="Select Column" />
        <IconField>
          <InputText @keyup.enter="get_result()" v-model="search.keywords" placeholder="Press enter to query" />
        </IconField>
        <Button @click="reset_search" icon="pi pi-refresh" text />
      </div>
    </div>
    <DataTable @sort="on_sort" class="compact-table" v-model:selection="result_selected" :value="result.items"
      tableStyle="min-width: 50rem">
      <Column selectionMode="multiple" headerStyle="width: 3rem"></Column>
      <template #empty> No data found. </template>
      <template #loading> Loading data. Please wait. </template>
      <Column sortable v-for="cn in result.columns" :field="cn" :header="cn"></Column>
      <Column>
        <template #body="{ data, index }">
          <div class="flex gap-2">
            <Button @click="on_delete_result($event, data)" rounded style="color: red;" icon="pi pi-trash" text
              size="small" />
            <Button @click="on_result_preview({ ...data })" rounded v-tooltip.top="'detail'" icon="pi pi-align-center"
              text size="small" />
          </div>
        </template>
      </Column>
      <template #footer>
        <Paginator :totalRecords="result.total" @page="change_result_page" :rows="result.rows"
          :rowsPerPageOptions="[5, 10, 20, 50]">
          <template #start>
            <Button @click="get_result()" rounded type="button" icon="pi pi-refresh" text />
          </template>
          <template #end>
            {{ `Total: ${result.total}` }}
          </template>
        </Paginator>
      </template>
    </DataTable>
    <Toast />
  </div>

  <Panel header="Data Result">
    <DataTable class="compact-table" :value="preview_content.items" tableStyle="min-width: 50rem;">
      <template #header>
        <div class="flex align-items-center justify-content-between">
          <div class="flex flex-column">
            <span><b>Name:</b> {{ current_preview?.Model }}</span>
            <span><b>Type:&ensp;</b> {{ current_preview?.Type }}</span>
          </div>
          <span>Total: {{ preview_content.total }}</span>
        </div>
      </template>
      <template #empty> No data found. </template>
      <template #loading> Loading data. Please wait. </template>
      <!-- <Column v-for="cn in preview_content.columns" :field="cn" :header="cn">
        <template>
          <div @contextmenu.prevent="handleRightClick($event, cn)">
            {{ getContent(cn) }}
          </div>
        </template>
      </Column> -->
      <div v-for="cn in preview_content.columns" :key="cn">
        <Column :field="cn" :header="cn">
          <template v-slot:body="slotProps">
            <div @contextmenu.prevent="handleRightClick($event, slotProps)" class="pre-wrap">
              {{ getContent(slotProps) }}
            </div>
          </template>
        </Column>
      </div>
      <template #footer>
        <Paginator :totalRecords="preview_content.total" :rows="preview_content.rows"
          @page="change_preview_content_page" :rowsPerPageOptions="[5, 10, 20, 50]" />
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
.p-fieldset {
  overflow: auto;
  /* 确保 Fieldset 容器是可滚动的 */
}

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

.align-items-center2 {
  display: flex;
  align-items: center;
  /* 这将使所有子元素垂直居中对齐 */
}
</style>
