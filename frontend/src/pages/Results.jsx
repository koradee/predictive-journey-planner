import { useEffect, useRef, useState } from 'react'
import JourneySummary from '../components/JourneySummary.jsx'
import RouteCard from '../components/RouteCard.jsx'
import RouteMap from '../components/RouteMap.jsx'
import { calculateRoutes } from '../utils/api.js'

export default function Results({ journey, onEdit }) {
  const [routes, setRoutes] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [retryCount, setRetryCount] = useState(0)
  const heading = useRef(null)

  useEffect(() => {
    heading.current?.focus()
    window.scrollTo(0, 0)
  }, [])

  useEffect(() => {
    let active = true

    async function loadRoutes() {
      try {
        const data = await calculateRoutes(journey)
        if (!active) return
        const fetchedRoutes = data.routes || []
        setRoutes(fetchedRoutes)
        if (fetchedRoutes.length > 0) {
          setSelected(fetchedRoutes[0].id)
        }
      } catch (err) {
        if (!active) return
        setError(err.message || 'Unable to retrieve routes from the backend.')
        setRoutes([])
        setSelected(null)
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadRoutes()
    return () => {
      active = false
    }
  }, [journey, retryCount])

  function handleRetry() {
    setLoading(true)
    setError(null)
    setRetryCount(c => c + 1)
  }

  return (
    <main id="results" className="container section results-page">
      <span className="badge">Pune OSM Pilot</span>
      <h1 ref={heading} tabIndex="-1">Your Journey Overview</h1>
      <button type="button" className="button secondary" onClick={onEdit}>
        Edit Journey
      </button>
      <JourneySummary journey={journey} />

      {loading && (
        <section className="loading-banner" role="status" aria-live="polite">
          <h2>Calculating Pune road routes…</h2>
          <p>Querying the FastAPI backend using the real OpenStreetMap road network.</p>
        </section>
      )}

      {!loading && error && (
        <section className="error-banner" role="alert">
          <h2>Route Calculation Failed</h2>
          <p>{error}</p>
          <div className="error-actions">
            <button type="button" className="button primary" onClick={handleRetry}>
              Retry
            </button>
            <button type="button" className="button secondary" onClick={onEdit}>
              Edit Journey
            </button>
          </div>
        </section>
      )}

      {!loading && !error && routes.length > 0 && (
        <section className="route-section" aria-labelledby="routes-title">
          <h2 id="routes-title">Explore your route options</h2>
          <p>
            Calculated via OpenStreetMap road network for Pune. Showing actual shortest road geometry and distance comparisons.
          </p>
          <div className="route-layout">
            <div>
              {routes.map(route => (
                <RouteCard
                  key={route.id}
                  route={route}
                  selected={selected === route.id}
                  onSelect={setSelected}
                />
              ))}
            </div>
            <RouteMap
              journey={journey}
              routes={routes}
              selected={selected}
              onSelect={setSelected}
            />
          </div>
        </section>
      )}

      {!loading && !error && routes.length === 0 && (
        <section className="journey-confirmation" role="status">
          <h2>No routes found</h2>
          <p>
            No valid road path found between the specified locations. Please use Edit Journey to check your inputs.
          </p>
        </section>
      )}

      <section className="journey-confirmation" aria-labelledby="prediction-title">
        <h2 id="prediction-title">Travel insights</h2>
        <dl className="journey-details">
          <div><dt>Traffic prediction</dt><dd>Not available (research benchmark)</dd></div>
          <div><dt>Predicted travel time</dt><dd>Not available (speeds require real-time sensors)</dd></div>
          <div><dt>Expected delay</dt><dd>Not available</dd></div>
          <div><dt>Best departure time</dt><dd>Not available</dd></div>
        </dl>
        <p>
          Live traffic forecasts and delay predictions are separate research benchmark activities (METR-LA); they are not connected to Pune road routes. Estimated durations do not include AI predictions.
        </p>
      </section>
    </main>
  )
}
