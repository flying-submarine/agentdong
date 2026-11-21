<script setup >
import { ref, onMounted, computed } from 'vue';
import PopoverConfirm from '@/components/PopoverConfirm.vue'
import { useRouter } from 'vue-router';
import { serviceFetch } from '@/service/utils';
import { useTokenStore } from "@/stores/token";
import { h } from 'vue';
import { message } from 'ant-design-vue';
import MarkdownRenderer from '@/components/MarkdownRenderer.vue';

const tokenStore = useTokenStore();
const router = useRouter();
const isUploading  = ref(false)
const fileList = ref([]);
const latestDocId = ref('')   // 最近一次上传成功后返回的 doc_id

// ---------- Recent Records：全部由后端接口提供（不做本地缓存） ----------
// GET  /api/doc/docs                   -> { data: [{ docId, fileName, createTime, chars, chunks, status }] }
// GET  /api/doc/docs/{docId}/content   -> { data: { text } }
// DELETE /api/doc/doc/{docId}          -> { docId, deleted }
const records = ref([])

const getRecords = async()=>{
  return (await serviceFetch(`/api/doc/docs`, { headers: {} })).json();
}

const init_Records = ()=>{
  getRecords().then((data) => {
    if (data && data.data && Array.isArray(data.data)) {
      records.value = data.data
    }
  }).catch(() => {})
}

// 上传后后端是异步入库，轮询列表直到这篇文档不再是 processing
const pollRecordsUntilDone = (docId, tries = 0) => {
  if (!docId || tries >= 15) return
  setTimeout(async () => {
    try {
      const data = await getRecords()
      if (data && Array.isArray(data.data)) {
        records.value = data.data
        const target = data.data.find(r => r.docId === docId)
        if (target && target.status !== 'processing') return
      }
    } catch (e) {
      console.warn('刷新文档列表失败', e)
    }
    pollRecordsUntilDone(docId, tries + 1)
  }, 2000)
}

onMounted(()=>{
  init_Records()
})
const dialogVisible = ref(false)
const truncatedFileName =(record) => {
  const maxLength = 50;
  const name = record.fileName || ''
  if (name.length > maxLength) {
    return name.slice(0, maxLength) + '...';
  }
  return name;
};

const confirm = ref(null)
const on_delete_session = (event, docId) => {
  confirm.value.show({
    label: 'Do you want to delete this item?',
    accept: () => serviceFetch(`/api/doc/doc/${docId}`, { method: 'DELETE' }).then(() => init_Records()),
    event,
  })
}

const handleDrop = (e)=>{
}

const customHeaders = ref({
  'Authorization': "Bearer "+tokenStore.token,
});

const UPLOAD_MESSAGE_KEY = 'logr-upload'

const handleChange = (info) => {
  const { status } = info.file;

  let resFileList = [...info.fileList];
  resFileList = resFileList.filter(file=>file.status !== "error").map(item=>({
    ...item,
    name:item.status === "uploading" ? "processing..." :item.name
  }))
  fileList.value = resFileList;

  if (status === 'done') {
    isUploading.value = false
    // 后端 /api/doc/upload 返回 { task_id, doc_id, filename, status, message, chars }
    const resp = info.file?.response || {}
    latestDocId.value = resp.doc_id || info.file.uid

    message.success({
      content: h('span', { class: 'logR-message-content' }, [
        `${info.file.name.length > 15 ? info.file.name.substring(0,13) + '...' : info.file.name} file uploaded successfully `,
        h('a', { href: '#', onClick: () => navDetail(), style: 'color:var(--app-primary); text-decoration: underline;' }, 'Check now')
      ]),
      key: UPLOAD_MESSAGE_KEY,
      duration: 5
    });
    init_Records()
    pollRecordsUntilDone(latestDocId.value)
  }
  if (info.file?.status === "error") {
    isUploading.value = false
    // FastAPI HTTPException 的错误体是 { detail: "..." }，兼容旧的 { message } 格式
    const resp = info.file?.response
    message.error({
      content: resp?.detail || resp?.message || `${info.file.name} file upload failed.`,
      key: UPLOAD_MESSAGE_KEY,
    });
  }
};

const navigateToPage = (id,sd) => {
  const sid = sd ? sd : "x"
  router.push(`/bussiness/LongReportSummarization/${id}/${sid}`);
};

const navDetail = ()=>{
  if (latestDocId.value) {
    navigateToPage(latestDocId.value)
    return
  }
  getRecords().then((data) => {
    if (data && data.data && Array.isArray(data.data) && data.data.length) {
      const {docId,sessionId} = data.data[0]
      navigateToPage(docId,sessionId)
    }
  })
}

// ---------- 预览弹窗：正文从后端按需读取 ----------
const previewVisible = ref(false)
const previewRecord = ref(null)
const previewContent = ref('')
const previewLoading = ref(false)
const previewTitle = computed(() => previewRecord.value?.fileName || 'Preview')
const previewIsMarkdown = computed(() => /\.md$/i.test(previewRecord.value?.fileName || ''))

const openPreview = async (record) => {
  previewRecord.value = record
  previewContent.value = ''
  previewVisible.value = true
  previewLoading.value = true
  try {
    const res = await serviceFetch(`/api/doc/docs/${record.docId}/content`, { headers: {} })
    const data = await res.json()
    previewContent.value = data?.data?.text || ''
  } catch (e) {
    previewContent.value = '（内容加载失败，请稍后重试）'
  } finally {
    previewLoading.value = false
  }
}
const onRecordClick = (record) => {
  openPreview(record)
}
const openPreviewDetail = () => {
  if (!previewRecord.value) return
  const { docId, sessionId } = previewRecord.value
  previewVisible.value = false
  navigateToPage(docId, sessionId)
}

