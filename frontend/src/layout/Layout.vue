<template>
  <div class="app-shell">
    <header class="app-header">
      <img :src="LogoImg" class="app-logo" alt="Wakeb GPT" />
      <span class="app-tagline">企业知识库问答</span>
      <div class="app-header-spacer"></div>
      <span class="app-header-user">
        <span class="user-dot">{{ (username || 'U').charAt(0).toUpperCase() }}</span>
        {{ username }}
      </span>
    </header>

    <div class="app-body">
      <aside class="app-sidebar">
        <nav class="side-nav">
          <router-link
            v-for="item in items"
            :key="item.url"
            v-slot="{ navigate }"
            :to="item.url"
            custom
          >
            <a
              class="side-nav-item"
              :class="getActive(item.url)"
              href="javascript:void(0)"
              @click="handleNavigation(navigate)"
            >
              <img :src="getImage(item.url)" class="side-nav-icon" alt="" />
              <span class="side-nav-label">{{ item.label }}</span>
            </a>
          </router-link>
        </nav>

        <div class="side-footer">
          <router-link v-if="isAdmin" v-slot="{ navigate }" to="/bussiness/AccountManage" custom>
            <a
              href="javascript:void(0)"
              class="side-nav-item account-item"
              :class="getActive('/bussiness/AccountManage')"
              @click.prevent="handleNavigation(navigate)"
            >
              <img :src="getImage('/bussiness/AccountManage')" class="side-nav-icon" alt="" />
              <span class="side-nav-label">Account Management</span>
            </a>
          </router-link>
          <button class="logout-btn" @click="logout">
            <i class="pi pi-sign-out"></i>
            <span>退出登录</span>
          </button>
        </div>
      </aside>

      <main class="app-main">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, toRefs, computed, watch } from "vue";
import { useUserStore, useRoleLoginList } from "@/stores/user";
import { useTokenStore } from "@/stores/token";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import Menu from "primevue/menu";
import { menuList } from './menu';
import { useRouter } from 'vue-router';
import { useGeneratStore } from "@/stores/generat";
import { message } from 'ant-design-vue';

import NewsLetterIcon from '@/assets/newsletter_icon.png';
import NewsLetterIconActive from '@/assets/newsletter_icon_active.png';

import ChatRagIcon from '@/assets/chatRag_icon.png';
import ChatRagIconActive from '@/assets/chatRag_icon_active.png';

import LongReportSummarizationIcon from '@/assets/longReportSummarization_icon.png';
import LongReportSummarizationIconActive from '@/assets/longReportSummarization_icon_active.png';
import { serviceFetch } from '@/service/utils';
import AccountIcon from '@/assets/account_icon.png';
import LogoImg from '@/assets/logo_wakeb_white.png';

const use_router = useRouter();
const currentRouter = ref(use_router.currentRoute);
const store = useUserStore();
const generating = useGeneratStore()
const tokenStore = useTokenStore();
const roleLoginListStore = useRoleLoginList();
const username = ref('')
const roleList = ref([])
const change_user_name = (e) => {
  store.setUser(username.value)
  console.log('change user name', username.value)
}
const getActive = (url)=>{
  const path = currentRouter.value.path;
  if(path == url ){
    return 'active-menu'
  } else {
    return ''
  }
}

const isAdmin = computed(() => {
  let flag = false;
  roleList.value.map(x=>{
    if(x.role === 'ADMIN'){
      flag = true;
    }
  })
  return flag
})



const getImage = (url)=>{
  const path = currentRouter.value.path;
  switch(url) {
    case '/bussiness/Newsletter': 
      if(url===path){
        return NewsLetterIconActive;
      } else {
        return NewsLetterIcon;
      }
    case '/bussiness/Chat-With-RAG':
    if(url===path){
        return ChatRagIconActive;
      } else {
        return ChatRagIcon;
      }
    case '/bussiness/LongReportSummarization':
    if(url===path){
        return LongReportSummarizationIconActive;
      } else {
        return LongReportSummarizationIcon;
      }
    case '/bussiness/AccountManage': 
      if(url===path){
        return AccountIcon;
      } else {
        return AccountIcon;
      }
  }
}
const items = ref([]);
items.value = menuList.filter(x => x.menu).map(x => {
  return { icon: x.icon, label: x.name, url: x.path, menu: x.menu }
})
const collapsed = ref(false);
const logout = async ()=>{
  if(generating.status) return message.warn('Generating, please do not switch!')
  const res = await serviceFetch('/gpt/user/logout', {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      }
  });
  const response =await res.json();
  if(response.code ===200) {
    const firstVisit = localStorage.getItem('firstVisit')||'';
    localStorage.clear();
    localStorage.setItem('firstVisit', firstVisit);

    use_router.push('/login');
  }
}

