<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { loginApi, registerApi, resetPasswordApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const activeTab = ref('login')

const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()
const resetFormRef = ref<FormInstance>()
const loading = ref(false)
const registerLoading = ref(false)
const resetLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const registerForm = reactive({
  username: '',
  password: '',
  confirm_password: '',
  nickname: '',
  email: '',
  phone: '',
})

const resetForm = reactive({
  username: '',
  email: '',
  phone: '',
  new_password: '',
  confirm_password: '',
})

const loginRules: FormRules<typeof loginForm> = {
  username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
  password: [{ required: true, message: '密码不能为空', trigger: 'blur' }],
}

const registerRules: FormRules<typeof registerForm> = {
  username: [
    { required: true, message: '用户名不能为空', trigger: 'blur' },
    { min: 3, message: '用户名长度不能少于3位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '密码不能为空', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const resetRules: FormRules<typeof resetForm> = {
  username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
  new_password: [
    { required: true, message: '新密码不能为空', trigger: 'blur' },
    { min: 6, message: '新密码长度不能少于6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== resetForm.new_password) {
          callback(new Error('两次输入的新密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
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

  return '操作失败，请稍后重试'
}

async function handleLogin() {
  if (!loginFormRef.value) {
    return
  }

  const valid = await loginFormRef.value.validate().catch(() => false)
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

async function handleRegister() {
  if (!registerFormRef.value) {
    return
  }

  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  registerLoading.value = true
  try {
    await registerApi(registerForm)
    ElMessage.success('注册成功，请登录')
    loginForm.username = registerForm.username
    loginForm.password = ''
    activeTab.value = 'login'
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    registerLoading.value = false
  }
}

async function handleResetPassword() {
  if (!resetFormRef.value) {
    return
  }

  const valid = await resetFormRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }

  resetLoading.value = true
  try {
    await resetPasswordApi(resetForm)
    ElMessage.success('密码重置成功，请使用新密码登录')
    loginForm.username = resetForm.username
    loginForm.password = ''
    activeTab.value = 'login'
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    resetLoading.value = false
  }
}

function goToTab(tab: string) {
  activeTab.value = tab
}
</script>

<template>
  <main class="page-container">
    <el-card class="app-card login-card" shadow="never">
      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <h1>登录</h1>
          <p>登录后可使用个人中心、互动记录和权限相关功能。</p>

          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            label-position="top"
            @submit.prevent="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" autocomplete="username" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                autocomplete="current-password"
                show-password
              />
            </el-form-item>
            <div class="form-footer-links">
              <span class="link-btn" @click="goToTab('reset')">忘记密码？</span>
            </div>
            <el-button class="login-form__button" type="primary" :loading="loading" @click="handleLogin">
              登录
            </el-button>
          </el-form>

          <div class="bottom-tip">
            还没有账号？
            <span class="link-btn" @click="goToTab('register')">立即注册</span>
          </div>

        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <h1>注册账号</h1>
          <p>创建一个新账号，体验更多功能。</p>

          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            class="login-form"
            label-position="top"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="registerForm.username" placeholder="请输入用户名（至少3位）" />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="registerForm.nickname" placeholder="请输入昵称（选填）" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱（选填）" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="registerForm.phone" placeholder="请输入手机号（选填）" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码（至少6位）"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="registerForm.confirm_password"
                type="password"
                placeholder="请再次输入密码"
                show-password
              />
            </el-form-item>
            <el-button
              class="login-form__button"
              type="primary"
              :loading="registerLoading"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form>

          <div class="bottom-tip">
            已有账号？
            <span class="link-btn" @click="goToTab('login')">立即登录</span>
          </div>
        </el-tab-pane>

        <el-tab-pane label="忘记密码" name="reset">
          <h1>重置密码</h1>
          <p>通过用户名验证后重置您的密码。</p>

          <el-form
            ref="resetFormRef"
            :model="resetForm"
            :rules="resetRules"
            class="login-form"
            label-position="top"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="resetForm.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="注册邮箱">
              <el-input v-model="resetForm.email" placeholder="请输入注册邮箱（选填，用于验证）" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="resetForm.phone" placeholder="请输入注册手机号（选填，用于验证）" />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="resetForm.new_password"
                type="password"
                placeholder="请输入新密码（至少6位）"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input
                v-model="resetForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            <el-alert
              type="warning"
              :closable="false"
              size="small"
              title="提示：邮箱或手机号至少填写一项用于验证"
              class="reset-tip"
            />
            <el-button
              class="login-form__button"
              type="primary"
              :loading="resetLoading"
              @click="handleResetPassword"
            >
              重置密码
            </el-button>
          </el-form>

          <div class="bottom-tip">
            想起来了？
            <span class="link-btn" @click="goToTab('login')">返回登录</span>
          </div>
        </el-tab-pane>
      </el-tabs>
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
  width: min(100%, 480px);
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.login-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}

h1 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 24px;
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
  margin-top: 8px;
}

.form-footer-links {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
  margin-top: -8px;
}

.link-btn {
  color: var(--el-color-primary);
  cursor: pointer;
  font-size: 14px;
}

.link-btn:hover {
  text-decoration: underline;
}

.bottom-tip {
  text-align: center;
  margin-top: 20px;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.reset-tip {
  margin-bottom: 16px;
}
</style>
