import assert from 'node:assert/strict'
import test from 'node:test'
import { demoRoutes, routesForJourney } from './demoRoutes.js'

test('supported Pune locations match despite case, commas, and whitespace', () => {
  const routes = routesForJourney({ source: ' SHIVAJINAGAR,   Pune ', destination: 'pune railway station' })
  assert.equal(routes.length, 2)
  assert.ok(routes.every(route => route.isDemo))
  assert.deepEqual(routes[0].coordinates[0], routes[1].coordinates[0])
  assert.deepEqual(routes[0].coordinates.at(-1), routes[1].coordinates.at(-1))
})

test('reverse journeys reverse geometry without modifying demo data', () => {
  const original = structuredClone(demoRoutes)
  const reversed = routesForJourney({ source: 'Pune Railway Station', destination: 'Shivajinagar' })
  assert.deepEqual(reversed[0].coordinates, [...original[0].coordinates].reverse())
  assert.deepEqual(demoRoutes, original)
  assert.notEqual(reversed[0].coordinates, demoRoutes[0].coordinates)
})

test('unsupported journeys do not invent routes', () => {
  assert.deepEqual(routesForJourney({ source: 'Mumbai', destination: 'Delhi' }), [])
})
