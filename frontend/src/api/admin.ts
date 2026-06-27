import request from '@/api/http'

export interface AdminDashboard {
  user_count: number
  news_count: number
  post_count: number
  pending_count: number
}

export interface UserItem {
  id: number
  username: string
  nickname: string
  role: string
  status: number
  create_time?: string
}

export interface PaginationResponse<T> {
  list: T[]
  total: number
  page: number
  page_size: number
}

export async function getDashboard(): Promise<AdminDashboard> {
  return request.get('/api/admin/dashboard')
}

export async function getPendingPosts(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<any>> {
  return request.get('/api/admin/pending-posts', {
    params: { page, page_size: pageSize },
  })
}

export async function getUsers(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginationResponse<UserItem>> {
  return request.get('/api/admin/users', {
    params: { page, page_size: pageSize },
  })
}

export async function getSystemConfig(): Promise<Record<string, unknown>> {
  return request.get('/api/admin/system-config')
}
