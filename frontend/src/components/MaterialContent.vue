<template>
  <div class="context-all">
    <div class="sidebar">
    </div>
    <div class="text-editor">
      <ckeditor :editor="editor" v-model="editorData" :config="editorConfig"></ckeditor>
    </div>
    <div class="chatbot" @click="to_chat_box">
      <img src="@/assets/qianwen.png" alt="logo">
      <div class="chatbot-title">
        Hi I'm your Olympic GPT Copilot, any questions?
      </div>
    </div>
  </div>
</template>

<script>
// import CKEditor from '@ckeditor/ckeditor5-vue';
import ClassicEditor from '@ckeditor/ckeditor5-build-classic';
export default {
  name: 'MaterialContent',
  data() {
    return {
      editor: ClassicEditor,
      editorData: '<p>Type your content here.</p>',
      editorConfig: {
        // 自定义配置
        toolbar: ['heading', '|', 'bold', 'italic', 'link', 'bulletedList', 'numberedList', 'blockQuote'],
        // 你可以在这里添加更多的配置选项
      }
    }
  },
  mounted() {
    console.log("MaterialContent mounted")
  },
  methods: {
    to_chat_box() {
      this.$router.push({ name: 'Chat', params: { userId: '123' } })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

.chatbot {
  position: fixed;
  right: 30px;
  bottom: 30px;
  width: 216px;
  display: flex;
  grid-gap: 10px;
  gap: 10px;
  align-items: center;
  justify-content: center;
  padding: 16px 12px;
  border: 1px solid #e7e9e8;
  border-radius: 16px;
  box-shadow: 0 4px 8px -4px rgba(0, 0, 0, .13), 0 6px 16px 0 rgba(0, 0, 0, .08), 0 12px 24px 16px rgba(0, 0, 0, .04);
  cursor: pointer;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  background-color: #fff;
  line-height: 1;
}

@keyframes autoRotate___1yRJT {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(1turn);
  }
}

.chatbot img {

  height: 62px;
  transform: translateZ(0);
  animation: autoRotate___1yRJT 3s ease .5s infinite backwards;
  vertical-align: middle;
  border-style: none;
  overflow-clip-margin: content-box;
  overflow: clip;
}

.chatbot-title {
  line-height: 1.2;
  font-size: 18px;
  font-weight: 700;
  font-family: Consol, Arial, PingFang SC, Microsoft YaHei;
  color: #6556ee;

}

.context-all {
  font-family: Arial, sans-serif;
  display: flex;
  height: 100vh;
  /* background-color: #f5f5f5; */
}
</style>
