export default function RouteCard({ route, selected, onSelect }) {
  return <article className={`route-card ${selected ? 'selected' : ''}`}>
    <span className="badge">Demo Mode</span>
    <h3>{route.name}</h3><p>{route.id} · {selected ? 'Selected' : 'Alternative'}</p>
    <button type="button" className="button secondary" aria-pressed={selected} onClick={() => onSelect(route.id)}>{selected ? 'Selected Route' : 'Select Route'}</button>
  </article>
}
