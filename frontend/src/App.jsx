import { useEffect, useLayoutEffect, useState } from 'react'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'
import Results from './pages/Results.jsx'
import { navigationLinks } from './data/navigation.js'

function readLocation(hasJourney) {
  if (window.location.hash === '#results' && !hasJourney) {
    // Journey details deliberately live only in memory, never in history.
    window.history.replaceState(null, '', '#plan-journey')
  }
  return window.location.hash
}

export default function App() {
  const [journey, setJourney] = useState(null)
  const [hash, setHash] = useState(() => readLocation(false))
  const showingResults = hash === '#results' && journey !== null

  useEffect(() => {
    const syncLocation = () => setHash(readLocation(journey !== null))
    window.addEventListener('popstate', syncLocation)
    window.addEventListener('hashchange', syncLocation)
    return () => {
      window.removeEventListener('popstate', syncLocation)
      window.removeEventListener('hashchange', syncLocation)
    }
  }, [journey])

  useLayoutEffect(() => {
    if (!showingResults) {
      // Run after native history traversal restores its scroll/focus position.
      const frame = window.requestAnimationFrame(() => {
        const section = hash.slice(1) || 'home'
        document.getElementById(section)?.scrollIntoView()
        if (section === 'plan-journey') document.getElementById('start')?.focus({ preventScroll: true })
      })
      return () => window.cancelAnimationFrame(frame)
    }
  }, [hash, showingResults])

  function navigateHome(section) {
    navigate(`#${section}`)
  }

  function navigate(nextHash) {
    if (window.location.hash !== nextHash) window.history.pushState(null, '', nextHash)
    setHash(nextHash)
    if (window.location.hash === hash && !showingResults) {
      document.getElementById(nextHash.slice(1))?.scrollIntoView()
      if (nextHash === '#plan-journey') document.getElementById('start')?.focus({ preventScroll: true })
    }
  }

  function saveJourney(details) {
    setJourney(details)
    navigate('#results')
  }

  return (
    <>
      <a className="skip-link" href={showingResults ? '#results' : '#main-content'}>Skip to content</a>
      <Navbar onNavigate={navigateHome} showingResults={showingResults} />
      <div hidden={showingResults}><Home journey={journey} onSaveJourney={saveJourney} /></div>
      {showingResults && <Results journey={journey} onEdit={() => navigateHome('plan-journey')} />}
      <footer className="site-footer"><div className="container footer-content">
        <div><strong>Predictive Journey Planner</strong><p>Plan ahead. Travel smarter.</p></div>
        <nav aria-label="Footer navigation">{navigationLinks.map(({ id, label }) => <a key={id} href={`#${id}`} onClick={event => { event.preventDefault(); navigateHome(id) }}>{label}</a>)}</nav>
      </div></footer>
    </>
  )
}
