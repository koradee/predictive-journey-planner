const API_BASE = import.meta.env?.VITE_API_BASE_URL || ''

export class ApiError extends Error {
  constructor(message, status = 0, code = 'NETWORK_OR_SERVER_ERROR') {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`)
    if (!res.ok) throw new ApiError(`Health check failed with status ${res.status}`, res.status)
    return await res.json()
  } catch (err) {
    if (err instanceof ApiError) throw err
    throw new ApiError('Unable to connect to the FastAPI backend service.', 0, 'CONNECTION_REFUSED')
  }
}

export async function checkBackendReady() {
  try {
    const res = await fetch(`${API_BASE}/api/ready`)
    const data = await res.json()
    if (!res.ok) {
      throw new ApiError(data.error || 'Routing data is not ready', res.status, 'ROUTING_DATA_NOT_READY')
    }
    return data
  } catch (err) {
    if (err instanceof ApiError) throw err
    throw new ApiError('Failed to query backend readiness.', 0, 'CONNECTION_REFUSED')
  }
}

export async function calculateRoutes(journey) {
  const payload = {
    source: journey.source,
    destination: journey.destination,
    travelDate: journey.travelDate,
    departureTime: journey.departureTime,
    alternatives: 3,
    objective: 'distance',
  }

  let res
  try {
    res = await fetch(`${API_BASE}/api/routes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
  } catch {
    throw new ApiError(
      `Cannot connect to FastAPI backend server (${API_BASE || 'http://127.0.0.1:8000'}). Please verify the backend is running.`,
      0,
      'CONNECTION_FAILED',
    )
  }

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    const detail = data.detail || (res.status === 404 ? 'Routing endpoint not found' : `Request failed (${res.status})`)
    const code = data.code || `HTTP_${res.status}`
    throw new ApiError(detail, res.status, code)
  }

  // Normalize route items: ensure coordinates is an array of [lat, lon]
  const routes = (data.routes || []).map((route, index) => {
    // If route already provides coordinates [lat, lon], use them;
    // Otherwise convert GeoJSON geometry.coordinates [lon, lat] -> [lat, lon]
    const leafletCoords = route.coordinates || route.geometry?.coordinates?.map(([lon, lat]) => [lat, lon]) || []
    const name = route.name || `Route ${index + 1} (${route.distance_km ? `${route.distance_km.toFixed(2)} km` : ''})`
    return {
      ...route,
      id: route.route_id,
      name,
      coordinates: leafletCoords,
      isReal: true,
    }
  })

  return {
    ...data,
    routes,
  }
}
