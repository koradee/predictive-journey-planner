import { useEffect, useRef, useState } from 'react'
import JourneySummary from '../components/JourneySummary.jsx'
import RouteCard from '../components/RouteCard.jsx'
import RouteMap from '../components/RouteMap.jsx'
import { routesForJourney } from '../data/demoRoutes.js'

export default function Results({ journey, onEdit }) {
  const [routes] = useState(() => routesForJourney(journey))
  const [selected, setSelected] = useState(routes[0]?.id ?? null)
  const heading = useRef(null)
  useEffect(() => { heading.current?.focus(); window.scrollTo(0, 0) }, [])

  return <main id="results" className="container section results-page">
    <span className="badge">Demo Mode</span>
    <h1 ref={heading} tabIndex="-1">Your Journey Overview</h1>
    <button type="button" className="button secondary" onClick={onEdit}>Edit Journey</button>
    <JourneySummary journey={journey} />
    {routes.length ? <section className="route-section" aria-labelledby="routes-title">
      <h2 id="routes-title">Explore your route options</h2>
      <p>These approximate Pune corridors are schematic, not verified road paths or navigation directions. Date and time do not change this demonstration.</p>
      <div className="route-layout">
        <div>{routes.map(route => <RouteCard key={route.id} route={route} selected={selected === route.id} onSelect={setSelected} />)}</div>
        <RouteMap journey={journey} routes={routes} selected={selected} onSelect={setSelected} />
      </div>
    </section> : <section className="journey-confirmation" role="status"><h2>Route data unavailable</h2><p>Routes are currently available in Demo Mode only for Shivajinagar, Pune ↔ Pune Railway Station. Your entered journey is preserved. Use Edit Journey to try the supported pair.</p></section>}
    <section className="journey-confirmation" aria-labelledby="prediction-title">
      <h2 id="prediction-title">Travel insights</h2>
      <dl className="journey-details">
        <div><dt>Traffic prediction</dt><dd>Not available</dd></div>
        <div><dt>Predicted travel time</dt><dd>Not available</dd></div>
        <div><dt>Expected delay</dt><dd>Not available</dd></div>
        <div><dt>Best departure time</dt><dd>Not available</dd></div>
      </dl>
      <p>Traffic forecasts, travel times, and departure recommendations are unavailable in Demo Mode.</p>
    </section>
  </main>
}
