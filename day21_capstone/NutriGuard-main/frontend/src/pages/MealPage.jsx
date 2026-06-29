function MealFieldCard({ type, iconClass, title, subtitle, label, value, onChange, rows, placeholder }) {
  return (
    <div className={`meal-field-card ${type}-card`}>
      <div className={`field-icon ${iconClass}`}>
        <span aria-hidden="true" />
        <b>{title}</b>
        <small>{subtitle}</small>
      </div>
      <label>
        {label}
        <textarea value={value} onChange={(event) => onChange(event.target.value)} rows={rows} placeholder={placeholder} />
      </label>
    </div>
  )
}

export default function MealPage(props) {
  return (
    <section className="panel page-panel">
      <div className="form-hero">
        <div>
          <span className="mini-label">Meal check-in</span>
          <h2>Meal Details</h2>
          <p>Log the full context so the daily report can understand timing, pairings, and supplements.</p>
        </div>
        <div className="meal-icons" aria-hidden="true">
          <span>Fresh</span>
          <span>Hydrate</span>
          <span>Timing</span>
        </div>
      </div>
      <div className="grid two">
        <label>
          Meal type
          <select value={props.mealType} onChange={(event) => props.setMealType(event.target.value)}>
            <option value="breakfast">Breakfast</option>
            <option value="lunch">Lunch</option>
            <option value="dinner">Dinner</option>
            <option value="snack">Snack</option>
            <option value="supplement">Supplement/medicine</option>
          </select>
        </label>
        <label>
          Meal time
          <input type="datetime-local" value={props.mealTime} onChange={(event) => props.setMealTime(event.target.value)} />
        </label>
      </div>
      <MealFieldCard type="food" iconClass="food-icon" title="Foods" subtitle="Meal items" label="Foods" value={props.foodsText} onChange={props.setFoodsText} rows={3} placeholder="Poha, dal, paneer, dahi, salad..." />
      <MealFieldCard type="drink" iconClass="drink-icon" title="Drinks" subtitle="Beverages" label="Drinks" value={props.drinksText} onChange={props.setDrinksText} rows={2} placeholder="Tea, coffee, water, juice..." />
      <MealFieldCard type="supplement" iconClass="dose-icon" title="Dose" subtitle="Supplements" label="Supplements or medicine" value={props.mealSupplementsText} onChange={props.setMealSupplementsText} rows={2} placeholder="Iron tablet, calcium, vitamin D..." />
      <MealFieldCard type="note" iconClass="note-icon" title="Notes" subtitle="Context" label="Notes" value={props.mealNotesText} onChange={props.setMealNotesText} rows={2} placeholder="Portion, symptoms, cravings, digestion..." />
      <label>
        Optional combined description
        <textarea value={props.mealText} onChange={(event) => props.setMealText(event.target.value)} rows={3} placeholder="Leave blank unless you want to add extra meal context." />
      </label>
      <button className="primary-action" onClick={props.submitMeal} disabled={props.loading}>Submit meal</button>
    </section>
  )
}
