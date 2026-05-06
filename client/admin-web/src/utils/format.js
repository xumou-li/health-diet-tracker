export function formatDateTime(value) {
  if (!value) {
    return '—'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString('zh-CN', {
    hour12: false,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

export function formatNumber(value) {
  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return '0'
  }

  return numericValue.toLocaleString('zh-CN')
}

export function formatMilliseconds(value) {
  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return '0 ms'
  }

  return `${Math.round(numericValue).toLocaleString('zh-CN')} ms`
}

export function formatJson(value) {
  if (value === null || typeof value === 'undefined') {
    return ''
  }

  if (typeof value === 'string') {
    try {
      return JSON.stringify(JSON.parse(value), null, 2)
    } catch (error) {
      return value
    }
  }

  return JSON.stringify(value, null, 2)
}
