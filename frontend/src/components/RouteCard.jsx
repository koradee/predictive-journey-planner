export default function RouteCard({ route, selected, onSelect }) {
  const routeId = route.route_id || route.id
  const badgeLabel = route.isReal || route.route_id ? 'Real OSM Route' : 'Demo Mode'
  const distanceLabel = typeof route.distance_km === 'number'
    ? `${route.distance_km.toFixed(2)} km`
    : null

  return (
    <article className={`route-card ${selected ? 'selected' : ''}`}>
      <span className="badge">{badgeLabel}</span>
      <h3>{route.name || `Route ${routeId}`}</h3>
      <p>
        {distanceLabel && <strong>Distance: {distanceLabel} · </strong>}
        {selected ? 'Selected Route' : 'Alternative Route'}
      </p>
      <button
        type="button"
        className="button secondary"
        aria-pressed={selected}
        onClick={() => onSelect(routeId)}
      >
        {selected ? 'Selected Route' : 'Select Route'}
      </button>
    </article>
  )
}
