<template>
  <div>
    <div>
      <input type="number" v-model="pageNumber" @input="goToPage" min="1" :max="totalPages" />
      <span> / {{ totalPages }}</span>
    </div>
    <canvas ref="pdfCanvas"></canvas>
  </div>
</template>

<script setup>
import * as pdfjsLib from 'pdfjs-dist';
import { ref, onMounted } from 'vue';

pdfjsLib.GlobalWorkerOptions.workerSrc = "pdfjs-dist/build/pdf.worker.js";
// Set up the PDF.js worker

const pdfDoc = ref(null);
const pageNumber = ref(1);
const totalPages = ref(0);
const pdfCanvas = ref(null);

const loadPdf = async (url) => {
  try {
    pdfDoc.value = await pdfjsLib.getDocument(url).promise;
    totalPages.value = pdfDoc.value.numPages;
    renderPage(pageNumber.value);
  } catch (error) {
    console.error('Error loading PDF:', error);
  }
};

const renderPage = async (pageNumber) => {
  try {
    const page = await pdfDoc.value.getPage(pageNumber);
    const viewport = page.getViewport({ scale: 1.5 });
    const canvas = pdfCanvas.value;
    const context = canvas.getContext('2d');

    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
      canvasContext: context,
      viewport: viewport,
    };
    await page.render(renderContext).promise;
  } catch (error) {
    console.error('Error rendering page:', error);
  }
};

const goToPage = () => {
  if (pageNumber.value >= 1 && pageNumber.value <= totalPages.value) {
    renderPage(pageNumber.value);
  }
};

onMounted(() => {
  const pdfUrl = 'http://city-brain-vendor.oss-cn-hangzhou.aliyuncs.com/tqms-data%2Fsaudi%2Fapp%2Flong_report_service%2Fadmin%40alibaba-inc.com%2F6ff97725-f17c-40c7-88f1-8fa79966cf30%2F2024.pdf?OSSAccessKeyId=LTAI5tJMfxXxTwbyW8xF6mjS&Expires=1724915265&Signature=vZZKMYMlZ3Xr4EnpZJuKScyIFB8%3D';
  loadPdf(pdfUrl);
});
</script>