// 与后端 doc_service.py 的 ALLOWED_EXTS / MAX_FILE_SIZE 保持一致
const ALLOWED_UPLOAD_EXTS = ['pdf', 'docx', 'md', 'txt']
const MAX_UPLOAD_SIZE = 20 * 1024 * 1024

const checkUp = (file,fileList)=>{
  const ext = (file.name?.split('.').pop() || '').toLowerCase()
  if (!ALLOWED_UPLOAD_EXTS.includes(ext)) {
    message.error('仅支持 PDF / DOCX / MD / TXT 格式')
    return false
  }
  if (file.size > MAX_UPLOAD_SIZE) {
    message.error('文件不能超过 20MB')
    return false
  }
  if (isUploading.value) {
    message.warn('Please wait until the current upload is finished.');
    return false;
  }
  isUploading.value = true
  message.loading({ content: 'Uploading and parsing...', key: UPLOAD_MESSAGE_KEY, duration: 0 })
}

const addFile = ()=>{
  dialogVisible.value=true
}

const progress = {
  class: 'logr_progress',
  size: 'small',
  strokeColor: { '0%': '#574FD7', '100%': '#9D8BFF' },
  showInfo: true,
};

const onDialogHide = ()=>{
  fileList.value  = []
  isUploading.value=false
  message.destroy(UPLOAD_MESSAGE_KEY)
}
</script>


<template>
  <div class="longReport-page">
    <PopoverConfirm ref="confirm" />
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
          accept=".pdf,.docx,.md,.txt"
          action="/api/doc/upload"
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
          <div>
            <p>Document Size: &lt;20MB</p>
            <p>Document Format: PDF / DOCX / MD / TXT (text-based)</p>
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
        <div v-for="record in records" :key="record.docId" class="record-card" @click="onRecordClick(record)">
          <a-tooltip placement="rightTop" :title="record.fileName">
            <p style="height: 65px;width: 100%;">
              {{truncatedFileName(record)}}
            </p>
          </a-tooltip>
          <div class="record-footer">
            <div class="record-meta">
              <span v-if="record.status === 'processing'" class="record-status processing">处理中</span>
              <span v-else-if="record.status === 'failed'" class="record-status failed">失败</span>
              <span v-else-if="record.status === 'done'" class="record-status done">已入库</span>
              <p class="record-date" >{{ record.createTime }}</p>
            </div>
            <Button @click.stop="on_delete_session($event, record.docId)" icon="pi pi-trash" class="p-button-text p-button-rounded" />
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="previewVisible"
      :title="previewTitle"
      width="840px"
      :footer="null"
      class="logr-preview-modal"
    >
      <div v-if="previewLoading" class="preview-placeholder">
        <a-spin /> <span style="margin-left:8px">内容加载中...</span>
      </div>
      <div v-else-if="previewContent" class="preview-body">
        <MarkdownRenderer v-if="previewIsMarkdown" :source="previewContent" />
        <pre v-else class="preview-pre">{{ previewContent }}</pre>
      </div>
      <div v-else class="preview-placeholder">没有可预览的文本内容</div>
      <div class="preview-footer">
        <Button size="small" icon="pi pi-external-link" label="打开详情页" @click="openPreviewDetail" />
      </div>
    </a-modal>
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
/* 上传进度条：显示出来并贴合弹窗宽度 */
::v-deep .logr_progress{
  margin: 8px 0 0;
}
::v-deep .ant-upload-list-item-progress{
  padding-inline-start: 0;
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
  justify-content: space-between;
  align-items: center;
}
.record-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.record-status {
  font-size: 10px;
  line-height: 14px;
  padding: 0 6px;
  border-radius: 7px;
  margin-bottom: 2px;
}
.record-status.processing { background: rgba(87, 79, 215, 0.12); color: #574FD7; }
.record-status.done { background: rgba(16, 185, 129, 0.14); color: #0f9d74; }
.record-status.failed { background: rgba(220, 53, 69, 0.12); color: #dc3545; }

.preview-body {
  max-height: 60vh;
  overflow: auto;
  background: rgba(164, 186, 224, 0.12);
  border-radius: 4px;
  padding: 4px 12px;
}
.preview-pre {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.7;
  margin: 0;
  font-family: inherit;
}
.preview-placeholder {
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-size: 13px;
}
.preview-footer {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

.record-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(226px, 330px));
  gap: 20px;
  grid-auto-rows: min-content;
}

.logR-grid{
  height: calc(100vh - 460px);
  min-height: 260px;   /* 视口偏小（如打开 DevTools）时保证卡片仍可见，否则 calc 为负会把容器压成 0 */
  overflow-y: auto;
}

.record-card {
  height: 122px;
  padding: 20px 12px 12px 10px;
  position: relative;
  margin: 0 2.5px;
  background-color: rgba(164, 186, 224, 0.25);
  box-shadow: 0 0 5px 5px transparent;
  border-radius: 3px;
  word-break: break-word;
  font-size:14px;
  color: #333;
  line-height: 21px;
  font-weight: 500;
  cursor: pointer;
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
}

.p-button-text {
  position: absolute;
}

</style>
