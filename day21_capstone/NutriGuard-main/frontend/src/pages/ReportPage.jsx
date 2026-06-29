import { mealField } from '../utils/meal'

export default function ReportPage({ selectedDate, setSelectedDate, loadReportDetails, report, reportDetails }) {
  return (
    <section className="panel page-panel report">
      <div className="report-head">
        <h2>Daily Report</h2>
        {report?.status && <span className={`status ${report.status.toLowerCase()}`}>{report.status}</span>}
      </div>
      <div className="date-row">
        <label>
          Report date
          <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
        </label>
        <button onClick={loadReportDetails}>Load report</button>
      </div>
      {reportDetails?.meals?.length > 0 && (
        <div className="timeline">
          {reportDetails.meals.map((meal, index) => (
            <article className="timeline-item" key={meal.id}>
              <div className="timeline-head">
                <div>
                  <strong>{index + 1}. {meal.meal_type || 'Meal'}</strong>
                  <p>{meal.meal_time ? new Date(meal.meal_time).toLocaleString() : 'No time set'}</p>
                </div>
                <span className={`status ${meal.status?.toLowerCase()}`}>{meal.status}</span>
              </div>
              <div className="meal-detail-grid">
                <p><b>Foods:</b> {mealField(meal, 'foods_text', 'Foods')}</p>
                <p><b>Drinks:</b> {mealField(meal, 'drinks_text', 'Drinks')}</p>
                <p><b>Supplements:</b> {mealField(meal, 'supplements_text', 'Supplements/medicine')}</p>
                <p><b>Notes:</b> {mealField(meal, 'notes_text', 'Notes')}</p>
              </div>
              <details open={index === reportDetails.meals.length - 1}>
                <summary>{index === 0 ? `${meal.meal_type || 'Meal'} report` : `Combined report after ${meal.meal_type || 'this meal'}`}</summary>
                {meal.report ? <pre>{meal.report.summary}</pre> : <p className="muted">Report is still processing for this meal.</p>}
              </details>
            </article>
          ))}
        </div>
      )}
      {report ? (
        <>
          <h3>Latest Combined Report</h3>
          <pre>{report.summary}</pre>
          {report.recommendations?.length > 0 && <ul>{report.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>}
          {report.safety_note && <p className="safety">{report.safety_note}</p>}
        </>
      ) : (
        <p className="muted">Choose a date or submit meals to generate a day-level report.</p>
      )}
    </section>
  )
}
