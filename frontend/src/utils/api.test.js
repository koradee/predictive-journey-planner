import assert from 'node:assert/strict'
import test from 'node:test'
import { ApiError, calculateRoutes } from './api.js'

test('calculateRoutes throws ApiError when fetch fails', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => {
    throw new Error('Connection refused')
  }

  try {
    await assert.rejects(
      async () => {
        await calculateRoutes({
          source: 'Shivajinagar, Pune',
          destination: 'Pune Railway Station',
          travelDate: '2026-10-30',
          departureTime: '12:00',
        })
      },
      (err) => {
        assert.ok(err instanceof ApiError)
        assert.equal(err.code, 'CONNECTION_FAILED')
        assert.ok(err.message.includes('Cannot connect'))
        return true
      },
    )
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('calculateRoutes correctly parses 400 error from backend', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => ({
    ok: false,
    status: 400,
    json: async () => ({
      detail: 'Location unsupported',
      code: 'unsupported_location',
    }),
  })

  try {
    await assert.rejects(
      async () => {
        await calculateRoutes({
          source: 'Unknown Place',
          destination: 'Pune Railway Station',
        })
      },
      (err) => {
        assert.ok(err instanceof ApiError)
        assert.equal(err.status, 400)
        assert.equal(err.code, 'unsupported_location')
        assert.equal(err.message, 'Location unsupported')
        return true
      },
    )
  } finally {
    globalThis.fetch = originalFetch
  }
})

test('calculateRoutes normalizes geometry and coordinates', async () => {
  const originalFetch = globalThis.fetch
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      schema_version: 'pune-routing-v1',
      routes: [
        {
          route_id: 'pune-test-123',
          distance_km: 3.35,
          geometry: {
            type: 'LineString',
            coordinates: [
              [73.8446, 18.5314],
              [73.8743, 18.5285],
            ],
          },
        },
      ],
    }),
  })

  try {
    const result = await calculateRoutes({
      source: 'Shivajinagar, Pune',
      destination: 'Pune Railway Station',
    })

    assert.equal(result.routes.length, 1)
    const route = result.routes[0]
    assert.equal(route.id, 'pune-test-123')
    assert.ok(route.isReal)
    // Leaflet coordinates should be [lat, lon]
    assert.deepEqual(route.coordinates, [
      [18.5314, 73.8446],
      [18.5285, 73.8743],
    ])
  } finally {
    globalThis.fetch = originalFetch
  }
})
