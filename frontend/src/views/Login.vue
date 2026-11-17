<template>
  <Splitter style="width: 100%;border: none" :gutterSize="0" layout="vertical">
    <SplitterPanel style="max-height: 50px; min-height: 50px;">  
      <div class="headerBg"><img :src="LogoImg" style="margin-left: 11px;height:24px"/></div>
    </SplitterPanel>
    <SplitterPanel>
      <Splitter class="bg" style="width: 100%;border: none" :gutterSize="0" layout="horizontal">
        <SplitterPanel class="left-login">
          <div class="login-form">
            <div class="title">Hello, Please Login</div>
              <a-form
                ref="formRef"
                :model="loginInfo"
                :rules="rules"
                layout="vertical"
              >
                <a-form-item class="input-label" :required="false" style="position: absolute;opacity: 0;">
                  <a-input :maxlength="120" class="input-user" hidden placeholder="Email" v-model:value="loginInfo.email" />
                </a-form-item>
                <a-form-item class="input-label" name="email" :required="false">
                  <a-input :maxlength="120" class="input-user" placeholder="Email" v-model:value="loginInfo.email" autocomplete="off"/>
                </a-form-item>
                <a-form-item class="input-label" style="position: absolute;opacity: 0;">
                  <a-input-password style="background: #EFEEFD;color: #9B76B0;height: 45px;width:355px"  :visibilityToggle="true" :maxlength="20" class="input-newpassword" placeholder="Password" v-model:value="loginInfo.password" autocomplete="off"/>
                </a-form-item>
                <a-form-item class="input-label" name="password">
                  <a-input-password style="background: #EFEEFD;color: #9B76B0;height: 45px;width:355px"  :visibilityToggle="true" :maxlength="20" class="input-newpassword" placeholder="Password" v-model:value="loginInfo.password" autocomplete="off"/>
                </a-form-item>
              </a-form>
              <div class="operator-link">
                <a href="javascript:void(0)" @click="sendEmail">Forgot Password?</a>
              </div>
            <div>
              <Button class="login-submit" @click="login" @keyup.enter="login">Login</Button>
            </div>
            <!-- <div style="display: flex;" class="operator-link">
              <a href="javascript:void(0)" @click="sendEmail">Forgot Password</a>
            </div> -->
          </div>
          <Dialog class="dialog-email" position="top" :visible="visible" modal :showHeader="false" :style="{ width: '523px' }">
            <div class="tip-content">
              <img :src="TipIcon" style="height: 37.5px"/>
              <div class="tip-text">The password reset link has been sent to {{loginInfo.email}}, please click and reset your password on the link page.
              </div>
            </div>
            <!-- <div class="close-time" style="text-align: center;">5</div> -->
        </Dialog>
        </SplitterPanel>
        <SplitterPanel>
          <!-- <img src="@/assets/loginBg.png" style="width: 100%;" alt="bg"> -->
        </SplitterPanel>
      </Splitter>
    </SplitterPanel>
  </Splitter>
</template>
<script setup lang="ts">
  import { ref, onMounted, onUnmounted } from "vue";
  import { useRouter } from 'vue-router';
  import Splitter from "primevue/splitter";
  import SplitterPanel from "primevue/splitterpanel";
  import Dialog from 'primevue/dialog';
  import { message } from 'ant-design-vue';
  import TipIcon from '@/assets/tip_icon.png';
  import LogoImg from '@/assets/logo_wakeb_white.png';

  const use_router = useRouter();
  const loginInfo = ref({
    email: '',
    password: ''
  })
  const formRef = ref();
  const emailInfo = ref({email: ''});
  const rules = {
    email: [
      { type: 'email', message: 'Please input correct email address', trigger: ['blur'] },
      { required: true, message: 'Please input email address', trigger: 'blur' },
    ],
  };

  const visible = ref(false)

  const sendEmail = async ()=>{
    try {
       await formRef.value.validate(['email']);
    } catch (error) {
      return;
    }
    const res =await fetch('/gpt/email/forget/password',{
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: loginInfo.value.email,
      }),
    }
    );
    const response = await res.json();
    if(response.code===200) {
      visible.value=true;
      setTimeout(() => {
        visible.value=false;
      }, 5000);
    } else {
      message.error(response.message);
    }
  }

  const loginUser = async (info)=>{
    const response = await fetch('/gpt/user/login',{
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...info
      }),
    })
    const res = await response.json()
    return res
  }

  const openDialog = ()=>{
    visible.value = true;
  }

  const login = async ()=>{
    try {
      await formRef.value.validate();
    } catch (e) {
      return ;
    }
    const info=loginInfo.value;

    const data =await loginUser(info);
    if(data.code===200) {
      localStorage.setItem('useUsername', data.data.username);
      localStorage.setItem('useToken', data.data.token);
      localStorage.setItem('roleLoginVOList', JSON.stringify(data.data.roleLoginVOList));
      use_router.push('/bussiness/Newsletter');
    } else {
      message.error(data.message);
    }
  }

  const loginEnter = (e)=>{
    if(e.key === "Enter") {
      login();
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', loginEnter);
    const firstVisit=localStorage.getItem('firstVisit');
    if(firstVisit!=='inited'){
      use_router.push('/welcome')
    }
  
  });

  onUnmounted(()=>{
    document.removeEventListener('keydown', loginEnter);
  })


