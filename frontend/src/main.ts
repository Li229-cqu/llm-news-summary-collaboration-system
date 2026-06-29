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
app.use(router)
app.use(ElementPlus)
app.mount('#app')
