import { mealField } from '../utils/meal'
import { useState } from 'react'
import { createPortal } from 'react-dom'
import { formatMealTime } from '../utils/time'

const SECTION_TITLES = {
  summary: "Today's Nutrition Summary",
  timeline: 'Timeline',
  needs_attention: 'Needs Attention',
  suggestions: 'Suggestions',
  safety: 'Safety',
}

const SECTION_ALIASES = {
  "today's nutrition summary": 'summary',
  'todays nutrition summary': 'summary',
  timeline: 'timeline',
  'needs attention': 'needs_attention',
  suggestions: 'suggestions',
  safety: 'safety',
}

function cleanLine(line) {
  return line
    .trim()
    .replace(/^\*+\s*/, '')
    .replace(/^[-*]\s*/, '')
    .replace(/\*\*/g, '')
    .trim()
}

function parseReportSections(summary = '') {
  const sections = []
  let current = { key: 'summary', title: SECTION_TITLES.summary, lines: [] }

  summary.split('\n').forEach((rawLine) => {
    const line = cleanLine(rawLine)
    if (!line) return

    const normalized = line.replace(/:$/, '').toLowerCase()
    const key = SECTION_ALIASES[normalized]
    if (key) {
      if (current.lines.length) sections.push(current)
      current = { key, title: SECTION_TITLES[key], lines: [] }
      return
    }

    current.lines.push(line)
  })

  if (current.lines.length) sections.push(current)
  return sections.length ? sections : [{ key: 'summary', title: SECTION_TITLES.summary, lines: [summary] }]
}

export default function ReportPage({ selectedDate, setSelectedDate, loadReportDetails, report, reportDetails, submitReportFeedback }) {
  const [feedbackMeal, setFeedbackMeal] = useState(null)
  const [feedbackCategory, setFeedbackCategory] = useState('suggestions')
  const [feedbackRating, setFeedbackRating] = useState('liked')
  const [feedbackComment, setFeedbackComment] = useState('')
  const [feedbackSaving, setFeedbackSaving] = useState(false)

  const feedbackLabels = {
    needs_attention: 'Needs Attention',
    suggestions: 'Suggestions',
  }

  const getFeedback = (meal, category) => meal.report?.feedback?.[category] || null

  const openFeedback = (meal, category, rating = getFeedback(meal, category)?.rating || 'liked') => {
    const feedback = getFeedback(meal, category)
    setFeedbackMeal(meal)
    setFeedbackCategory(category)
    setFeedbackRating(rating)
    setFeedbackComment(feedback?.comment || '')
  }

  const closeFeedback = () => {
    setFeedbackMeal(null)
    setFeedbackComment('')
    setFeedbackSaving(false)
  }

  const saveFeedback = async () => {
    if (!feedbackMeal) return
    setFeedbackSaving(true)
    try {
      await submitReportFeedback(feedbackMeal.id, feedbackCategory, feedbackRating, feedbackComment)
      closeFeedback()
    } finally {
      setFeedbackSaving(false)
    }
  }

  const feedbackDialog = feedbackMeal && createPortal(
    <div className="modal-backdrop" role="presentation" onClick={closeFeedback}>
      <div className="feedback-modal" role="dialog" aria-modal="true" aria-label="Report feedback" onClick={(event) => event.stopPropagation()}>
        <div>
          <span className="eyebrow">{feedbackLabels[feedbackCategory]} feedback</span>
          <h3>Was this section useful?</h3>
          <p className="muted">Your answer is stored by report section so we can measure what the agent gets right later.</p>
        </div>
        <div className="feedback-choice-row">
          <button className={feedbackRating === 'liked' ? 'active-choice' : 'ghost-button'} onClick={() => setFeedbackRating('liked')}>Liked it</button>
          <button className={feedbackRating === 'disliked' ? 'active-choice' : 'ghost-button'} onClick={() => setFeedbackRating('disliked')}>Not useful</button>
        </div>
        <label>
          Optional note
          <textarea
            value={feedbackComment}
            onChange={(event) => setFeedbackComment(event.target.value)}
            placeholder={`What should the agent improve in ${feedbackLabels[feedbackCategory].toLowerCase()}?`}
          />
        </label>
        <div className="modal-actions">
          <button className="ghost-button" onClick={closeFeedback}>Cancel</button>
          <button onClick={saveFeedback} disabled={feedbackSaving}>{feedbackSaving ? 'Saving...' : 'Save feedback'}</button>
        </div>
      </div>
    </div>,
    document.body
  )

  return (
    <>
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
                  <p>{formatMealTime(meal.meal_time)}</p>
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
                {meal.report ? (
                  <ReportBody
                    summary={meal.report.summary}
                    renderFeedback={(category) => (
                      <ReportFeedbackRow
                        label={feedbackLabels[category]}
                        feedback={getFeedback(meal, category)}
                        onLike={() => openFeedback(meal, category, 'liked')}
                        onDislike={() => openFeedback(meal, category, 'disliked')}
                      />
                    )}
                  />
                ) : (
                  <p className="muted">Report is still processing for this meal.</p>
                )}
              </details>
            </article>
          ))}
        </div>
      )}
      {report ? (
        <>
          <h3>Latest Combined Report</h3>
          <ReportBody summary={report.summary} />
          {report.recommendations?.length > 0 && <ul>{report.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>}
          {report.safety_note && <p className="safety">{report.safety_note}</p>}
        </>
      ) : (
        <p className="muted">Choose a date or submit meals to generate a day-level report.</p>
      )}
      </section>
      {feedbackDialog}
    </>
  )
}

function ReportBody({ summary, renderFeedback }) {
  return (
    <div className="report-body">
      {parseReportSections(summary).map((section) => (
        <section className={`report-section ${section.key}`} key={`${section.key}-${section.title}`}>
          <h4>{section.title}</h4>
          <ul>
            {section.lines.map((line, index) => (
              <li key={`${section.key}-${index}`}>{line}</li>
            ))}
          </ul>
          {['needs_attention', 'suggestions'].includes(section.key) && renderFeedback?.(section.key)}
        </section>
      ))}
    </div>
  )
}

function ReportFeedbackRow({ label, feedback, onLike, onDislike }) {
  return (
    <div className="report-feedback-row">
      <span>{feedback ? `${label} feedback saved: ${feedback.rating}` : `Was this ${label} section helpful?`}</span>
      <button onClick={onLike}>Like</button>
      <button className="ghost-button" onClick={onDislike}>Not useful</button>
    </div>
  )
}
