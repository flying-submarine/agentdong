<template>
  <router-view></router-view>
</template>
<style>
.p-popover  .pi-info-circle{
    /* background: red; */
    color:rgba(39,38,54,0.6)!important;
}
.p-popover .p-button-danger{
  background: var(--app-primary)!important;
  border-radius: 8px!important;
  border:none!important;
}
.p-popover .p-button-danger:hover{
  background: var(--app-primary-hover)!important;
  border-radius: 8px!important;
  border:none!important;
}
.p-popover .p-button-secondary{
  border: 0.4px solid rgba(52, 41, 68, 0.5)!important;
  border-radius: 2px!important;
  opacity: 0.5!important;
}

.ant-message{
  z-index:1999;
}
.ant-upload-list-item-actions{
  display:none;
}
.logR-message-content{
  min-width:400px;
}
.logR-message-content a:hover{
  background-color: transparent;
  color: var(--app-primary-hover)!important;
}
.ragH_p .p-dialog-header .p-dialog-header-actions{
  display: none;
}
.ragH_p .p-dialog-footer .p-button-danger{
  background:var(--app-primary)!important; 
  border-color:var(--app-primary)!important;
}
.ragH_p .p-dialog-footer .p-button-danger:hover{
  background:var(--app-primary-hover)!important; 
  border-color:var(--app-primary-hover)!important;
}

.longR-Dialog .p-dialog-header-actions{
  /* display:none!important; */
}
</style>