</script>
<style>
  .headerBg {
    height: 50px;
    line-height: 50px;
    font-size: 30px;
    color: #fff;
    background: url('../assets/headerBg.png');
    background-size: cover;
  }
  .left-login {
    display:flex;
    justify-content: center;
    align-items: center;
    max-width: 420px; 
    min-width: 420px;
    background: url('../assets/textBg.png');
    background-size: cover;
    box-shadow: 0 0 20px 5px rgba(81,13,143,0.20);
    min-height: calc(100vh - 50px);
  }
  .bg {
    background: url('../assets/loginBg.png') !important;
    background-size: cover !important;
  }
  .login-form {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    .title {
      text-align: center;
      color: #fff;
      font-size: 30px;
    }
    .input-user {
      margin-top: 37px;
      width: 355px;
      height: 45px;
      color: #9B76B0;
      background: rgba(255,255,255, 0.85);
      &:enabled:hover {
        border-color: rgba(188,210,255,1);
      }
      &::-webkit-input-placeholder { /* Chrome, Opera, Safari */
        color: #9B76B0;
      }
      
      &:-moz-placeholder { /* Firefox 18- */
        color: #9B76B0;;
      }
      
      &::-moz-placeholder { /* Firefox 19+ */
        color: #9B76B0;;
      }
      
      &:-ms-input-placeholder { /* Internet Explorer 10-11 */
        color: #9B76B0;
      }
    }
    .input-newpassword {
      & .ant-input {
        background: #EFEEFD!important;
        color: rgb(155, 118, 176);
        &::-webkit-input-placeholder { /* Chrome, Opera, Safari */
          color: #9B76B0;
        }
        
        &:-moz-placeholder { /* Firefox 18- */
          color: #9B76B0;;
        }
        
        &::-moz-placeholder { /* Firefox 19+ */
          color: #9B76B0;;
        }
        
        &:-ms-input-placeholder { /* Internet Explorer 10-11 */
          color: #9B76B0;
        }
      }
    }
    & .ant-form-item .ant-form-item-label >label.ant-form-item-required:not(.ant-form-item-required-mark-optional)::before {
      color: #fff;
    }
    & .ant-form-item .ant-form-item-explain-error {
      color: #fff;
      font-size: 16px;
    }
    .input-password {
      margin-top: 20px;
      width: 355px;
      height: 45px;
      color: #9B76B0;
      background: rgba(255,255,255, 0.85);
      &:enabled:hover {
        border-color: rgba(188,210,255,1);
      }
      &::-webkit-input-placeholder { /* Chrome, Opera, Safari */
        color: #9B76B0;
      }
      
      &:-moz-placeholder { /* Firefox 18- */
        color: #9B76B0;
      }
      
      &::-moz-placeholder { /* Firefox 19+ */
        color: #9B76B0;;
      }
      
      &:-ms-input-placeholder { /* Internet Explorer 10-11 */
        color: #9B76B0;
      }
    }
    .login-submit {
      margin-top: 28px;
      height: 56px;
      width: 355px;
      line-height: 56px;
      font-size: 24px;
      background: linear-gradient(180deg, #CB7FF2 0%, #686AF6 100%);
      box-shadow: 0 4px 11px 5px rgba(50,45,146,0.15);
      border-radius: 5px;
    }
    .operator-link {
      position: absolute;
      bottom: 88px;
      left: 0px;
      a {
        font-size: 12px;
        color: rgba(188,210,255,1);
        letter-spacing: 0.17px;
        text-align: center;
        &:hover {
          background: transparent;
        }
      }
    }
  }
  .dialog-email {
     .p-dialog-header {
      padding: 12px 12px 0 12px;
     }
     .p-dialog-content {
      padding: 0;
     }
     .p-dialog-title {
      font-size: 16px;
     }
     .tip-content {
      padding: 15px 24px;
      display: flex;
     }
     .tip-text {
      margin-left: 14px;
      font-size: 14px;
      color: #444;
      font-weight: 500;
      color: #444444;
      letter-spacing: 0.12px;
      line-height: 20px;
     }
     .close-time {
      margin: 0 auto;
      border-radius: 40px;
      border: 1px solid rgba(188,210,255,1);
      line-height: 40px;
      width: 40px;
      height: 40px;
     }
  }

  input:-webkit-autofill {
    transition: background-color 5000s ease-in-out 0s;
  }
  input:-webkit-autofill:hover {
    transition: background-color 5000s ease-in-out 0s;
  }
  input:-webkit-autofill:focus {
    transition: background-color 5000s ease-in-out 0s;
  }
  input:-webkit-autofill:active {
    transition: background-color 5000s ease-in-out 0s;
  }
  input:-internal-autofill-selected {
    transition: background-color 5000s ease-in-out 0s;
  }
</style>
