import ProfileMenu from './ProfileMenu'
import ThemeToggle from './ThemeToggle'

const pageTitle = {
  profile: 'Set profile',
  meal: 'Log meal',
  report: 'Daily report',
  history: 'History',
}

export default function DashboardHeader({ page, theme, setTheme, user, profileOpen, setProfileOpen, onUpdateProfile, onLogout }) {
  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">NutriGuard workspace</span>
        <h2>{pageTitle[page] || 'NutriGuard'}</h2>
        <p>Profile-aware nutrition, full-day timing, and progressive reports.</p>
      </div>
      <div className="desktop-header-actions">
        <ThemeToggle theme={theme} setTheme={setTheme} />
        <ProfileMenu
          user={user}
          open={profileOpen}
          setOpen={setProfileOpen}
          onUpdateProfile={onUpdateProfile}
          onLogout={onLogout}
        />
      </div>
    </header>
  )
}
