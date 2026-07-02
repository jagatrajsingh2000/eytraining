const APP_TIME_ZONE = import.meta.env.VITE_APP_TIMEZONE || 'Asia/Kolkata'

export const formatMealTime = (value) => {
  if (!value) return 'No time set'
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: APP_TIME_ZONE,
  }).format(new Date(value))
}

export const dateKeyInAppTimezone = (value) => {
  if (!value) return ''
  const parts = new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: APP_TIME_ZONE,
  }).formatToParts(new Date(value))
  const byType = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${byType.year}-${byType.month}-${byType.day}`
}
