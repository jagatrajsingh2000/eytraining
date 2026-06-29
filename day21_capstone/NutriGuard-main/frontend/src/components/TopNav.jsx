import Brand from './Brand'
import ThemeToggle from './ThemeToggle'

export default function TopNav({ theme, setTheme, rightContent }) {
  return (
    <header className="app-navbar">
      <Brand compact />
      <div className="top-actions">
        <ThemeToggle theme={theme} setTheme={setTheme} />
        {rightContent}
      </div>
    </header>
  )
}
