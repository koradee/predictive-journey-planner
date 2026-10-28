import { useState } from 'react'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'

export default function App() {
  const [journey, setJourney] = useState(null)

  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <Navbar />
      <Home journey={journey} onSaveJourney={setJourney} />
    </>
  )
}