const handleNavigation = (navigate)=>{
  console.log(generating.status,'generating.status')
  if (generating.status) {
    message.warn('Generating, please do not switch!');
    return;
  }
  navigate();
}

const initInfo = ()=>{
  const useUsername = localStorage.getItem('useUsername')||'';
  const useToken = localStorage.getItem('useToken')||'';
  const roleLoginListStr = localStorage.getItem('roleLoginVOList')||'[]';
  const roleLoginList = JSON.parse(roleLoginListStr);
  tokenStore.setToken(useToken);
  store.setUser(useUsername)
  roleLoginListStore.setRoleLoginList(roleLoginList);
  roleList.value = roleLoginList;
  username.value = useUsername;
}
initInfo();
</script>
<style>
/* ---------------- 应用外壳 ---------------- */
.app-shell {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--app-bg);
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 30;
  height: 60px;
  flex: 0 0 60px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 24px;
  background: #111827;
  color: #fff;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06);
}
.app-logo {
  height: 22px;
  width: auto;
}
.app-tagline {
  font-size: 12px;
  color: #9ca3af;
  padding-left: 14px;
  border-left: 1px solid rgba(255, 255, 255, 0.18);
  letter-spacing: 0.02em;
}
.app-header-spacer {
  flex: 1;
}
.app-header-user {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13px;
  color: #e5e7eb;
}
.user-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--app-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
}

/* ---------------- 主体 ---------------- */
.app-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.app-sidebar {
  width: 216px;
  flex: 0 0 216px;
  background: var(--app-surface);
  border-right: 1px solid var(--app-border);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 18px 12px 16px;
  min-height: calc(100vh - 60px);
}

.side-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.side-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 42px;
  padding: 10px 12px;
  border-radius: var(--app-radius-sm);
  color: var(--app-text-2);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
  position: relative;
}
.side-nav-item:hover {
  background: var(--app-surface-3);
  color: var(--app-text);
}
.side-nav-item.active-menu {
  background: var(--app-primary-soft);
  color: var(--app-primary);
  font-weight: 600;
}
.side-nav-item.active-menu::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 10px;
  bottom: 10px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--app-primary);
}
.side-nav-icon {
  width: 20px;
  height: 20px;
  flex: 0 0 20px;
  object-fit: contain;
}
.side-nav-label {
  flex: 1;
  line-height: 1.35;
}

.side-footer {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 14px;
  border-top: 1px solid var(--app-border);
}
.account-item {
  color: var(--app-text-2);
}
.logout-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-height: 42px;
  padding: 10px 12px;
  margin-top: 2px;
  border: 0;
  border-radius: var(--app-radius-sm);
  background: transparent;
  color: var(--app-text-3);
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.logout-btn:hover {
  background: #fef3f2;
  color: var(--app-danger);
}

.app-main {
  flex: 1;
  min-width: 0;
  min-height: calc(100vh - 60px);
  padding: 20px;
  background: var(--app-bg);
  overflow: auto;
}

/* 兼容旧样式引用 */
.custom-menu { display: none; }
.p-datatable-filter-constraint-dropdown {
  display: none !important;
}
.compact-table .p-datatable-tbody > tr > td {
  padding: 6px 10px;
  font-size: 13px;
}
</style>

<!-- <script setup>
import { RouterLink, RouterView } from 'vue-router'
import HelloWorld from './components/HelloWorld.vue'
</script>

<template>
  <header>
    <img alt="Vue logo" class="logo" src="@/assets/logo.svg" width="125" height="125" />

    <div class="wrapper">
      <HelloWorld msg="You did it!" />

      <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
}
</style> -->
