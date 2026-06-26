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

export interface RegisterParams {
  username: string
  password: string
  confirm_password: string
  nickname?: string
  email?: string
  phone?: string
}

export interface RegisterResult {
  id: number
  username: string
  nickname: string
}

export interface ResetPasswordParams {
  username: string
  email?: string
  phone?: string
  new_password: string
  confirm_password: string
}

export function loginApi(params: LoginParams) {
  return request.post<LoginResult, LoginResult>('/api/auth/login', params)
}

export function registerApi(params: RegisterParams) {
  return request.post<RegisterResult, RegisterResult>('/api/auth/register', params)
}

export function resetPasswordApi(params: ResetPasswordParams) {
  return request.post<{ message: string }, { message: string }>('/api/auth/reset-password', params)
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
