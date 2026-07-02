export const todayInputDate = () => new Date().toISOString().slice(0, 10)

const extractMealLabel = (mealText, label) => {
  if (!mealText) return ''
  const prefix = `${label}:`
  const line = mealText.split('\n').find((item) => item.toLowerCase().startsWith(prefix.toLowerCase()))
  return line ? line.split(':').slice(1).join(':').trim() : ''
}

export const mealField = (meal, field, label) => {
  if (meal[field]) return meal[field]
  const labeledValue = extractMealLabel(meal.meal_text, label)
  if (labeledValue) return labeledValue
  if (field === 'foods_text') return meal.meal_text || 'Not provided'
  return 'Not provided'
}
