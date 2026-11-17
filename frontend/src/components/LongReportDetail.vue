<script setup>
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import LongReportChat from '@/components/LongReportChat.vue'
import { ref,onMounted,nextTick} from 'vue';
import { LongReportSummarizationSession } from "@/service/LongReportSummarizationSession";
import { useRoute } from 'vue-router';
import { useRouter } from 'vue-router';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import MarkdownRenderer from "./MarkdownRenderer.vue";
import { calcNumber } from '@/service/utils';

const spinning = ref(false);
const route = useRoute()
const router = useRouter();
const docId = route.params.docId ;
const tabs = ['Summary', 'File Reading'];
const logR_summary_content = ref<HTMLElement | null>(null);
const selectedTab = ref(0);
const words = ref();
const iframeKey = ref(0);
const detailInfo = ref({
  docId:"",
  docSummary:"",
  fileName:"",
  sid:""
})
const wordsNumber = ref(0);
const pdfUrl = ref("")

const summaryText = ref("")

const selectTab = (index) => {
  selectedTab.value = index;
};

const navigateToPage = () => {
  router.push('/bussiness/LongReportSummarization');
};

const initInfo = ()=>{
  LongReportSummarizationSession.get(docId).then(data=>{
    detailInfo.value = data
    pdfUrl.value = data.oss_url+`#toolbar=0&page=${1}`
    summaryText.value = data.docSummary;
    const wNumber = calcNumber(data.docSummary);
    wordsNumber.value = wNumber;
  })
}

onMounted(()=>{
  initInfo()
})

const submitWords = async()=>{
  spinning.value = true 
  summaryText.value = ""
  const response =await LongReportSummarizationSession.getSummary(docId,words.value)
  spinning.value = false 

  for await(const chunk of response) {
    const status = chunk.status
    if (status === 'generating') {
      // console.log(chunk,'lchunk')
      summaryText.value += chunk.output ?? '';
      // console.log(chunk.output,'chunk.output')
      const wNumber = calcNumber(summaryText.value);
      wordsNumber.value = wNumber;
      await nextTick(); // 确保 DOM 更新
      // scrollToBottom(logR_summary_content)
    } else if (status === 'stop') {
      // scrollToBottom(logR_summary_content)
      break
    }
  }
}

const exportPdf = ()=>{
  const pdfElement = document.getElementById("logr-summary");
  const cloneElement = pdfElement.cloneNode(true);
  cloneElement.style.height = pdfElement.scrollHeight + 'px';
  cloneElement.style.zIndex = -1;
  cloneElement.style.fontSize = 10+"px";

  document.body.appendChild(cloneElement);
  requestAnimationFrame(() => {
    html2canvas(cloneElement, {
      allowTaint: false,
      useCORS: true, 
    }).then(canvas => {
      document.body.removeChild(cloneElement);
      const imgData = canvas.toDataURL('image/png');
      const doc = new jsPDF('p', 'mm', 'a4');
      const bufferX = 10;
      const bufferY = 10;
      const imgProps = doc.getImageProperties(imgData);
      const pdfWidth = doc.internal.pageSize.getWidth() - 2 * bufferX;
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
      doc.addImage(imgData, 'png', bufferX, bufferY, pdfWidth, pdfHeight);
      doc.save(`Report Summarization_${detailInfo.value.fileName}`);
    });
  });
}

const navPdfIndex = (i) => {
  // 如果pdfUrl中已经包含 #page=，则替换页码
  selectedTab.value = 1
  if (pdfUrl.value.includes('page=')) {
    pdfUrl.value = pdfUrl.value.replace(/page=\d+/, `page=${i}`);
  } else {
    // 如果没有 #page=，则直接添加
    pdfUrl.value += `page=${i}`;
  }
  
  // console.log(pdfUrl.value, 'pdfUrl.value');
  iframeKey.value += 1; // 强制更新 iframe
};
</script>

