import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

import MyKnowledge from '../components/MyKnowledge.vue'
import MyMaterial from '../components/MyMaterial.vue'
import MaterialContent from '../components/MaterialContent.vue'
// import Chat from "@/components/Chat.vue";
import Chat from "@/views/ChatView.vue";
import News from "@/components/News.vue";
import NewsView from "@/views/NewsView.vue";
import RAG from "@/components/RAG.vue";
import Writing from "@/views/WritingView.vue";
import NewRagView from "@/views/NewRagView.vue";

import LongReportSummarization from "@/views/LongReportSummarizationView.vue";
import LongReportDetail from "@/components/LongReportDetail.vue";

// import Evaluation from '@/components/Evaluation.vue'
// import EvaluationResult from '@/components/EvaluationResult.vue'
import TableQA from '@/components/TableQA.vue'
import WelcomePage from '@/components/WelcomePage.vue'
import Evaluation from '@/views/EvaluationView.vue'
import Layout from '@/layout/Layout.vue'
import Register from '@/views/Register.vue'
import AccountManage from '@/views/AccountManage.vue'
import ModifyPassword from '@/views/ModifyPasswordView.vue'

const allRoutes = [
  {
    path: '/welcome',
    name: 'welcome',
    component: WelcomePage,
  },
  {
    path: '/login',
    redirect: '/welcome',
  },
  {
    path: '/register',
    name: 'register',
    component: Register,
  },
  {
    path: '/modifyPassword',
    name: 'Modify password',
    component: ModifyPassword,
  },
  {
    path: '/bussiness',
    component: Layout,
    children: [
      {
        path: '/bussiness/MyMaterial',
        name: 'My Material',
        component: MyMaterial,
      },
      {
        path: '/MaterialContent',
        name: 'MaterialContent',
        component: MaterialContent,
      },
      {
        path: '/image',
        name: 'My Knowledge',
        component: MyKnowledge,
      },
      {
        path: '/bussiness/Chat',
        name: 'Chat',
        component: Chat,
      },
      {
        path: '/bussiness/Newsletter',
        name: 'Newsletter',
        component: NewsView,
      },
      {
        path: '/bussiness/Chat-With-RAG',
        name: 'Chat with RAG',
        component: NewRagView,
      },
      {
        path: '/bussiness/LongReportSummarization',
        name: 'Long Report Summarization',
        component: LongReportSummarization,
      },
      {
        path: '/bussiness/LongReportSummarization/:docId/:ssid',
        name: 'Long Report Detail',
        component: LongReportDetail,
      },
      {
        path: '/bussiness/Writting_Assistant',
        name: 'Writting Assistant',
        component: Writing,
      },
      {
        path: '/bussiness/Chat_BI',
        name: 'Chat BI',
        component: TableQA,
      },
      {
        path: '/bussiness/Evaluation',
        name: 'Evaluation',
        component: Evaluation,
      },
      {
        path: '/bussiness/AccountManage',
        name: 'AccountManage',
        component: AccountManage,
      },
    ]
  },
  {
    path: '/',
    redirect: '/welcome'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: allRoutes
})

export default router
