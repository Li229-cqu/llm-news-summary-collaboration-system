export interface ChartThemeColors {
  background: string
  tooltipBg: string
  tooltipText: string
  axisText: string
  axisLine: string
  splitLine: string
}

function cssVar(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

export function getChartThemeColors(): ChartThemeColors {
  return {
    background: cssVar('--chart-bg', 'transparent'),
    tooltipBg: cssVar('--chart-tooltip-bg', 'rgba(255, 255, 255, 0.96)'),
    tooltipText: cssVar('--chart-tooltip-text', '#334155'),
    axisText: cssVar('--chart-axis-text', '#64748b'),
    axisLine: cssVar('--chart-axis-line', '#cbd5e1'),
    splitLine: cssVar('--chart-split-line', '#e2e8f0'),
  }
}

export function createChartTooltip(trigger: 'axis' | 'item' = 'axis', extra: Record<string, unknown> = {}) {
  const theme = getChartThemeColors()
  return {
    trigger,
    backgroundColor: theme.tooltipBg,
    borderColor: theme.axisLine,
    textStyle: { color: theme.tooltipText },
    ...extra,
  }
}

export function createChartLegend(extra: Record<string, unknown> = {}) {
  const theme = getChartThemeColors()
  return {
    textStyle: { color: theme.axisText, fontSize: 11 },
    ...extra,
  }
}

export function createValueAxis(extra: Record<string, unknown> = {}) {
  const theme = getChartThemeColors()
  const extraAxisLabel = (extra.axisLabel ?? {}) as Record<string, unknown>
  const extraSplitLine = (extra.splitLine ?? {}) as Record<string, unknown>
  return {
    type: 'value',
    axisLabel: { color: theme.axisText, fontSize: 10, ...extraAxisLabel },
    axisLine: { lineStyle: { color: theme.axisLine } },
    axisTick: { lineStyle: { color: theme.axisLine } },
    ...extra,
    splitLine: { lineStyle: { color: theme.splitLine }, ...extraSplitLine },
  }
}

export function createCategoryAxis(data: unknown[], extra: Record<string, unknown> = {}) {
  const theme = getChartThemeColors()
  const extraAxisLabel = (extra.axisLabel ?? {}) as Record<string, unknown>
  const extraSplitLine = (extra.splitLine ?? {}) as Record<string, unknown>
  return {
    type: 'category',
    data,
    axisLabel: { color: theme.axisText, fontSize: 10, ...extraAxisLabel },
    axisLine: { lineStyle: { color: theme.axisLine } },
    axisTick: { lineStyle: { color: theme.axisLine } },
    ...extra,
    splitLine: { lineStyle: { color: theme.splitLine }, ...extraSplitLine },
  }
}
