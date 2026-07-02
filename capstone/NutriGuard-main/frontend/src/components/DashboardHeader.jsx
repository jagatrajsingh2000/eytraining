import NotificationMenu from './NotificationMenu'
import ProfileMenu from './ProfileMenu'
import ThemeToggle from './ThemeToggle'

const pageTitle = {
  profile: 'Set profile',
  meal: 'Log meal',
  report: 'Daily report',
  history: 'History',
  admin: 'Admin metrics',
}

export default function DashboardHeader({
  page,
  theme,
  setTheme,
  user,
  profileOpen,
  setProfileOpen,
  notifications,
  notificationOpen,
  setNotificationOpen,
  onMarkNotificationRead,
  onRefreshNotifications,
  onUpdateProfile,
  onLogout,
}) {
  return (
    <header className="topbar">
      <div>
        <span className="eyebrow">NutriGuard workspace</span>
        <h2>{pageTitle[page] || 'NutriGuard'}</h2>
        <p>Profile-aware nutrition, full-day timing, and progressive reports.</p>
      </div>
      <div className="desktop-header-actions">
        <ThemeToggle theme={theme} setTheme={setTheme} />
        <NotificationMenu
          notifications={notifications}
          open={notificationOpen}
          setOpen={setNotificationOpen}
          onMarkRead={onMarkNotificationRead}
          onRefresh={onRefreshNotifications}
        />
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
