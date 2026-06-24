import type { UserInfo } from '@/stores/user'
import request from './request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  token: string
  user: UserInfo
}

export function loginApi(params: LoginParams) {
  return request.post<LoginResult, LoginResult>('/api/auth/login', params)
}

export function logoutApi() {
  return request.post<null, null>('/api/auth/logout')
}

export function getCurrentUserApi() {
  return request.get<UserInfo, UserInfo>('/api/auth/me')
}

export function checkLoginApi() {
  return request.get<UserInfo, UserInfo>('/api/auth/check-login')
}

export function checkEditorApi() {
  return request.get<UserInfo, UserInfo>('/api/auth/check-editor')
}

export function checkAdminApi() {
  return request.get<UserInfo, UserInfo>('/api/auth/check-admin')
}
