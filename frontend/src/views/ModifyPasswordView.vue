<template>
  <Splitter style="width: 100%;border: none" :gutterSize="0" layout="vertical">
    <SplitterPanel style="max-height: 60px; min-height: 60px;">  
      <div class="headerBg"><img :src="LogoImg" style="margin-left: 11px;height:24px"/></div>
    </SplitterPanel>
    <SplitterPanel>
      <Splitter class="bg" style="width: 100%;border: none" :gutterSize="0" layout="horizontal">
        <SplitterPanel class="left-login">
          <div class="modify-password-form">
            <div class="title">
              <img class="back-img" :src="BackImage" @click="goLogin"/>
              Forgot Password</div>
            <!-- <div class="flex-auto" style="margin-top: 0">
              <label for="email">* Email Address</label>
              <InputText :disabled="true" v-model="passwordInfo.email" class="input-user" placeholder="Email Address" autocomplete="off" maxlength="20" />
            </div>
            <div class="flex-auto">
              <label for="password">* New Password</label>
              <Password :feedback="false" v-model="passwordInfo.password" inputClass="input-password" placeholder="Password" autocomplete="off" maxlength="20" />
            </div>
            <div class="flex-auto">
              <label for="password">* Confirm Password</label>
              <Password :feedback="false" v-model="passwordInfo.password" inputClass="input-password" placeholder="Password" autocomplete="off" maxlength="20" />
            </div> -->
            <a-form
              ref="formRef"
              :model="passwordInfo"
              :rules="rules"
              layout="vertical"
            >
              <a-form-item class="input-label" label="Email" name="email">
                <a-input :maxlength="120" class="input-user" v-model:value="passwordInfo.email" :disabled="true"/>
              </a-form-item>
              <a-form-item class="input-label" label="New password " name="password">
                <a-input-password :visibilityToggle="true" :maxlength="20" style="color: #4C4A4E;height: 45px;width:355px" v-model:value="passwordInfo.password" placeholder="Password"/>
              </a-form-item>
              <a-form-item class="input-label" label="Confirm password " name="repassword">
                <a-input-password :visibilityToggle="true" :maxlength="20"  style="color: #4C4A4E;height: 45px;width:355px"  v-model:value="passwordInfo.repassword" placeholder="Confirm password"/>
              </a-form-item>
            </a-form>
            <div class="comment">
              <p>The password should be at least 8 characters and include uppercase and lowercase letters, numbers, and special characters.</p>
            </div>
            <div>
              <Button class="login-submit" @click="submitPassword">Submit</Button>
            </div>
          </div>
        </SplitterPanel>
        <SplitterPanel>
          <!-- <img src="@/assets/loginBg.png" style="width: 100%;" alt="bg"> -->
        </SplitterPanel>
      </Splitter>
    </SplitterPanel>
  </Splitter>
</template>
<script setup lang="ts">
  import { ref } from "vue";
  import { useRouter } from 'vue-router';
  import Splitter from "primevue/splitter";
  import SplitterPanel from "primevue/splitterpanel";
  import BackImage from '@/assets/back.png';
  import { message } from 'ant-design-vue';
  import LogoImg from '@/assets/logo_wakeb_white.png';

  const use_router = useRouter();
  const passwordInfo = ref({
    id: '',
    email: '',
    newPassword: '',
    repassword: '',
  })
  const formRef = ref();

  const validatePassword = async (rule, value) => {
      if (value === '') {
        return Promise.reject('Please input the password');
      } else {
        const regex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{8,20}$/;
        if(!regex.test(value)){
          return Promise.reject('Please enter the correct password format.');
        }
        if (passwordInfo.value.repassword !== '') {
          formRef.value.validateFields('repassword');
        }
        return Promise.resolve();
      }
    };
  const validateRePassword = async (rule, value) => {
    if (value === '') {
      return Promise.reject('Please input the password again');
    } else if (value !== passwordInfo.value.password) {
      return Promise.reject("Two inputs don't match!");
    } else {
      return Promise.resolve();
    }
  };
  const rules = {
    email: [{ required: true, message: 'Please input Email', trigger: 'blur' }],
    password: [{ required: true, validator: validatePassword, trigger: 'blur' }],
    repassword: [{ required: true, validator: validateRePassword, trigger: 'blur' }],
  }

  const sendPassword = async (info)=>{
    const response = await fetch('/gpt/user/forget/password',{
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...info
      }),
    })
    const res = await response.json()
    return res;
  }

  const goLogin = ()=>{
    use_router.push('/login');
  }

  const submitPassword = async ()=>{
    try {
      await formRef.value.validate();
    } catch (error) {
      return;
    }
    const urlParams = use_router.currentRoute.value.query;
    const res =await sendPassword({password: passwordInfo.value.password, ...urlParams});
    if(res.code===200) {
      message.success(res.message);
      use_router.push('/login');
    } else {
      message.error(res.message);
    }
  }

  const initBaseData = async ()=>{
    const urlParams = use_router.currentRoute.value.query;
    const response = await fetch(`/gpt/user/forget/password/info?token=${urlParams.token}`,{
      method: "Get",
      headers: {
        "Content-Type": "application/json",
      }
    })
    const res = await response.json();
    if(res.code == 200) {
      passwordInfo.value.email = res.data.email;
      passwordInfo.value.id = res.data.id;
    }
  }

  initBaseData();

