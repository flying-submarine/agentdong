import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue';
import CKEditor from '@ckeditor/ckeditor5-vue';
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import 'liux-components/dist/style.css'

import PrimeVue from "primevue/config";
import Button from "primevue/button";
import Checkbox from "primevue/checkbox";
import Textarea from "primevue/textarea";
import Avatar from "primevue/avatar";
// import Dropdown from "primevue/dropdown";
import Select from "primevue/select";
import ProgressBar from "primevue/progressbar";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Password from 'primevue/password';
import Skeleton from "primevue/skeleton";
import Divider from 'primevue/divider';
import SelectButton from 'primevue/selectbutton';
import TreeSelect from 'primevue/treeselect';
import ToggleSwitch from 'primevue/toggleswitch';
import Tooltip from 'primevue/tooltip';
import Card from 'primevue/card';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import DatePicker from 'primevue/datepicker';
import ToastService from 'primevue/toastservice';
import ConfirmationService from 'primevue/confirmationservice';

import "primeflex/primeflex.css";
import "primeicons/primeicons.css";
import MyPreset from './style.js'


import Ripple from 'primevue/ripple';

import router from './router'

const app = createApp(App)

app.use(CKEditor)
app.use(PrimeVue, {
    theme: {
        preset: MyPreset
    },
    ripple: true,
});
app.directive('ripple', Ripple);
app.use(createPinia())
app.use(router)
app.use(Antd)
app.use(ToastService)
app.use(ConfirmationService)
app.use(ElementPlus)

app.component("Checkbox", Checkbox);
app.component("Button", Button);
app.component("Textarea", Textarea);
app.component("Avatar", Avatar);
// app.component("Dropdown", Dropdown);
app.component("Dropdown", Select);
app.component("Select", Select);
app.component("ProgressBar", ProgressBar);
app.component("Dialog", Dialog);
app.component("InputText", InputText);
app.component("Skeleton", Skeleton);
app.component("SelectButton", SelectButton);
app.component("TreeSelect", TreeSelect);
app.component("ToggleSwitch", ToggleSwitch);
app.component("Tooltip", Tooltip);
app.directive('tooltip', Tooltip);
app.component("Card", Card);
app.component("Divider", Divider);
app.component("Password", Password);
app.component("Tabs", Tabs);
app.component("TabList", TabList);
app.component("Tab", Tab);
app.component("TabPanel", TabPanel);
app.component("TabPanels", TabPanels);
app.component("DatePicker", DatePicker);


// app.directive('click-outside', {
//     beforeMount(el, binding, vnode) {
//       const ourClickEventHandler = event => {
//         if (!el.contains(event.target) && el !== event.target) {
//           // This is a click outside, call provided function
//           binding.value(event); // binding.value is the function provided as the expression
//         }
//       };
//       // Attach our event listener
//       el.__vueClickOutside__ = ourClickEventHandler;
//       document.addEventListener('click', ourClickEventHandler);
//     },
//     beforeUnmount(el) {
//       // Remove our event listener
//       document.removeEventListener('click', el.__vueClickOutside__);
//     },
//   });


app.mount('#app')
