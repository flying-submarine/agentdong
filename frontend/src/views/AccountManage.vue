<script setup>

import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import DataTable from 'primevue/datatable';
import Paginator from 'primevue/paginator';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import { serviceFetch } from '@/service/utils';
import { message } from 'ant-design-vue';
import { nextTick, onMounted, onUnmounted, ref } from 'vue';

const products=ref([]);
const visible = ref(false);
const departmentList = ref([]);
const accountManageRef = ref()
const invitation = ref({
  email: '',
  departmentId: ''
})
const pageInfo = ref({
  pageNum: 1,
  pageSize: 10,
  total: 0,
})
const rules = {
  email: [{ required: true, message: 'Please input email address',trigger: ['change'] }, 
  { type: 'email', message: 'Please input correct email address', trigger: ['blur'] }],
  departmentId: [{ required: true, message: 'Please select department' }]
}
const formRef = ref();

const getAccountList = async (params)=>{
  const res = await serviceFetch('/gpt/user/page', {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(params)
  });
  const data = await res.json();
  if(data.code === 200) {
    products.value=data.data.records;
    pageInfo.value.total = data.data.total;
  }
}


const getDepartmentList = async ()=>{
  const res = await serviceFetch('/gpt/department/list?compantId=1', {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const response = await res.json();
  if(response.code === 200) {
    departmentList.value=(response.data||[]).map(item=>{
      return {
        value: item.id,
        label: item.departmentName
      }
    });
  }
}

const initData = ()=>{
  getAccountList({pageNum: 1, pageSize: 10});
  getDepartmentList();

}
const openDialog = ()=>{
  visible.value=true;
}

initData();

const sendInvitation = async ()=>{
  try {
    await formRef.value.validate();
  } catch(error) {
    return;
  }
  const info = invitation.value;
  const res = await serviceFetch('/gpt/email/send/invitation', {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(info)
  });
  const response =await res.json();
  if(response.code === 200) {
    visible.value = false;
    invitation.value = {
      email: '',
      departmentId: ''
    }
    // getAccountList();
    message.success('Send email successfully');
  } else {
    message.error(response.message);
  }
}

const reSendEmail = (email, department)=>{
  console.log(email, department, 'info')
}

const changePage = (e)=>{
  getAccountList({
    pageNum: e.page + 1,
    pageSize: e.rows
  })
}

const hideDialog = ()=>{
  invitation.value = {
    email: '',
    departmentId: ''
  }
  visible.value = false;
}

const changeDepartment =async (e, idx, data)=>{
  const submitInfo = {
    userId: data.id,
    departmentId: e.value
  }
  const res = await serviceFetch('/gpt/user/update', {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(submitInfo)
  });
  const response =await res.json();
  if(response.code === 200){
    products.value=products.value.map((item, i)=>{
      if(i==idx) {
        item.departmentId = e.value;
        item.departmentName = (departmentList.value.find(ele=>ele.value==e.value)).label;
        item.isEditor = false;
      }
      return item;
    });
    keyRef.value=Math.random();
    message.success('Department modified successfully')
  }else {
    message.error(response.message);
  }
}


const editRow = (idx)=>{
  products.value=products.value.map((item, i)=>{
    if(i==idx) {
      item.isEditor = true;
    }
    return item;
  });
}

// onMounted(()=>{
//   document.addEventListener('click', handleCancel)
// })
// onUnmounted(()=>{
//   document.removeEventListener('click', handleCancel)
// })
const handleCancel = (e)=>{
 // debugger;
//  if(!accountManageRef.value.contains(e.target)) {
    products.value=products.value.map((item, i)=>{
      item.isEditor = false;
      return item;
    });
 // }

}

const keyRef = ref(Math.random())
</script>

<template>
  <div>
  <Splitter style="width: 100%;" :gutterSize="0">
    <SplitterPanel>
      <div class="account-manage">
        <div class="account-header">
          <div class="title">Account management</div>
          <Button @click="openDialog" class="operate">Add Account</Button>
        </div>
        <div class="account-table">
          <DataTable :value="products" editMode="cell" :key="keyRef">
            <Column field="id" header="ID" style="text-align: center;font-size: 14px;"></Column>
            <Column field="email" header="Email address" style="text-align: center;font-size: 14px;"></Column>
            <Column field="departmentName" header="Department" style="text-align: center;font-size: 14px;" >
              <template #body="{ data, field, index }">
                <div>
                  <div>{{ data[field] }}</div>
                </div>
              </template>
              <template #editor="{ data, field, index }">
                <div>
                  <Select @change="(e)=>changeDepartment(e, index, data)" :modelValue="data.departmentId" :options="departmentList" optionLabel="label" optionValue="value"></Select>
                </div>
              </template>
            </Column>
            <Column field="status" header="Status" style="text-align: center;font-size: 14px;">
              <template #body="{data}">
                <div @click="()=>reSendEmail(data.email, data.department)">enrolled</div>
              </template>
            </Column>
          </DataTable>
          <Paginator  @page="changePage" :rows="pageInfo.pageSize" :alwaysShow="false" :totalRecords="pageInfo.total" :rowsPerPageOptions="[10, 20, 30]"></Paginator>
        </div>
        <Dialog class="dialog-account" v-model:visible="visible" @hide="hideDialog" modal header="New Account Invitation" :style="{ width: '821px' }">
          <div class=" items-center mb-4">
              <a-form
                ref="formRef"
                :model="invitation"
                :rules="rules"
                layout="vertical"
              >
                <a-row type="flex" justify="center" align="top" :gutter="8">
                  <a-col :span="12">
                    <a-form-item class="input-label" label="Email Address" name="email" :required="false">
                      <a-input :maxlength="120" class="invitation-info" placeholder="Email" v-model:value="invitation.email" autocomplete="off"/>
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item class="input-label" label="Department" name="departmentId" :required="false">
                      <a-select :dropdownStyle="{'z-index':1200 }" placeholder="select a department" class="invitation-dept" v-model:value="invitation.departmentId"  :options="departmentList"></a-select>
                    </a-form-item>
                  </a-col>
                </a-row>
              </a-form>
          </div>
          <div class="flex justify-end gap-2">
              <Button type="button" label="Cancel" severity="secondary" @click="visible = false"></Button>
              <Button type="button" label="Send invitation " @click="sendInvitation"></Button>
          </div>
      </Dialog>
      </div>
    </SplitterPanel>
  </Splitter>
  </div>
</template>

<style>
  .account-manage {
    margin: 21px 31px;
    .account-header {
      display: flex;
      justify-content: space-between;
      padding-bottom: 11px;
      border-bottom: 1px solid rgba(172,199,255,0.44);
      .title {
        font-size: 20px;
        color: var(--p-primary-500);
        font-weight: 600;
      }
      .operate {
        font-weight: 500px;
        font-size: 16px;
      }
    }
    .account-table {
      margin-top: 16px;
      .p-datatable-thead {
        background-image: linear-gradient(180deg, #A57AF1 0%, #6868F5 100%);
        .p-datatable-header-cell {
          background-color: transparent;
          color: #fff;
          .p-datatable-column-header-content {
            justify-content: center;
          }
        }
      }
    }
  }
  .dialog-account {
     .p-dialog-title {
      font-size: 20px;
     }
     .invitation-info {
      width:373px !important;
      min-height: 40px;
      border: none;
      background: rgba(68,64,255,0.1);
      .p-select-label {
        line-height: 26px;
      }
     }
     .invitation-dept {
        .ant-select-selector {
          border: none;
          height: 40px;
          border-radius: 3px;
        background: rgba(68,64,255,0.1);
          .ant-select-selection-item {
            line-height: 40px;
          }
        }
     }
     .input-label {
      label {
        font-size: 18px;
        color: #444;
      }
     }
     .ant-form-item .ant-form-item-label >label.ant-form-item-required:not(.ant-form-item-required-mark-optional)::before {
      display: none;
     }
  }
  .department {
    .p-select-label {
      line-height: 1.2;
    }
  }
  .justify-end {
    justify-content: flex-end;
  }
</style>
