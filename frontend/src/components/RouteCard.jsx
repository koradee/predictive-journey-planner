export default function RouteCard({ route, selected, onSelect }) {
  return <article className={`route-card ${selected ? 'selected' : ''}`}>
    <span className="badge">Schematic demonstration</span>
    <h3>{route.name}</h3><p>{route.id}</p>
    <button type="button" className="button secondary" aria-pressed={selected} onClick={() => onSelect(route.id)}>{selected ? 'Selected Route' : 'Select Route'}</button>
  </article>
}
