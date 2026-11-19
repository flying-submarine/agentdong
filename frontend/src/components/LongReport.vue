<script setup >
import { ref,onMounted } from 'vue';
import PopoverConfirm from '@/components/PopoverConfirm.vue'
import { useRouter } from 'vue-router';
import { serviceFetch } from '@/service/utils';
// import { v4 as uuidv4 } from 'uuid'
import { useTokenStore } from "@/stores/token";
import { LongReportSummarizationSession } from "@/service/LongReportSummarizationSession";
import { h } from 'vue';
import { message} from 'ant-design-vue';

const tokenStore = useTokenStore();
const router = useRouter();
const isUploading  = ref(false)
const fileList = ref([]);
const navigateToPage = (id,sd) => {
  const sid = sd ? sd : "x"
  router.push(`/bussiness/LongReportSummarization/${id}/${sid}`);
};
const records = ref([])

const getRecords = async()=>{
  return (await serviceFetch(`/gpt/lrllm/docs`, { 
    headers: {},
  })).json();
}


const init_Records = ()=>{
  getRecords().then((data) => {
    if (data.data) {
      records.value = data.data
    }
  })
}

onMounted(()=>{
  init_Records()
})
const dialogVisible = ref(false)
const truncatedFileName =(record) => {
  const maxLength = 50;
  if (record.fileName.length > maxLength) {
    return record.fileName.slice(0, maxLength) + '...';
  }
  return record.fileName;
};

const confirm = ref(null)
const on_delete_session = (event, sid) => {
  confirm.value.show({
    label: 'Do you want to delete this item?',
    accept: () => LongReportSummarizationSession.delete(sid).then(() => {init_Records()}),
    event,
  })
}

const handleDrop = (e)=>{
}

const customHeaders = ref({
  'Authorization': "Bearer "+tokenStore.token,  // 替换为你的实际Token
});

const handleChange = (info) => {
  const { status } = info.file;

  let resFileList = [...info.fileList];

  // 2. read from response and show file link
  resFileList = resFileList.filter(file=>file.status !== "error").map(item=>({
    ...item,
    name:item.status === "uploading" ? "processing..." :item.name
  }))

  fileList.value = resFileList;

  if (status === 'done') {
    isUploading.value = false
    message.success({
      content: h('span', { class: 'logR-message-content' }, [
        `${info.file.name.length > 15 ? info.file.name.substring(0,13) + '...' : info.file.name} file uploaded successfully `,
        h('a', { href: '#', onClick: () => navDetail(), style: 'color:var(--app-primary); text-decoration: underline;' }, 'Check now')
      ]),
      duration: 5
    });
    init_Records()
  } 
  if (info.file?.status === "error") {
    isUploading.value = false
    message.error(info.file?.response?.message || `${info.file.name} file upload failed.`);
  }
};

const navDetail = ()=>{
  getRecords().then((data) => {
    if (data.data.length && Array.isArray(data.data) ) {
      const lastestItem = data.data[0]
      const {docId,sessionId} = lastestItem
      navigateToPage(docId,sessionId)
    } 
  })
}
const checkUp = (file,fileList)=>{
  // console.log(file,fileList,'file,fileList')
  if (isUploading.value) {
    message.warn('Please wait until the current upload is finished.');
    return false; // 阻止上传
  }
  if(records.value.length>9) {
    message.warn('Maximum files 10')
    return false
  } 
  isUploading.value = true
}

const addFile = ()=>{
  if(records.value.length>9) {
    message.warn('Maximum files 10')
    return false
  } 
  dialogVisible.value=true
}

const progress = {
  class: 'logr_progress',
};

const onDialogHide = ()=>{
  // console.log('hideDialog')
  fileList.value  = []
  isUploading.value=false
}
</script>


