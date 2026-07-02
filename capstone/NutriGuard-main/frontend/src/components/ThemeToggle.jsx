export default function ThemeToggle({ theme, setTheme }) {
  return (
    <button
      className={`theme-toggle ${theme === 'dark' ? 'dark' : ''}`}
      aria-label="Toggle dark mode"
      title="Toggle dark mode"
      onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
    >
      <span className="theme-symbol">{theme === 'light' ? '☀' : '◐'}</span>
      <span className="theme-track">
        <span className="theme-knob" />
      </span>
    </button>
  )
}
