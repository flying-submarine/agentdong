<script setup lang="ts">
import Papa from 'papaparse';
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Paginator from 'primevue/paginator'
import { onMounted, ref } from 'vue';
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import { lazy_load_text } from '@/service/utils'


const current_table_title = ref('')
const csv_data = ref([])

const table_data = ref({ items: [], total: 0, rows: 10, page: 0 })
const get_table_data = async () => {
  const { rows, page } = table_data.value
  const start = page * rows;
  const end = start + rows;
  const data = table_filter(csv_data.value)
  table_data.value.items = data.slice(start, end)
  table_data.value.total = data.length
}

const to_page = (e) => {
  table_data.value.page = e.page
  table_data.value.rows = e.rows
  get_table_data()
}

let get_csv_page = null
const header = ref('')
const get_table_data_lazy = async () => {
  const { rows, page } = table_data.value
  loading.value = true
  const { data, total } = await get_csv_page(page, rows)
  loading.value = false

  // init header
  if (page == 0 && data.length > rows) {
    header.value = data[0]
  }

  const header_text = page == 0 ? '' : (header.value + '\n')
  const context = header_text + data.join('\n')
  Papa.parse(context, {
    header: true,
    complete: ret => {
      table_data.value.items = ret.data
      table_data.value.total = total
    },
  })
}

const load_table_data = async (url) => {
  const data = await parse_csv(url)
  // string to number if success
  data.forEach(d => {
    for (const k in d) {
      const t = d[k]
      const n = Number(t)
      d[k] = isNaN(n) ? t : n
    }
  });
  column_options.value = data.length > 0 ? Object.keys(data[0]).map(x => ({ label: x })) : []
  csv_data.value = data
}

const loading = ref(false)
const parse_csv = async (url): Promise<any> => {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      download: true,
      header: true,
      complete: (results) => (resolve(results.data)),
    })
  })
}

const init_table = async (url: string) => {
  header.value = ''
  get_csv_page = await lazy_load_text(url)
  table_data.value = { items: [], total: 0, rows: 10, page: 0 }
}

const csv_table_list = ref([])
const show_csv = async (tables) => {
  if (tables.length == 0) {
    return
  }
  csv_table_list.value = tables
  current_table.value = tables[0]
  change_table()
}

const current_table = ref()
const change_table = async () => {
  const { url, title } = current_table.value
  current_table_title.value = title
  await load_table_data(url)
  get_table_data()
}

const on_sort = (event) => {
  const { sortField, sortOrder } = event
  csv_data.value.sort((a, b) => {
    const ak = a[sortField]
    const bk = b[sortField]
    if (ak === 'NA') return 1
    if (bk === 'NA') return -1
    return ak > bk ? sortOrder : sortOrder * -1
  })
  get_table_data()
}

const emit = defineEmits<{
  (e: "toggle_expand_table", flag: boolean): void;
}>()
const expand_flag = ref(false)
const expand_table = () => {
  emit("toggle_expand_table", expand_flag.value)
  expand_flag.value = !expand_flag.value
}

const table_filter = (data = []) => {
  const column = search.value?.column?.label ?? ''
  if (!column) {
    return data
  }

  const kw = search.value?.keywords
  if (!kw) {
    return data
  }
  return data.filter(x => ((x[column] + '').indexOf(kw) > -1))
}

const column_options = ref([])
const search = ref({ column: { label: '' }, keywords: '' })
const reset_search = () => {
  search.value = { column: { label: '' }, keywords: '' }
  get_table_data()
}

defineExpose({
  show_csv,
})
</script>


<template>
  <div class="flex flex-column">
    <div class="flex align-items-center h-4rem justify-content-between" style="border-bottom: 1px solid #ccc;">
      <p>&ensp;</p>
      <Dropdown  v-model="current_table" @change="change_table" :options="csv_table_list" optionLabel="title"
        placeholder="Select Table" class="w-full md:w-15rem m-1">
      </Dropdown>
      <Button @click="expand_table" text :icon="expand_flag ? 'pi pi-arrow-left' : 'pi pi-arrow-right'" />
    </div>
    <DataTable @sort="on_sort" class="compact-table" :loading="loading" :value="table_data.items">
      <template #header>
        <div class="flex align-items-center justify-content-start gap-1">
          <p>Search:</p>
          <Select v-model="search.column" :options="column_options" optionLabel="label" placeholder="Select Type"
            class="" />
          <IconField>
            <InputText @keyup.enter="get_table_data()" v-model="search.keywords" placeholder="Press enter to query" />
          </IconField>
          <Button @click="reset_search" icon="pi pi-refresh" text />
        </div>
      </template>
      <template #empty> No table found. </template>
      <template #loading>
        <div class="flex align-items-center gap-2">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
          <span>Loading table data. Please wait. </span>
        </div>
      </template>
      <Column sortable v-for="fn in table_data.items.length > 0 ? Object.keys(table_data.items[0]) : []" :field="fn"
        :header="fn" />
      <template #footer>
        <Paginator :rows="table_data.rows" :totalRecords="table_data.total" @page="to_page"
          :rowsPerPageOptions="[5, 10, 20, 50]">
          <template #start>
            <Button @click="get_table_data()" rounded type="button" icon="pi pi-refresh" text />
          </template>
          <template #end>
            {{ `Total: ${table_data.total}` }}
          </template>
        </Paginator>
      </template>
    </DataTable>
  </div>
</template>



<style scoped></style>