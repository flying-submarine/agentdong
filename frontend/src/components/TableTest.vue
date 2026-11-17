<template>
  <div>
    <DataTable :value="items">
      <Column field="name" header="Name"></Column>
      <Column field="age" header="Age"></Column>
      <Column field="job" header="Job"></Column>
      <template #footer>
        <Paginator :rows="rows" :totalRecords="totalRecords" @page="onPageChange"></Paginator>
      </template>
    </DataTable>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import DataTable from 'primevue/datatable';
import Paginator from 'primevue/paginator';
import Column from 'primevue/column';

export default {
  name: 'PaginationTable',
  components: {
    DataTable,
    Column,
    Paginator,
  },
  setup() {
    const items = ref([]);
    const rows = ref(5);  // 每页显示5条数据
    const totalRecords = ref(0);
    const currentPage = ref(0);

    const fetchData = (page, rows) => {
      // 模拟数据请求
      setTimeout(() => {
        const totalData = Array.from({ length: 100 }, (_, i) => ({
          name: `Name ${i + 1}`,
          age: 20 + (i % 10),
          job: `Job ${i + 1}`
        }));

        const start = page * rows;
        const end = start + rows;
        console.log(start, end)
        items.value = totalData.slice(start, end);
        totalRecords.value = totalData.length;
        // items.value.length = totalData.length;
      }, 500);
    };

    onMounted(() => {
      fetchData(currentPage.value, rows.value);
    });

    const onPageChange = (event) => {
      currentPage.value = event.page;
      fetchData(currentPage.value, rows.value);
    };

    return {
      items,
      rows,
      totalRecords,
      onPageChange
    };
  }
};
</script>

<style>
/* 写上你需要的样式 */
</style>
