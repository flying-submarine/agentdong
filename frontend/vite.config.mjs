import { defineConfig } from 'vite'   // defineConfig：vite 配置的入口函数
import vue from '@vitejs/plugin-vue'   // 让 vite 能编译 .vue 文件
import path from 'path'   // 拼路径用
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') }   // @ = src 目录，src 里大量 import 用的就是 @
  },
  server: {
    proxy: {
      '/api': 'https://agentdong.com'   // 开发模式：/api 开头的请求转给线上后端
    }
  }
})