</script>
<style scoped>
 .headerBg {
    height: 60px;
    line-height: 60px;
    font-size: 36px;
    color: #fff;
    background: url('../assets/headerBg.png');
    background-size: cover;
  }
  .left-login {
    max-width: 400px; 
    min-width: 400px;
    background: url('../assets/textBg.png');
    background-size: cover;
    box-shadow: 0 0 20px 5px rgba(81,13,143,0.20);
  }
  .bg {
    background: url('../assets/loginBg.png') !important;
    background-size: cover !important;
  }
  .modify-password-form {
    display: flex;
    flex-direction: column;
    margin-top: 51px;
    padding:0 20px;
    .title {
      text-align: left;
      color: #fff;
      font-size: 28px;
      margin-bottom: 99px;
      &::v-deep .back-img {
        margin-top: -4px;
        vertical-align: middle;
        margin-right: 18px;
        cursor: pointer;
      }
    }
    .flex-auto {
      margin-top: 25px;
      color: #fff;
      font-weight: 500;
      font-size: 22px;
      letter-spacing: 0.19px;
      text-shadow: 0 2px 4px rgba(87,79,215,0.20);
    }
    .input-user {
      margin-top: 8px;
      width: 356px;
      height: 45px;
      font-weight: 400;
      font-size: 20px;
      border: none;
      &:enabled:hover {
        border-color: rgba(188,210,255,1);
      }
      &:disabled {
        background: rgba(215,208,255,0.95);
      }
      &.p-disabled {
        background: rgba(215,208,255,0.95);
      }
      & .p-select-label {
        line-height: 45px;
      }
    }
    ::v-deep .input-password {
      margin-top: 8px;
      width: 356px;
      height: 45px;
      border-color: rgba(188,210,255,1);
      &:enabled:hover {
        border-color: rgba(188,210,255,1);
      }
    }
    ::v-deep .ant-form-item .ant-form-item-label >label.ant-form-item-required:not(.ant-form-item-required-mark-optional)::before {
      color: #fff;
    }
    ::v-deep .ant-form-item .ant-form-item-explain-error {
      color: #fff;
      font-size: 16px;
    }
    ::v-deep .input-label .ant-form-item-label label {
      color: #fff!important;
      font-size: 22px;
    }
    
    .login-submit {
      margin-top: 37px;
      margin-bottom: 20px;
      height: 45px;
      width: 356px;
      line-height: 45px;
      font-size: 20px;
      border-radius: 4px;
      background-image: linear-gradient(180deg, #CB7FF2 0%, #686AF6 100%);
      box-shadow: 0 4px 11px 5px rgba(50,45,146,0.15);
    }
    .comment {
      margin-top: 22px;
      font-size: 14px;
      color: #FFFFFF;
      letter-spacing: 0.12px;
    }
    .operator-link {
      margin: 43px 0;
      a {
        font-size: 20px;
        color: rgba(188,210,255,1);
        letter-spacing: 0.17px;
        text-align: center;
        &:hover {
          background: transparent;
        }
      }
    }
  }
  
</style>