<template>
  <div class='logR-detail'>
    <div class="logR-detail-header" >
        <i class="pi pi-arrow-circle-left"  @click="navigateToPage" style="font-size: 22px;color:rgba(87,79,215,1);"/>
        <a-tooltip placement="rightTop" :title="detailInfo.fileName">
          <span 
            style="
              font-size: 18px;
              line-height: 18px;
              color: #444444;
              text-wrap: nowrap;
              letter-spacing: 0.24px;
              font-weight: 600;
              margin-left: 14px;
              overflow: hidden; 
              text-overflow: ellipsis;
              white-space: nowrap; 
              max-width: 600px; /* 设置最大宽度，可以根据需要调整 */
              display: inline-block;
            ">
            {{detailInfo.fileName}}
          </span>
        </a-tooltip>
    </div>

    <Splitter style="background: transparent;" class="logR-detail-content" :gutterSize="10">
      <SplitterPanel style="flex:2;padding-left:10px;">
        <div class="logR-tab">
          <p 
            v-for="(tab, index) in tabs" 
            :key="index" 
            :class="{'active': selectedTab === index}"
            @click="selectTab(index)"
          >
            {{ tab }}
          </p>
        </div>
        <div  class="logR-tab-content">
          <div class="logR-tab-content-summary" v-if = "selectedTab===0">
            <div class="logR-summary-header" > 
              <p>
                <a-tooltip placement="rightTop" :title="detailInfo.fileName">
                  <span 
                    style="
                      font-size: 14px;
                      line-height: 20px;
                      color: #444444;
                      text-wrap: nowrap;
                      letter-spacing: 0.12px;
                      font-weight: 600;
                      overflow: hidden; 
                      text-overflow: ellipsis;
                      white-space: nowrap; 
                      max-width: 200px; /* 设置最大宽度，可以根据需要调整 */
                      display: inline-block;
                      margin-top:9px;
                  ">
                    {{detailInfo.fileName}}
                  </span>
                </a-tooltip>
              </p>
              <p style="padding-top: 5px">
                <span style="font-size: 12px;font-weight: 400;">
                  Regenerate around 
                </span>
                <a-input-number style="background: rgba(87,79,215,0.07);border: 0.5px solid #BCD2FF;"  size="small" id="wordsNumber" v-model:value="words" :min="1" :max="3000" />
                <span style="font-size: 12px;font-weight: 400;">
                  words
                </span>
                <Button  style="height: 20px;margin-right:10px;font-size: 10px;" @click="submitWords" id="submitBtn">Submit</Button>
                <Button style="height: 20px;font-size: 10px;" @click="exportPdf" id="exportBtn">Export</Button>
              </p>
            </div>
            <div class="logR_summary_container">
              <p class="logR_summary_content" ref="logR_summary_content" id="logr-summary" dir="auto"  v-if="!spinning">
                <MarkdownRenderer :source="summaryText"></MarkdownRenderer>
                <div v-if="wordsNumber>0">Total: around {{wordsNumber}} words</div>
              </p>
              <div class="flex flex-column ml-4"  v-if="spinning">
                <Skeleton class="mb-2"></Skeleton>
                <Skeleton width="10rem" class="mb-2"></Skeleton>
                <Skeleton width="5rem" class="mb-2"></Skeleton>
                <Skeleton width="2rem" class="mb-2"></Skeleton>
              </div>
            </div>
          </div>
          <div class="logR-tab-content-file" v-if = "selectedTab===1">
            <a-tooltip placement="rightTop" :title="detailInfo.fileName">
              <p 
                style="
                  font-size: 14px;
                  color: #444444;
                  text-wrap: nowrap;
                  letter-spacing: 0.12px;
                  font-weight: 600;
                  overflow: hidden; 
                  text-overflow: ellipsis;
                  white-space: nowrap; 
                  max-width: 200px; /* 设置最大宽度，可以根据需要调整 */
                  display: inline-block;
                  margin-bottom:8px;
                  margin-top:-3px;
              ">
                {{detailInfo.fileName}}
            </p>
            </a-tooltip>
            <p class="logR-file-content" style="flex-grow: 1; overflow-y: auto;background: #fff;border-radius: 5px;">
              <iframe :src="pdfUrl" height="900px;" width="100%" :key="iframeKey"/>
            </p>
          </div>
        </div>
      </SplitterPanel>
      <SplitterPanel style="flex:1;" >
        <LongReportChat @changePage="navPdfIndex"/>
      </SplitterPanel>
    </Splitter>
  </div>
</template>

<style scoped>
.logR-detail {
  background-image: url('@/assets/IconRagContent.png');
  box-shadow: 0 0 5px 2px rgba(87,79,215,0.10);
  border-radius: 5px;
  /* height: 100%; */
  background-color: #fff;
  width: 100%;
  display: flex;
  flex-direction: column;
  /* padding-bottom: 12px; */
  height:calc(100vh - 93px);
}
.logR-detail-header{
  height:54px;
  border-bottom:1px solid rgba(64,129,255,0.35);
  display: flex;
  align-items: center;
  padding-left: 20px;
}

::v-deep .logR-detail-content .p-splitter-gutter {
  background: transparent;
}

.logR-tab {
  display: flex;
  margin-top:10px;
}

.logR-tab > p {
  font-size: 16px;
  letter-spacing: 0.14px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.3s;
  padding: 0 15px;
  border-bottom: 1px solid #e2e8f0;
}

.logR-tab > p:hover,
.logR-tab > p.active {
  color: #574FD7;
}

.logR-tab > p.active {
  border-bottom: 2px solid rgba(87,79,215,1);
  background: none;
}

.logR-tab-content{
  margin:12px 0 ;
  background-color: rgba(87,79,215,0.07);
  border-radius: 5px;
  height:calc(100vh - 206px);
}

.logR-tab-content-summary{
  padding:0 20px 0 16px;
  height:calc(100vh - 206px);

}

.logR-tab-content-summary .logR-summary-header{
  display: flex;
  justify-content: space-between;
}

.logR-tab-content-file{
  padding:12px 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.logR_summary_container{
  height:calc(100vh - 255px);
  position: relative;
  width: 100%;
  /* height: 100%; */
  overflow-y: auto;
}
.logR_summary_content{
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: auto; /* 确保子元素的高度根据内容自动调整 */
  overflow-y: auto; /* 子元素自身也可滚动 */
}
.logR-file-content{
  height:calc(100vh - 290px);
  overflow-y: scroll;
}

</style>
