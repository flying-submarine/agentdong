<template>
  <Splitter style="width: 100%;border: none;background: #D9D4FC;" :gutterSize="0" layout="vertical">
    <SplitterPanel style="max-height: 50px; min-height: 50px;">  
      <div class="header" style="height: 50px;line-height: 50px;font-size: 30px;color: #fff">
        <img :src="LogoImg" style="margin-left: 11px;height:24px"/>
      </div>
    </SplitterPanel>
    <SplitterPanel>
      <Splitter :gutterSize="0">
        <SplitterPanel style="max-width: 200px; min-width: 200px;">
          <!-- <div v-show="!collapsed" class="sidebar-header">
            <img src="@/assets/qianwen.png" alt="logo">
            Wakeb GPT
          </div> -->
          <div class="left-spliter" style="display: flex;flex-direction: column; justify-content: space-between;">
            <Menu class="custom-menu" :model="items" :baseZIndex="0">
              <template #item="{ item, props }" >
                <router-link v-if="item.menu" v-slot="{ href, navigate }" :to="item.url" custom>
                  <a  v-bind="props.action" @click="handleNavigation(navigate)"  :class="getActive(item.url)">
                    <img :src="getImage(item.url)" style="height: 16px; flex-shrink: 0;margin-top: 4px" alt="logo">
                    <span class="ml-2">{{ item.label }}</span>
                  </a>
                </router-link>
              </template>
            </Menu>
            <div class="menu-footer">
              <div style="display:flex">
                <img src="@/assets/admin_icon.png" style="height: 18px;" alt="logo">
                <!-- <input style="width: 60px;" v-model="username" @change="change_user_name" /> -->
                <span style="margin-left: 9px;">{{username}}</span>
                <span style="margin-left: 25px;cursor: pointer;" @click="logout">Logout</span>
              </div>
              <div style="margin-top: 22px" v-if="isAdmin">
                <router-link v-slot="{ href, navigate }" to="/bussiness/AccountManage" custom>
                  <a  @click.prevent="handleNavigation(navigate)"  class="account-item" :class="getActive('/bussiness/AccountManage')">
                    <img :src="getImage('/bussiness/AccountManage')" style="height: 18px; flex-shrink: 0;" alt="logo">
                    <div class="account ml-2">Account Management</div>
                  </a>
                </router-link>
              </div>
            </div>
          </div>
        </SplitterPanel>
        <SplitterPanel class="center-bg">
          <router-view></router-view>
        </SplitterPanel>
      </Splitter>
    </SplitterPanel>
  </Splitter>
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
/* @import './base.css'; */
.header {
  position: fixed;
  left: 0;
  top: 0;
  width: 100%;
  height: 50px;
  background: url('../assets/headerBg.png');
  z-index: 20;
}
.left-spliter {
  position: fixed;
  left: 0;
  top: 50px;
  max-width: 200px;
  min-width: 200px;
  background: url('../assets/leftBg.png');
  height: calc(100vh - 50px);
  box-shadow: 0 0 20px 5px rgba(14,66,210,0.25);
  z-index: 8;
  .active-menu {
    color: var(--p-primary-500);
  }
}
.menu-footer {
  position: relative;
  bottom: 24px;
  left: 13px;
  font-size: 14px;
  .account-item {
    color: rgb(51, 65, 85);
    font-size: var(--menu-font-size);
    font-weight: 600;
    padding: 0;
    &:hover {
      background: transparent;
    }
    &.active-menu {
      color: var(--p-primary-500);
    }
    .account {
      display: inline-block;
      vertical-align: middle;
      margin-top: -8px;
      font-weight: 600;
      font-size: 14px;
    }
  }
}
.custom-menu {
  border: none !important; 
  font-size: var(--menu-font-size);
  font-weight: 600;
  background: transparent !important;
  --p-menu-item-focus-color: #8b5cf6;
  .p-menu-list {
    padding: 0;
  }
}

.p-menu-item-link {
  background-color: var(--surface-0);
  color: var(--text-color);
  transition: background-color 0.3s, color 0.3s;
  margin: 0 34px 0 13px;
  padding: 22px 0 22px 0 !important;
  border-bottom: 0.5px solid rgba(151,151,151,0.6);
  align-items: start !important;
  line-height: 22px;
  letter-spacing: 0.14px;
}
.p-menu-item.p-focus .p-menu-item-content {
  background-color: transparent !important;
}
.p-menu-item:not(.p-disabled) .p-menu-item-content:hover {
  background-color: transparent !important;
  color: var(--p-menu-item-focus-background);
}
/* 更改 hover 和选中状态的颜色 */
.p-menu-item-link:hover,
.p-menu-item-link:active,
.p-menu-item-link-active {
  background-color: var(--primary-color) !important;
  color: var(--primary-color-text) !important;
}

.p-panelmenu {
  gap: 0 !important;
}

.p-panelmenu-panel {
  border: none !important;
  ;
}

/* .p-panelmenu-header-content:hover,
.p-panelmenu-item-content:hover {
  background-color: rgb(223, 203, 203) !important;
} */

body {
  display: flex;
  place-items: center;
}

#app {
  margin: 0 auto;
  font-weight: normal;
  min-height: calc(100vh - 16px);
  width: 100%;
  display: flex;
}

main {
  width: 100%;
  min-height: calc(100vh - 16px);
}

a,
.green {
  text-decoration: none;
  color: hsla(160, 100%, 37%, 1);
  transition: 0.4s;
  padding: 3px;
}

.center-bg {
  background: #D9D4FC;
  background-size: cover;
  padding: 21px 15px;
}

@media (hover: hover) {
  a:hover {
    background-color: hsla(160, 100%, 37%, 0.2);
  }
}

.p-datatable-filter-constraint-dropdown {
  display: none !important;
}

.sidebar-header {
  display: flex;
  align-items: center;
  padding: 20px;
  font-weight: bold;
  color: #007bfc;
}

.sidebar-header img {
  width: 30px;
  height: 30px;
  margin-right: 10px;
}

#components-layout-demo-custom-trigger .trigger {
  font-size: 12px;
  line-height: 64px;
  padding: 0 24px;
  cursor: pointer;
  transition: color 0.3s;
}

#components-layout-demo-custom-trigger .trigger:hover {
  color: #1890ff;
}

#components-layout-demo-custom-trigger .logo {
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  margin: 16px;
}


.compact-table .p-datatable-tbody>tr>td {
  padding: 4px 8px;
  font-size: 12px;
}

.compact-table .p-datatable-tbody>tr {
  height: 24px;
}

.menu-item-text {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  /* ���߲������������ */

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
