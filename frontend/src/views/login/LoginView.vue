<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { loginApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const loginForm = reactive({
  username: '',
  password: '',
})

const rules: FormRules<typeof loginForm> = {
  username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
  password: [{ required: true, message: '密码不能为空', trigger: 'blur' }],
}

onMounted(() => {
  if (userStore.isLoggedIn) {
    router.replace('/home')
  }
})

function getErrorMessage(error: unknown) {
  if (typeof error === 'object' && error !== null) {
    const responseData = (error as { response?: { data?: { message?: string } } }).response?.data
    const message = responseData?.message || (error as { message?: string }).message
    if (message) {
      return message
    }
  }

  return '登录失败，请稍后重试'
}

async function handleLogin() {
  if (!formRef.value) {
    return
  }

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  loading.value = true
  try {
    const result = await loginApi(loginForm)
    userStore.setLoginInfo(result.token, result.user)
    ElMessage.success('登录成功')

    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/home'
    await router.replace(redirect.startsWith('/') ? redirect : '/home')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="page-container">
    <el-card class="app-card login-card" shadow="never">
      <h1>登录</h1>
      <p>登录后可使用个人中心、互动记录和权限相关功能。</p>

      <el-form ref="formRef" :model="loginForm" :rules="rules" class="login-form" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" autocomplete="current-password" show-password />
        </el-form-item>
        <el-button class="login-form__button" type="primary" :loading="loading" @click="handleLogin">
          登录
        </el-button>
      </el-form>

      <el-alert class="login-account-hint" type="info" :closable="false" title="测试账号">
        <template #default>
          <div>普通用户：user / 123456</div>
          <div>审核编辑：editor / 123456</div>
          <div>管理员：admin / 123456</div>
        </template>
      </el-alert>
    </el-card>
  </main>
</template>

<style scoped>
.page-container {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
}

.login-card {
  width: min(100%, 440px);
}

h1 {
  margin-top: 0;
}

p {
  margin: 0;
  color: var(--color-text-secondary);
}

.login-form {
  margin-top: 24px;
}

.login-form__button {
  width: 100%;
}

.login-account-hint {
  margin-top: 20px;
  line-height: 1.8;
}
</style>
