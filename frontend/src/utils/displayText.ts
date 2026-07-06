export function displayCategoryName(name?: string | null): string {
  return name === '娱乐' ? '文娱' : (name || '')
}
