import { useEffect, useState } from 'react'

const links = [
  { id: 'home', label: 'Home' },
  { id: 'plan-journey', label: 'Plan Journey' },
  { id: 'how-it-works', label: 'How It Works' },
  { id: 'about', label: 'About' },
]

export default function Navbar({ onNavigate, showingResults }) {
  const [active, setActive] = useState('home')

  useEffect(() => {
    const updateActive = () => {
      if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) {
        setActive('about')
        return
      }
      const marker = window.scrollY + (window.innerWidth <= 600 ? 160 : 112)
      const current = [...links].reverse().find(({ id }) => {
        const section = document.getElementById(id)
        return section && section.offsetTop <= marker
      })
      setActive(current?.id ?? 'home')
    }
    updateActive()
    window.addEventListener('scroll', updateActive, { passive: true })
    window.addEventListener('resize', updateActive)
    return () => {
      window.removeEventListener('scroll', updateActive)
      window.removeEventListener('resize', updateActive)
    }
  }, [])

  return (
    <header className="site-header">
      <nav className="container navbar" onClick={event => {
        const link = event.target.closest('a[href^="#"]')
        if (link) { event.preventDefault(); onNavigate(link.hash.slice(1)) }
      }} aria-label="Main navigation">
        <a className="brand" href="#home">
          <span className="brand-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <circle cx="6" cy="6" r="3" />
              <circle cx="18" cy="18" r="3" />
              <path d="M9 6h7a4 4 0 0 1 0 8H8a4 4 0 0 0 0 8h3" />
            </svg>
          </span>
          <span>Predictive Journey Planner</span>
        </a>
        <div className="nav-links">
          {links.map(({ id, label }) => (
            <a key={id} href={`#${id}`} className={`${id === 'plan-journey' ? 'nav-cta' : ''} ${!showingResults && active === id ? 'active' : ''}`}
              aria-current={!showingResults && active === id ? 'location' : undefined}>
              {label}
            </a>
          ))}
        </div>
      </nav>
    </header>
  )
}
