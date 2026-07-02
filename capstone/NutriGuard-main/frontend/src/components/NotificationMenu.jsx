export default function NotificationMenu({ notifications, open, setOpen, onMarkRead, onRefresh }) {
  const unreadCount = notifications.filter((item) => item.status === 'unread').length

  return (
    <div className="notification-menu">
      <button className="notification-button" onClick={() => setOpen((current) => !current)}>
        <svg className="notification-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M18 16v-5a6 6 0 0 0-12 0v5l-2 2h16l-2-2Z" />
          <path d="M10 20a2 2 0 0 0 4 0" />
        </svg>
        <span>Alerts</span>
        {unreadCount > 0 && <b>{unreadCount}</b>}
      </button>
      {open && (
        <div className="notification-popover">
          <div className="notification-popover-head">
            <strong>Meal reminders</strong>
            <button onClick={onRefresh}>Refresh</button>
          </div>
          {notifications.length ? (
            <div className="notification-list">
              {notifications.map((notification) => (
                <article className={`notification-card ${notification.status}`} key={notification.id}>
                  <div>
                    <strong>{notification.title}</strong>
                    <p>{notification.message}</p>
                    <small>{notification.notification_date}</small>
                  </div>
                  {notification.status === 'unread' && (
                    <button onClick={() => onMarkRead(notification.id)}>Read</button>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <p className="muted">No meal reminders right now.</p>
          )}
        </div>
      )}
    </div>
  )
}
