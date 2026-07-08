import { nextTick } from 'vue'

/** 当前页面会话中需要强制显示的回复 ID 集合（刷新后自然清空） */
const forceVisibleReplyIds = new Set<number>()

/** 标记某条回复在当前会话中强制可见 */
export function markReplyForceVisible(replyId: number) {
  forceVisibleReplyIds.add(replyId)
}

/** 检查某条回复是否被标记为强制可见 */
export function isReplyForceVisible(replyId: number): boolean {
  return forceVisibleReplyIds.has(replyId)
}

/** 清除指定回复在当前会话中的强制可见标记。 */
export function clearReplyForceVisible(replyIds: number[]) {
  for (const replyId of replyIds) {
    forceVisibleReplyIds.delete(replyId)
  }
}

/** 滚动定位到指定评论/回复 */
export async function scrollToComment(commentId: number) {
  await nextTick()
  const el = document.getElementById(`comment-${commentId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}