<template>
  <PopoverConfirm ref="confirm" />
  <div class="longReport-page">
    <div>
      <p style="font-size: 18px;color: #574FD7;font-weight:600;border-bottom:1px solid rgba(172, 199, 255, 0.44)
        ;margin-bottom: 18px;">Create New Doc</p>
      <div class="record-grid">
        <div class="record-add-card">
          <Button icon="pi pi-plus" class="p-button-rounded" @click="addFile"/>
        </div>
      </div>
      <Dialog 
        class="longR-Dialog" 
        v-model:visible="dialogVisible" 
        modal 
        header="Upload Files" 
        style="width:684px;z-index:900"
        @hide="onDialogHide"
      >
        <a-upload-dragger
          name="file"
          accept=".pdf" 
          action="/gpt/lrllm/docs/upload"
          :headers="customHeaders" 
          @change="handleChange"
          @drop="handleDrop"
          :progress="progress"
          :file-list="fileList"
          :before-upload="checkUp"
          :showUploadList="{ showRemoveIcon: false }"
          class="logR-upload-drag"
        >
          <div class="upload-btn">
            <img src="@/assets/longReportUpload.png" alt="Logo" class="button-logo">
            <span>Click or drag files here to upload</span>
          </div>
        </a-upload-dragger>
        <div class="upload-info">
          <div style="width">
            <p>Document Size: &lt;30MB</p> 
            <p>Document Format:.pdf file with text as main content</p>
          </div>
          <div>
            <p>Document Pages: &lt;100 pages</p>
            <p>Document Language Supported:Arabic, English</p> 
          </div>
        </div>
      </Dialog>
    </div>

    <div class="recent-records">
      <p  class="recent-records-title"
        style="
          font-size: 18px;
          color: #574FD7;
          font-weight:600;
          border-bottom:1px solid rgba(172, 199, 255, 0.44);
          margin-bottom: 18px;
        ">
          Recent Records
      </p>
      <div class="record-grid logR-grid">
        <div v-for="record in records" :key="record.docId" class="record-card" @click="navigateToPage(record.docId,record.sessionId)">
          <a-tooltip placement="rightTop" :title="record.fileName">
            <p style="height: 65px;width: 100%;">
              {{truncatedFileName(record)}}
            </p>
          </a-tooltip>
          <div class="record-footer"> 
            <p class="record-date" >{{ record.createTime }}</p>
            <Button @click.stop="on_delete_session($event, record.docId)" icon="pi pi-trash" class="p-button-text p-button-rounded" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

.longReport-page{
  background-image: url('@/assets/IconRagContent.png');
  box-shadow: var(--app-shadow-sm);
  border-radius: 5px;
  background-color: #fff;
  padding: 22px 34px 22px;
  height: 100%;
}

.create-new-doc {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.upload-btn{
  width:100%;
  height:334px;
  background-color: rgba(108,64,255,0.1);
  border-radius: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
}

.upload-btn span{
  margin-top:15px;
  font-size:22px;
  color:var(--app-primary);
  letter-spacing: 0.33px;
  font-weight:400px;
  line-height: 30px;
}

.recent-records {
  margin-top: 30px;
}
.recent-records-title{
  
}

::v-deep .logR-upload-drag{
  border: none;
}
::v-deep .logr_progress{
  display:none;
}
::v-deep .logR-upload-drag .ant-upload{
  padding:0;
}

.upload-info{
  margin-top:20px;
}

.upload-info > div{
  display: flex;
  color: #444444;
  letter-spacing: 0.25px;
  line-height: 30px;
}

.upload-info > div > :first-child{
  width: 265px;
}

.upload-info > div > :last-child{
  flex: 1;
}

.ant-upload-btn {
  padding:0;
}

.record-footer {
  display: flex;
  justify-content: space-between; /* 将元素左右分布 */
  align-items: center; /* 垂直居中对齐 */
}


.record-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(226px, 330px));
  gap: 20px; 
  grid-auto-rows: min-content; 
}

.logR-grid{
  height: calc(100vh - 460px);
  overflow-y: scroll;
}

.record-card {
  height: 122px;
  padding: 20px 12px 12px 10px;
  position: relative;
  margin: 0 2.5px; 
  background-color: rgba(164, 186, 224, 0.25);
  box-shadow: 0 0 5px 5px transparent;
  border-radius: 3px;
  word-break: break-word; /* 允许在单词内部换行 */
  font-size:14px;
  color: #333;
  line-height: 21px;
  font-weight: 500;
}
.record-add-card{
  text-align: center;
  height: 122px;
  line-height: 122px;
  margin: 0 2.5px; 
  background-color: rgba(87, 79, 215, 0.2);
  box-shadow: 0 0 5px 5px transparent;
  border-radius: 3px;
}
.record-date {
  font-size: 10px;
  line-height: 14px;
  color: #333;
  font-weight: 400;
  /* margin-top: 10px; */
}

.p-button-text {
  position: absolute;
  /* top: 10px; */
  /* right: 10px; */
}

</style>