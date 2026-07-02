import HealthyBackdrop from '../components/HealthyBackdrop'
import TopNav from '../components/TopNav'

export default function AuthPage({
  authMode,
  setAuthMode,
  theme,
  setTheme,
  name,
  setName,
  email,
  setEmail,
  password,
  setPassword,
  confirmPassword,
  setConfirmPassword,
  login,
  signup,
  loading,
  message,
}) {
  const isMissingAccount = message.toLowerCase().includes('account does not exist')

  return (
    <main className="app-frame auth-frame">
      <HealthyBackdrop />
      <TopNav
        theme={theme}
        setTheme={setTheme}
        rightContent={<button className="nav-cta" onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>{authMode === 'login' ? 'Sign up' : 'Login'}</button>}
      />
      <section className="auth-layout">
        <section className="auth-hero">
          <span className="eyebrow">Personal nutrition intelligence</span>
          <h1>NutriGuard</h1>
          <p>Build a daily nutrition timeline that understands health goals, deficiencies, supplements, and meal timing.</p>
          <div className="hero-pills">
            <span>Daily timing</span>
            <span>Profile-aware</span>
            <span>Gemini reports</span>
          </div>
        </section>
        <section className="auth-card">
          <div className="auth-switch">
            <button className={authMode === 'login' ? 'active' : ''} onClick={() => setAuthMode('login')}>Login</button>
            <button className={authMode === 'signup' ? 'active' : ''} onClick={() => setAuthMode('signup')}>Sign up</button>
          </div>
          {authMode === 'signup' && (
            <label>
              Name
              <input value={name} onChange={(event) => setName(event.target.value)} />
            </label>
          )}
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} />
          </label>
          {authMode === 'signup' && (
            <label>
              Confirm password
              <input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={8} />
            </label>
          )}
          <button onClick={authMode === 'login' ? login : signup} disabled={loading}>
            {authMode === 'login' ? 'Login' : 'Create account'}
          </button>
          {authMode === 'signup' && <p className="message">After signup, you’ll complete your profile journey.</p>}
          {message && <p className="message">{message}</p>}
          {isMissingAccount && (
            <button className="ghost-button" onClick={() => setAuthMode('signup')}>
              Create account
            </button>
          )}
        </section>
      </section>
    </main>
  )
}
