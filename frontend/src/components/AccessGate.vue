<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

// 演示站访问门控：仅作访问控制，不是安全机制（密码会打包进前端，懂技术者可绕过）
const ACCESS_PASSWORD = 'qwertyuiop'
const STORAGE_KEY = 'agentdong_gate_granted'

const isUnlocked = ref(sessionStorage.getItem(STORAGE_KEY) === '1')
const password = ref('')
const errorMsg = ref('')
const reveal = ref(false)
const pwdInput = ref(null)

const unlock = () => {
  if (password.value === ACCESS_PASSWORD) {
    sessionStorage.setItem(STORAGE_KEY, '1')
    isUnlocked.value = true
    errorMsg.value = ''
  } else {
    errorMsg.value = '密码错误，请重新输入'
    password.value = ''
    pwdInput.value?.focus()
  }
}

watch(isUnlocked, (v) => {
  document.body.style.overflow = v ? '' : 'hidden'
})

onMounted(() => {
  if (!isUnlocked.value) {
    document.body.style.overflow = 'hidden'
    setTimeout(() => pwdInput.value?.focus(), 0)
  }
})

onUnmounted(() => {
  document.body.style.overflow = ''
})
</script>

<template>
  <slot v-if="isUnlocked" />
  <div v-else class="gate-mask">
    <div class="gate-card">
      <div class="gate-icon"><i class="pi pi-lock" aria-hidden="true" /></div>
      <h1 class="gate-title">访问验证</h1>
      <p class="gate-desc">请输入访问密码以进入系统</p>

      <form class="gate-form" @submit.prevent="unlock">
        <div class="gate-field" :class="{ 'has-error': errorMsg }">
          <i class="pi pi-key field-icon" aria-hidden="true" />
          <input
            ref="pwdInput"
            v-model="password"
            :type="reveal ? 'text' : 'password'"
            class="gate-input"
            placeholder="请输入访问密码"
            autocomplete="current-password"
            @input="errorMsg = ''"
          />
          <button
            type="button"
            class="gate-eye"
            :aria-label="reveal ? '隐藏密码' : '显示密码'"
            @click="reveal = !reveal"
          >
            <i :class="reveal ? 'pi pi-eye-slash' : 'pi pi-eye'" aria-hidden="true" />
          </button>
        </div>
        <p v-if="errorMsg" class="gate-error">{{ errorMsg }}</p>
        <button type="submit" class="gate-submit">进入系统</button>
      </form>

      <p class="gate-foot">受限访问 · 仅限授权人员</p>
    </div>
  </div>
</template>

<style scoped>
.gate-mask {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, rgba(244, 245, 247, 0.96), rgba(238, 242, 255, 0.96));
  backdrop-filter: blur(8px);
}
.gate-card {
  width: 100%;
  max-width: 380px;
  padding: 36px 32px 28px;
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius-lg);
  box-shadow: var(--app-shadow-lg);
  text-align: center;
}
.gate-icon {
  width: 52px;
  height: 52px;
  margin: 0 auto 18px;
  border-radius: 14px;
  background: var(--app-primary-soft);
  color: var(--app-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.gate-title {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 600;
  color: var(--app-text);
}
.gate-desc {
  margin: 0 0 24px;
  font-size: 13px;
  color: var(--app-text-2);
}
.gate-field {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border: 1px solid var(--app-border-strong);
  border-radius: var(--app-radius-sm);
  background: var(--app-surface);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.gate-field:focus-within {
  border-color: var(--app-primary);
  box-shadow: 0 0 0 3px var(--app-primary-ring);
}
.gate-field.has-error { border-color: var(--app-danger); }
.field-icon { color: var(--app-text-3); font-size: 14px; }
.gate-input {
  flex: 1;
  min-width: 0;
  height: 44px;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--app-text);
  font-size: 14px;
  font-family: inherit;
}
.gate-input::placeholder { color: var(--app-text-3); }
.gate-eye {
  border: 0;
  background: transparent;
  color: var(--app-text-3);
  cursor: pointer;
  padding: 6px;
  font-size: 14px;
}
.gate-eye:hover { color: var(--app-primary); }
.gate-error {
  margin: 8px 0 0;
  text-align: left;
  font-size: 12px;
  color: var(--app-danger);
}
.gate-submit {
  width: 100%;
  height: 44px;
  margin-top: 18px;
  border: 0;
  border-radius: var(--app-radius-sm);
  background: var(--app-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.gate-submit:hover { background: var(--app-primary-hover); }
.gate-foot {
  margin: 20px 0 0;
  font-size: 11px;
  color: var(--app-text-3);
}
</style>
