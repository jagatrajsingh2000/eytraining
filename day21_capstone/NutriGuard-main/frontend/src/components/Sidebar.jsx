import Brand from './Brand'
import { navItems } from '../constants'

export default function Sidebar({ page, menuOpen, setMenuOpen, setPage, loadReportDetails, loadHistory }) {
  const navigate = (value) => {
    setPage(value)
    setMenuOpen(false)
    if (value === 'report') loadReportDetails()
    if (value === 'history') loadHistory()
  }

  return (
    <aside className={`side-nav ${menuOpen ? 'open' : ''}`}>
      <Brand />
      <button className="drawer-close" onClick={() => setMenuOpen(false)} aria-label="Close menu">Close</button>
      <nav>
        {navItems.map(([value, label]) => (
          <button key={value} className={page === value ? 'active' : ''} onClick={() => navigate(value)}>
            {label}
          </button>
        ))}
      </nav>
      <div className="sidebar-well">
        <div className="sidebar-leaf-sprig" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <span className="mini-label">Today's focus</span>
        <strong>Balanced plate</strong>
        <div className="plate-rings" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <p>Track foods, drinks, and supplement timing so the agent can spot meal combinations.</p>
      </div>
      <div className="sidebar-tips">
        <span>Leafy greens</span>
        <span>Protein gap</span>
        <span>Tea timing</span>
      </div>
    </aside>
  )
}
