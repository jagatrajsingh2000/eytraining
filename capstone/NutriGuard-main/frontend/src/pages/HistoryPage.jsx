import { dateKeyInAppTimezone, formatMealTime } from '../utils/time'

export default function HistoryPage({ selectedDate, setSelectedDate, history, loadHistory }) {
  const filtered = history.filter((meal) => {
    const time = meal.meal_time || meal.created_at
    return !selectedDate || (time && dateKeyInAppTimezone(time) === selectedDate)
  })

  return (
    <section className="panel page-panel">
      <div className="report-head">
        <h2>Meal History</h2>
        <button onClick={loadHistory}>Refresh</button>
      </div>
      <div className="date-row">
        <label>
          History date
          <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
        </label>
      </div>
      <div className="history">
        {filtered.length === 0 && <p className="muted">No meals for this date.</p>}
        {filtered.map((meal) => (
          <article key={meal.id}>
            <strong>#{meal.id} {meal.meal_type || 'meal'}</strong>
            <span className={`status ${meal.status?.toLowerCase()}`}>{meal.status}</span>
            <p>{formatMealTime(meal.meal_time)}</p>
            <p>{meal.meal_text}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
