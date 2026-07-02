import { dietOptions, goalOptions } from '../constants'

export default function ProfilePage(props) {
  return (
    <section className="panel page-panel">
      <h2>Health Profile</h2>
      <div className="grid two">
        <div className="field-group">
          <span>Goals</span>
          <div className="checkbox-grid">
            {goalOptions.map(([value, label]) => (
              <label className="check-card" key={value}>
                <input type="checkbox" checked={props.goals.includes(value)} onChange={() => props.toggleGoal(value)} />
                {label}
              </label>
            ))}
          </div>
        </div>
        <label>
          Diet type
          <select value={props.dietType} onChange={(event) => props.setDietType(event.target.value)}>
            {dietOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
      </div>
      <label>
        Health conditions
        <textarea value={props.healthConditionsText} onChange={(event) => props.setHealthConditionsText(event.target.value)} rows={3} />
      </label>
      <label>
        Deficiencies
        <textarea value={props.deficienciesText} onChange={(event) => props.setDeficienciesText(event.target.value)} rows={3} />
      </label>
      <label>
        Supplements
        <textarea value={props.supplementsText} onChange={(event) => props.setSupplementsText(event.target.value)} rows={3} />
      </label>
      <label>
        Upload text report
        <input type="file" accept=".txt,.csv,.md,text/*" onChange={props.readReportFile} />
      </label>
      <label>
        Health report text
        <textarea value={props.healthReportText} onChange={(event) => props.setHealthReportText(event.target.value)} rows={8} />
      </label>
      <button onClick={() => props.saveProfile('meal')} disabled={props.loading}>Save profile</button>
      {props.parsedProfile && (
        <div className="parsed-box">
          <strong>Normalized for agents</strong>
          <p>Conditions: {(props.parsedProfile.health_conditions || []).join(', ') || 'none'}</p>
          <p>Deficiencies: {(props.parsedProfile.deficiencies || []).join(', ') || 'none'}</p>
          <p>Supplements: {(props.parsedProfile.supplements || []).join(', ') || 'none'}</p>
        </div>
      )}
      {props.message && <p className="message">{props.message}</p>}
    </section>
  )
}
