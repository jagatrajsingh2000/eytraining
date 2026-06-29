import { useEffect, useState } from 'react'
import { apiRequest } from './api'
import DashboardHeader from './components/DashboardHeader'
import HealthyBackdrop from './components/HealthyBackdrop'
import Sidebar from './components/Sidebar'
import AuthPage from './pages/AuthPage'
import HistoryPage from './pages/HistoryPage'
import MealPage from './pages/MealPage'
import ProfilePage from './pages/ProfilePage'
import ReportPage from './pages/ReportPage'
import { todayInputDate } from './utils/meal'

function App() {
  const [authMode, setAuthMode] = useState('login')
  const [page, setPage] = useState('meal')
  const [theme, setTheme] = useState('light')
  const [menuOpen, setMenuOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [name, setName] = useState('Jagat')
  const [email, setEmail] = useState('jagat@example.com')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [user, setUser] = useState(null)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const [goals, setGoals] = useState(['reduce_deficiency'])
  const [dietType, setDietType] = useState('vegetarian')
  const [healthConditionsText, setHealthConditionsText] = useState('I have iron deficiency')
  const [deficienciesText, setDeficienciesText] = useState('Low ferritin and vitamin D')
  const [supplementsText, setSupplementsText] = useState('I take an iron tablet in the morning')
  const [healthReportText, setHealthReportText] = useState('')
  const [parsedProfile, setParsedProfile] = useState(null)

  const [mealText, setMealText] = useState('')
  const [foodsText, setFoodsText] = useState('poha')
  const [drinksText, setDrinksText] = useState('tea')
  const [mealSupplementsText, setMealSupplementsText] = useState('')
  const [mealNotesText, setMealNotesText] = useState('')
  const [mealType, setMealType] = useState('breakfast')
  const [mealTime, setMealTime] = useState(() => new Date().toISOString().slice(0, 16))
  const [mealId, setMealId] = useState(null)
  const [selectedDate, setSelectedDate] = useState(todayInputDate())
  const [report, setReport] = useState(null)
  const [reportDetails, setReportDetails] = useState(null)
  const [history, setHistory] = useState([])

  const resetAuthMessage = () => setMessage('')

  const loadProfile = async (userId = user?.id) => {
    if (!userId) return
    try {
      const data = await apiRequest(`/users/${userId}/profile`)
      setGoals(data.goals?.length ? data.goals : [data.goal || 'reduce_deficiency'])
      setDietType(data.diet_type || 'vegetarian')
      setHealthConditionsText(data.health_conditions_text || (data.health_conditions || []).join(', '))
      setDeficienciesText(data.deficiencies_text || (data.deficiencies || []).join(', '))
      setSupplementsText(data.supplements_text || (data.supplements || []).join(', '))
      setHealthReportText(data.health_report_text || '')
      setParsedProfile(data)
    } catch {
      setParsedProfile(null)
    }
  }

  const loadHistory = async (userId = user?.id) => {
    if (!userId) return
    try {
      setHistory(await apiRequest(`/users/${userId}/meals`))
    } catch {
      setHistory([])
    }
  }

  const loadReportDetails = async (userId = user?.id, date = selectedDate) => {
    if (!userId) return
    try {
      const query = date ? `?report_date=${date}` : ''
      const data = await apiRequest(`/users/${userId}/daily-report/details${query}`)
      setReportDetails(data)
      setReport(data.combined_report)
    } catch {
      setReportDetails(null)
    }
  }

  const login = async () => {
    setLoading(true)
    resetAuthMessage()
    try {
      const data = await apiRequest('/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      setUser(data)
      await loadProfile(data.id)
      await loadHistory(data.id)
      await loadReportDetails(data.id, selectedDate)
      setPage(data.has_profile ? 'meal' : 'profile')
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  const signup = async () => {
    setLoading(true)
    resetAuthMessage()
    if (password !== confirmPassword) {
      setMessage('Passwords do not match')
      setLoading(false)
      return
    }
    try {
      const data = await apiRequest('/users/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      })
      setUser(data)
      setPage('profile')
      setMessage('Account created. Complete your profile to personalize reports.')
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  const saveProfile = async (nextPage = 'meal') => {
    if (!user) return
    setLoading(true)
    resetAuthMessage()
    try {
      const data = await apiRequest(`/users/${user.id}/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goals,
          diet_type: dietType,
          health_conditions_text: healthConditionsText,
          deficiencies_text: deficienciesText,
          supplements_text: supplementsText,
          health_report_text: healthReportText,
        }),
      })
      setParsedProfile(data)
      setMessage('Profile saved and normalized for the nutrition agents.')
      setPage(nextPage)
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  const submitMeal = async () => {
    if (!user) return
    setLoading(true)
    setReport(null)
    try {
      const data = await apiRequest('/meals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          meal_text: mealText || null,
          foods_text: foodsText,
          drinks_text: drinksText,
          supplements_text: mealSupplementsText,
          notes_text: mealNotesText,
          meal_type: mealType,
          meal_time: mealTime ? new Date(mealTime).toISOString() : null,
        }),
      })
      setMealId(data.meal_log_id)
      setReport({ status: data.status, summary: data.message, recommendations: [], safety_note: '' })
      setPage('report')
      loadHistory(user.id)
    } catch (error) {
      setReport({ status: 'ERROR', summary: error.message, recommendations: [], safety_note: '' })
    } finally {
      setLoading(false)
    }
  }

  const readReportFile = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    setHealthReportText(await file.text())
    setMessage(`Loaded ${file.name}. Save profile to use this report.`)
  }

  const toggleGoal = (value) => {
    setGoals((current) => {
      if (!current.includes(value)) return [...current, value]
      const next = current.filter((item) => item !== value)
      return next.length ? next : current
    })
  }

  const logout = () => {
    setUser(null)
    setProfileOpen(false)
    setMessage('')
  }

  const showProfile = () => {
    setPage('profile')
    setProfileOpen(false)
  }

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  useEffect(() => {
    if (user && page === 'report') {
      loadReportDetails(user.id, selectedDate)
    }
  }, [selectedDate])

  useEffect(() => {
    if (!mealId) return undefined
    const timer = window.setInterval(async () => {
      try {
        const query = selectedDate ? `?report_date=${selectedDate}` : ''
        const data = await apiRequest(`/users/${user.id}/daily-report/details${query}`)
        setReportDetails(data)
        setReport(data.combined_report)
        if (data.status === 'COMPLETED') {
          window.clearInterval(timer)
          loadHistory()
        }
      } catch (error) {
        setReport({ status: 'ERROR', summary: error.message, recommendations: [], safety_note: '' })
        window.clearInterval(timer)
      }
    }, 3000)
    return () => window.clearInterval(timer)
  }, [mealId, selectedDate])

  if (!user) {
    return (
      <AuthPage
        authMode={authMode}
        setAuthMode={setAuthMode}
        theme={theme}
        setTheme={setTheme}
        name={name}
        setName={setName}
        email={email}
        setEmail={setEmail}
        password={password}
        setPassword={setPassword}
        confirmPassword={confirmPassword}
        setConfirmPassword={setConfirmPassword}
        login={login}
        signup={signup}
        loading={loading}
        message={message}
      />
    )
  }

  return (
    <main className="dashboard-frame">
      <HealthyBackdrop />
      <button className="menu-launcher" onClick={() => setMenuOpen(true)} aria-label="Open menu">
        <span />
        <span />
        <span />
      </button>
      {menuOpen && <button className="drawer-overlay" onClick={() => setMenuOpen(false)} aria-label="Close menu" />}
      <div className="dashboard-shell">
        <Sidebar page={page} menuOpen={menuOpen} setMenuOpen={setMenuOpen} setPage={setPage} loadReportDetails={loadReportDetails} loadHistory={loadHistory} />
        <section className="main-area">
          <DashboardHeader
            page={page}
            theme={theme}
            setTheme={setTheme}
            user={user}
            profileOpen={profileOpen}
            setProfileOpen={setProfileOpen}
            onUpdateProfile={showProfile}
            onLogout={logout}
          />
          {page === 'profile' && (
            <ProfilePage
              goals={goals}
              toggleGoal={toggleGoal}
              dietType={dietType}
              setDietType={setDietType}
              healthConditionsText={healthConditionsText}
              setHealthConditionsText={setHealthConditionsText}
              deficienciesText={deficienciesText}
              setDeficienciesText={setDeficienciesText}
              supplementsText={supplementsText}
              setSupplementsText={setSupplementsText}
              healthReportText={healthReportText}
              setHealthReportText={setHealthReportText}
              readReportFile={readReportFile}
              saveProfile={saveProfile}
              loading={loading}
              parsedProfile={parsedProfile}
              message={message}
            />
          )}
          {page === 'meal' && (
            <MealPage
              mealType={mealType}
              setMealType={setMealType}
              mealTime={mealTime}
              setMealTime={setMealTime}
              foodsText={foodsText}
              setFoodsText={setFoodsText}
              drinksText={drinksText}
              setDrinksText={setDrinksText}
              mealSupplementsText={mealSupplementsText}
              setMealSupplementsText={setMealSupplementsText}
              mealNotesText={mealNotesText}
              setMealNotesText={setMealNotesText}
              mealText={mealText}
              setMealText={setMealText}
              submitMeal={submitMeal}
              loading={loading}
            />
          )}
          {page === 'report' && (
            <ReportPage
              selectedDate={selectedDate}
              setSelectedDate={setSelectedDate}
              loadReportDetails={() => loadReportDetails(user.id)}
              report={report}
              reportDetails={reportDetails}
            />
          )}
          {page === 'history' && (
            <HistoryPage
              selectedDate={selectedDate}
              setSelectedDate={setSelectedDate}
              history={history}
              loadHistory={() => loadHistory()}
            />
          )}
        </section>
      </div>
    </main>
  )
}

export default App
