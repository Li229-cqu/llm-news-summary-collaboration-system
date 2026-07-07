import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import pinia from './stores'
import { useThemeStore } from './stores/theme'
import { useUserStore } from './stores/user'
import './styles/variables.css'
import './styles/global.css'

const app = createApp(App)

app.use(pinia)
useThemeStore(pinia).initializeTheme()
const userStore = useUserStore(pinia)
userStore.loadFromStorage()
// 启动时从服务器同步最新用户信息，解决跨设备头像/昵称不一致问题
userStore.syncProfile()
app.use(router)
app.use(ElementPlus)
app.mount('#app')
