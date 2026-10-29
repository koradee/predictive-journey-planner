import { useEffect, useMemo, useRef, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

const markerIcon = L.icon({
  iconUrl,
  iconRetinaUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function getRouteCoordinates(route) {
  if (route.coordinates && route.coordinates.length > 0) return route.coordinates
  if (route.geometry?.coordinates && route.geometry.coordinates.length > 0) {
    return route.geometry.coordinates.map(([lon, lat]) => [lat, lon])
  }
  return []
}

function FitRoutes({ routes }) {
  const map = useMap()
  useEffect(() => {
    const allPoints = routes.flatMap(getRouteCoordinates)
    if (allPoints.length === 0) return
    const fitRoutes = () => map.fitBounds(allPoints, { padding: [30, 30], animate: false })
    fitRoutes()
    map.on('resize', fitRoutes)
    return () => map.off('resize', fitRoutes)
  }, [map, routes])
  return null
}

function RouteLine({ route, selected, onSelect }) {
  const line = useRef(null)
  const routeId = route.route_id || route.id
  const positions = getRouteCoordinates(route)

  useEffect(() => {
    if (selected) line.current?.bringToFront()
    else line.current?.bringToBack()
  }, [selected])

  return (
    <Polyline
      ref={line}
      positions={positions}
      pathOptions={{ color: selected ? '#245bd6' : '#748399', weight: selected ? 7 : 5 }}
      eventHandlers={{ click: () => onSelect(routeId) }}
    />
  )
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
    load: () => {
      clearTimeout(timer.current)
      setTiles(failedTiles.current.size ? 'unavailable' : 'ready')
    },
  }), [])

  useEffect(() => () => clearTimeout(timer.current), [])

  const firstRoutePoints = routes.length > 0 ? getRouteCoordinates(routes[0]) : []
  const startPoint = firstRoutePoints[0] || [18.5314, 73.8446]
  const endPoint = firstRoutePoints.at(-1) || [18.5285, 73.8743]

  return (
    <div className="map-column">
      <p role="status">
        {tiles === 'loading'
          ? 'Loading OpenStreetMap tiles…'
          : tiles === 'slow'
          ? 'Map tiles are taking longer than expected. Road network lines remain available while loading continues.'
          : tiles === 'unavailable'
          ? 'Map tiles are unavailable or incomplete. Road network lines and route selection remain available; check your connection and reload to retry.'
          : 'Blue: selected route. Gray: alternative route.'}
      </p>
      <MapContainer className="route-map" center={startPoint} zoom={14} scrollWheelZoom={false}>
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          eventHandlers={tileEvents}
        />
        <FitRoutes routes={routes} />
        {routes.map(route => {
          const routeId = route.route_id || route.id
          return (
            <RouteLine
              key={routeId}
              route={route}
              selected={routeId === selected}
              onSelect={onSelect}
            />
          )
        })}
        <Marker position={startPoint} icon={markerIcon} alt={`Source: ${journey.source}`}>
          <Popup>Source: {journey.source}</Popup>
        </Marker>
        <Marker position={endPoint} icon={markerIcon} alt={`Destination: ${journey.destination}`}>
          <Popup>Destination: {journey.destination}</Popup>
        </Marker>
      </MapContainer>
    </div>
  )
}
