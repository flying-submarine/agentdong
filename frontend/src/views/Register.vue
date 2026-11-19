<template>
  <Splitter style="width: 100%;border: none" :gutterSize="0" layout="vertical">
    <SplitterPanel style="max-height: 50px; min-height: 50px;">  
      <div class="headerBg"><img :src="LogoImg" style="margin-left: 11px;height:24px"/></div>
    </SplitterPanel>
    <SplitterPanel>
      <Splitter class="bg" style="width: 100%;border: none" :gutterSize="0" layout="horizontal">
        <SplitterPanel class="left-login">
          <div class="register-form">
            <div class="title">Sign up</div>
            <!-- <div class="flex-auto">
              <label for="email">* Email Address</label>
              <InputText :disabled="true" v-model="registerInfo.email" class="input-user" placeholder="Email Address" autocomplete="off" maxlength="20" />
            </div>
            <div class="flex-auto">
              <label for="department">* Department</label>
              <Select :disabled="true" optionValue="id"  optionLabel="departmentName" v-model="registerInfo.departmentId" :options="departmentList" placeholder="select a department" class="input-user" />
            </div>
            <div class="flex-auto">
              <label for="username">* username</label>
              <InputText v-model="registerInfo.username" class="input-user" placeholder="username" autocomplete="off" maxlength="120" />
            </div>
            <div class="flex-auto">
              <label for="password">* Password</label>
              <Password :feedback="false" v-model="registerInfo.password" inputClass="input-password" placeholder="Password" autocomplete="off" maxlength="20" />
            </div>
            <div class="flex-auto">
              <label for="repassword">* Repeat password</label>
              <Password :feedback="false" v-model="registerInfo.repassword" inputClass="input-password" placeholder="Password" autocomplete="off" maxlength="20" />
            </div> -->
            <a-form
              ref="formRef"
              :model="registerInfo"
              :rules="rules"
              layout="vertical"
            >
              <a-form-item class="input-label" label="Email" name="email">
                <a-input :maxlength="120" class="input-user" v-model:value="registerInfo.email" :disabled="true"/>
              </a-form-item>
              <a-form-item class="input-label" label="Department" name="departmentId">
                <a-select class="input-user" :disabled="true" v-model:value="registerInfo.departmentId"  :options="departmentList"></a-select>
              </a-form-item>
              <a-form-item class="input-label" label="Username" name="username">
                <a-input :maxlength="15" class="input-user" style="color: #4C4A4E" v-model:value="registerInfo.username" placeholder="Username"/>
              </a-form-item>
              <a-form-item class="input-label" label="Password" name="password">
                <a-input-password :visibilityToggle="true" :maxlength="20" style="color: #4C4A4E;height: 45px;width:355px" v-model:value="registerInfo.password" placeholder="Password"/>
              </a-form-item>
              <a-form-item class="input-label" label="Repeat password" name="repassword">
                <a-input-password :visibilityToggle="true" :maxlength="20"  style="color: #4C4A4E;height: 45px;width:355px"  v-model:value="registerInfo.repassword" placeholder="Repeat password"/>
              </a-form-item>
            </a-form>
            <div class="comment">
              <p>The password should be at least 8 characters and include uppercase and lowercase letters, numbers, and special characters.</p>
            </div>
            <div>
              <Button class="login-submit" @click="register">Register</Button>
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
  import LogoImg from '@/assets/logo_wakeb_white.png';

  const use_router = useRouter();
  const registerInfo = ref({
    email: '',
    username: '',
    password: '',
    repassword: '',
    departmentId: '',
  })
  const formRef = ref();
  const departmentList = ref([]);
  const validatePassword = async (rule, value) => {
      if (value === '') {
        return Promise.reject('Please input the password');
      } else {
        const regex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{8,20}$/;
        if(!regex.test(value)){
          return Promise.reject('Please enter the correct password format.');
        }
        if (registerInfo.value.repassword !== '') {
          formRef.value.validateFields('repassword');
        }
        return Promise.resolve();
      }
    };
  const validateRePassword = async (rule, value) => {
    if (value === '') {
      return Promise.reject('Please input the password again');
    } else if (value !== registerInfo.value.password) {
      return Promise.reject("Two inputs don't match!");
    } else {
      return Promise.resolve();
    }
  };
  const rules = {
    email: [{ required: true, message: 'Please input Email', trigger: 'blur' }],
    departmentId: [{ required: true, message: 'Please select a department', trigger: 'blur' }],
    username: [{ required: true, message: 'Please input username', trigger: 'blur' }],
    password: [{ required: true, validator: validatePassword, trigger: 'blur' }],
    repassword: [{ required: true, validator: validateRePassword, trigger: 'blur' }],
  }

  const registerUser = async (info)=>{
    const response = await fetch('/gpt/user/register',{
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

  const register = async ()=>{
    const error = await formRef.value.validate();
    const info=registerInfo.value;
    const urlParams = use_router.currentRoute.value.query;
    const res =await registerUser({...info, ...urlParams, repassword: undefined, departmentId:undefined, email: undefined  });
    if(res.code===200) {
      use_router.push('/login');
    }
  }

  const initBaseData = async ()=>{
    const urlParams = use_router.currentRoute.value.query;
    const response = await fetch(`/gpt/user/register/info?token=${urlParams.token}`,{
      method: "Get",
      headers: {
        "Content-Type": "application/json",
      }
    })
    const res = await response.json();
    if(res.code == 200) {
      registerInfo.value.email = res.data.email;
      registerInfo.value.departmentId = res.data.departmentId;
    }
  }


const getDepartmentList = async ()=>{
  const res = await fetch('/gpt/department/list?compantId=1', {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  const response = await res.json();
  if(response.code === 200) {
    departmentList.value=(response.data||[]).map(item=>{
      return {
        value: item.id,
        label: item.departmentName
      }
    });
  }
}

  initBaseData();
  getDepartmentList();

</script>
<style >
 .headerBg {
    height: 50px;
    line-height: 50px;
    font-size: 30px;
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
    min-height: calc(100vh - 50px);
  }
  .bg {
    background: url('../assets/loginBg.png') !important;
    background-size: cover !important;
  }
  .register-form {
    display: flex;
    flex-direction: column;
    margin-top: 54px;
    padding:0 20px;
    .title {
      text-align: left;
      color: #fff;
      font-size: 30px;
      margin-bottom: 29px;
    }
    .flex-auto {
      font-size: 22px;
      color: #fff;
      font-weight: 500;
      font-size: 22px;
      letter-spacing: 0.19px;
      text-shadow: 0 2px 4px var(--app-primary-ring);
    }
    & .ant-form-item .ant-form-item-label >label.ant-form-item-required:not(.ant-form-item-required-mark-optional)::before {
      color: #fff;
    }
    & .ant-form-item .ant-form-item-explain-error {
      color: #fff;
      font-size: 16px;
    }

    .input-label {
      .ant-form-item-label label{
        color: #fff!important;
        font-size: 22px;
      }
    }
    .input-user {
      width: 355px;
      height: 45px;
      font-weight: 400;
      font-size: 14px;
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
      & .ant-select-selector {
        height: 45px;
        border:none;
        background: rgba(215,208,255,0.95)!important;
        .ant-select-selection-item {
          line-height: 45px;
        }
      }
    }
    .input-password {
      margin-top: 8px;
      width: 355px;
      height: 45px;
      border-color: rgba(188,210,255,1);
      &:enabled:hover {
        border-color: rgba(188,210,255,1);
      }
    }
    .login-submit {
      margin-top: 37px;
      margin-bottom: 20px;
      height: 56px;
      width: 355px;
      line-height: 56px;
      font-size: 28px;
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
