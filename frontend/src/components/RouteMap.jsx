import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

const markerIcon = L.icon({ iconUrl, iconRetinaUrl, shadowUrl, iconSize: [25,41], iconAnchor: [12,41], popupAnchor: [1,-34], shadowSize: [41,41] })
function FitRoutes({ routes }) {
  const map = useMap()
  useEffect(() => {
    const fitRoutes = () => map.fitBounds(routes.flatMap(route => route.coordinates), { padding: [30,30], animate: false })
    fitRoutes()
    map.on('resize', fitRoutes)
    return () => map.off('resize', fitRoutes)
  }, [map, routes])
  return null
}
function RouteLine({ route, selected, onSelect }) {
  const line = useRef(null)
  useEffect(() => {
    if (selected) line.current?.bringToFront()
    else line.current?.bringToBack()
  }, [selected])
  return <Polyline ref={line} positions={route.coordinates} pathOptions={{ color: selected ? '#245bd6' : '#748399', weight: selected ? 7 : 5 }} eventHandlers={{ click: () => onSelect(route.id) }} />
}

export default function RouteMap({ journey, routes, selected, onSelect }) {
  const [tiles, setTiles] = useState('loading')
  const timer = useRef(null)
  const failedTiles = useRef(new Set())
  const tileEvents = useMemo(() => ({
    loading: () => {
      clearTimeout(timer.current)
      setTiles(failedTiles.current.size ? 'unavailable' : 'loading')
      timer.current = setTimeout(() => {
        setTiles(current => current === 'loading' ? 'slow' : current)
      }, 10000)
    },
    tileerror: ({ tile }) => {
      failedTiles.current.add(tile)
      setTiles('unavailable')
    },
    tileload: ({ tile }) => { failedTiles.current.delete(tile) },
    tileunload: ({ tile, target }) => {
      failedTiles.current.delete(tile)
      if (!target.isLoading() && !failedTiles.current.size) setTiles('ready')
    },
    // Leaflet fires load after both successes and failures; retain real failures.
    load: () => {
      clearTimeout(timer.current)
      setTiles(failedTiles.current.size ? 'unavailable' : 'ready')
    },
  }), [])
  useEffect(() => () => clearTimeout(timer.current), [])
  const points = routes[0].coordinates
  return (
      <div className="map-column">
        <p role="status">{tiles === 'loading' ? 'Loading OpenStreetMap tiles…' : tiles === 'slow' ? 'Map tiles are taking longer than expected. Schematic routes remain available while loading continues.' : tiles === 'unavailable' ? 'Map tiles are unavailable or incomplete. Schematic lines and route selection remain available; check your connection and reload to retry.' : 'Blue: selected route. Gray: alternative route.'}</p>
        <MapContainer className="route-map" center={points[0]} zoom={14} scrollWheelZoom={false}>
          <TileLayer url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' eventHandlers={tileEvents} />
          <FitRoutes routes={routes} />
          {routes.map(route => <RouteLine key={route.id} route={route} selected={route.id === selected} onSelect={onSelect} />)}
          <Marker position={points[0]} icon={markerIcon} alt={`Source: ${journey.source}`}><Popup>Source: {journey.source}</Popup></Marker>
          <Marker position={points.at(-1)} icon={markerIcon} alt={`Destination: ${journey.destination}`}><Popup>Destination: {journey.destination}</Popup></Marker>
        </MapContainer>
      </div>
  )
}
