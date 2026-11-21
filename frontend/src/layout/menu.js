
import chat_svg from '@/assets/chat.svg'
import news_svg from '@/assets/news.svg'
import database from '@/assets/database.svg'
import writing_svg from '@/assets/writing.svg'
import longText_svg from '@/assets/longText.svg'
import star from '@/assets/star.svg'

const APP_MODE = 'dev';

export const menuList = [
  {
    path: '/bussiness/MyMaterial',
    icon: '🏆',
    name: 'My Material',
    menu: false,
  },
  // {
  //     path: '/TestPage',
  //     name: 'TestPage',
  //     component: TestPage,
  //     menu: false,
  // },
  {
    path: '/bussiness/MaterialContent',
    name: 'MaterialContent',
    icon: '📚',
    menu: false,
  },
  {
    path: '/bussiness/image',
    icon: '📚',
    name: 'My Knowledge',
    menu: false,
  },
  {
    path: '/bussiness/Chat',
    icon: chat_svg,
    name: 'Chat',
    menu: false,
    class: "chat-menu"
  },
  {
    path: '/bussiness/Newsletter',
    icon: news_svg,
    name: '资讯简报',
    menu: true,
    class: "news-menu"
  },
  {
    path: '/bussiness/Chat-With-RAG',
    icon: database,
    name: '知识库问答',
    menu: true,
    class: "chat-rag-menu",
  },
  {
    path: '/bussiness/LongReportSummarization',
    icon: longText_svg,
    name: '长文摘要',
    menu: true,
    class: "long-report-menu"
  },
  {
    path: '/bussiness/LongReportSummarization/:docId/:ssid',
    name: 'Long Report Detail',
    menu: false,
    class: "long-report-menu"
  },
  {
    path: '/bussiness/Writting_Assistant',
    icon: writing_svg,
    name: 'Writting Assistant',
    menu: false,
    class: 'writting-menu'
  },
  {
    path: '/bussiness/Chat_BI',
    icon: star,
    name: 'Chat BI',
    menu: false,
    class: 'bi-menu'
  },
  {
    path: '/bussiness/Evaluation',
    icon: star,
    name: 'Evaluation',
    menu: false,
    class: "evaluation-menu"
  },
]
