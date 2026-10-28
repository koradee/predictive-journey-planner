import { useState } from 'react'
import { flushSync } from 'react-dom'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'
import Results from './pages/Results.jsx'

export default function App() {
  const [journey, setJourney] = useState(null)
  const [showingResults, setShowingResults] = useState(false)

  function navigateHome(section) {
    flushSync(() => setShowingResults(false))
    window.history.replaceState(null, '', `#${section}`)
    document.getElementById(section)?.scrollIntoView()
    if (section === 'plan-journey') document.getElementById('start')?.focus({ preventScroll: true })
  }

  function saveJourney(details) {
    setJourney(details)
    setShowingResults(true)
    window.history.replaceState(null, '', '#results')
  }

  return (
    <>
      <a className="skip-link" href={showingResults ? '#results' : '#main-content'}>Skip to content</a>
      <Navbar onNavigate={navigateHome} showingResults={showingResults} />
      <div hidden={showingResults}><Home journey={journey} onSaveJourney={saveJourney} /></div>
      {showingResults && <Results journey={journey} onEdit={() => navigateHome('plan-journey')} />}
    </>
  )
}
