import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'
import RouteCard from './RouteCard.jsx'
import { routesForJourney } from '../data/demoRoutes.js'

const markerIcon = L.icon({ iconUrl, iconRetinaUrl, shadowUrl, iconSize: [25,41], iconAnchor: [12,41], popupAnchor: [1,-34], shadowSize: [41,41] })
function FitRoutes({ routes }) {
  const map = useMap()
  useEffect(() => { map.fitBounds(routes.flatMap(route => route.coordinates), { padding: [30,30] }) }, [map, routes])
  return null
}
export default function RouteMap({ journey }) {
  const [selected, setSelected] = useState('PUNE-A')
  const [tiles, setTiles] = useState('loading')
  const [routes] = useState(() => routesForJourney(journey))
  useEffect(() => {
    const timer = setTimeout(() => setTiles(current => current === 'loading' ? 'unavailable' : current), 10000)
    return () => clearTimeout(timer)
  }, [])
  if (!routes.length) return <p className="journey-confirmation" role="status">This map demonstration supports only Shivajinagar, Pune ↔ Pune Railway Station. Edit your journey to try this pair.</p>
  const points = routes[0].coordinates
  return <section className="route-section" aria-labelledby="routes-title">
    <h3 id="routes-title">Explore schematic routes</h3>
    <p>Demonstration only: these approximate Pune corridors are not verified road paths or navigation directions. No traffic, travel-time measurements, or AI predictions are provided. Date and time do not change this demonstration.</p>
    <div className="route-layout"><div>{routes.map(route => <RouteCard key={route.id} route={route} selected={route.id === selected} onSelect={setSelected} />)}</div>
      <div className="map-column">
        <p role="status">{tiles === 'loading' ? 'Loading OpenStreetMap tiles…' : tiles === 'unavailable' ? 'Map tiles are unavailable or incomplete. Schematic lines and route selection remain available; check your connection and reload to retry.' : 'Blue: selected route. Gray: alternative route.'}</p>
        <MapContainer className="route-map" center={points[0]} zoom={14} scrollWheelZoom={false}>
          <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' eventHandlers={{ tileerror: () => setTiles('unavailable'), load: () => setTiles(current => current === 'unavailable' ? current : 'ready') }} />
          <FitRoutes routes={routes} />
          {[...routes].sort((a,b) => Number(a.id === selected)-Number(b.id === selected)).map(route => <Polyline key={route.id} positions={route.coordinates} pathOptions={{ color: route.id === selected ? '#245bd6' : '#748399', weight: route.id === selected ? 7 : 5 }} eventHandlers={{ click: () => setSelected(route.id) }} />)}
          <Marker position={points[0]} icon={markerIcon}><Popup>Source: {journey.source}</Popup></Marker>
          <Marker position={points.at(-1)} icon={markerIcon}><Popup>Destination: {journey.destination}</Popup></Marker>
        </MapContainer>
      </div>
    </div>
  </section>
}
