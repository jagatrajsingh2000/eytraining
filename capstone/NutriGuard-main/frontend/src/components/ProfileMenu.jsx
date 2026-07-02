export default function ProfileMenu({ user, open, setOpen, onUpdateProfile, onLogout }) {
  return (
    <div className="profile-menu">
      <button className="profile-button" onClick={() => setOpen((current) => !current)}>
        {user.email.slice(0, 1).toUpperCase()}
      </button>
      {open && (
        <div className="profile-popover">
          <strong>{user.email}</strong>
          <button className="profile-action" onClick={onUpdateProfile}>Update profile</button>
          <button className="profile-action danger-action" onClick={onLogout}>Logout</button>
        </div>
      )}
    </div>
  )
}
