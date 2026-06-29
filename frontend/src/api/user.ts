import request from '@/api/request'

export interface UserInfo {
  id: number
  username: string
  nickname: string
  role: string
  avatar: string
  email: string
  phone: string
  status: number
}

export interface UpdateProfileParams {
  nickname?: string
  avatar?: string
  email?: string
  phone?: string
}

export interface ChangePasswordParams {
  old_password: string
  new_password: string
  confirm_password: string
}

export function getUserProfileApi() {
  return request.get<UserInfo, UserInfo>('/api/user/profile')
}

export function updateUserProfileApi(params: UpdateProfileParams) {
  return request.put<UserInfo, UserInfo>('/api/user/profile', params)
}

export function changePasswordApi(params: ChangePasswordParams) {
  return request.post<null, null>('/api/user/change-password', params)
}
