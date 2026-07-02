export default function Brand({ compact = false }) {
  return (
    <div className={compact ? 'navbar-brand' : 'brand-card'}>
      <span className={`brand-mark ${compact ? 'compact' : ''}`}>N</span>
      <div>
        {compact ? <strong>NutriGuard</strong> : <h1>NutriGuard</h1>}
        <span>AI meal timeline · Azure CI check</span>
      </div>
    </div>
  )
}
