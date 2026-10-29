import assert from 'node:assert/strict'
import test from 'node:test'
import { localDate, validateJourney } from './journey.js'

const now = new Date(2026, 9, 29, 12, 30, 15)
const valid = {
  source: 'Shivajinagar, Pune', destination: 'Pune Railway Station',
  travelDate: '2026-10-30', departureTime: '12:00',
}

test('required fields reject empty and whitespace-only input', () => {
  const result = validateJourney({ source: '  ', destination: '', travelDate: '', departureTime: '' }, now)
  assert.deepEqual(Object.keys(result.errors), ['source', 'destination', 'travelDate', 'departureTime'])
  assert.equal(result.journey, null)
})

test('identical locations are rejected after normalizing case and whitespace', () => {
  const result = validateJourney({ ...valid, source: ' Pune  Railway Station ', destination: 'pune railway station' }, now)
  assert.ok(result.errors.destination)
  assert.equal(result.journey, null)
})

test('accepted locations are normalized without mutating entered values', () => {
  const values = { ...valid, source: ' Shivajinagar,   Pune ' }
  const result = validateJourney(values, now)
  assert.deepEqual(result.errors, {})
  assert.equal(result.journey.source, 'Shivajinagar, Pune')
  assert.equal(values.source, ' Shivajinagar,   Pune ')
})

test('past dates and past times today are rejected', () => {
  assert.ok(validateJourney({ ...valid, travelDate: '2026-10-28' }, now).errors.travelDate)
  assert.ok(validateJourney({ ...valid, travelDate: '2026-10-29', departureTime: '12:29' }, now).errors.departureTime)
  assert.ok(validateJourney({ ...valid, travelDate: '2026-10-29', departureTime: '12:30' }, now).errors.departureTime)
})

test('future departures today and on a later date are accepted', () => {
  assert.deepEqual(validateJourney({ ...valid, travelDate: '2026-10-29', departureTime: '12:31' }, now).errors, {})
  assert.deepEqual(validateJourney(valid, now).errors, {})
})

test('invalid calendar dates and times are rejected', () => {
  for (const patch of [{ travelDate: '2026-02-30' }, { travelDate: 'invalid' }, { departureTime: '25:00' }, { departureTime: 'invalid' }]) {
    assert.equal(validateJourney({ ...valid, ...patch }, now).journey, null)
  }
})

test('each submission validates against the supplied current local time', () => {
  const values = { ...valid, travelDate: '2026-10-29', departureTime: '12:31' }
  assert.ok(validateJourney(values, now).journey)
  assert.equal(validateJourney(values, new Date(2026, 9, 29, 12, 32)).journey, null)
})

test('local calendar day and departure validation agree around midnight', () => {
  const late = new Date(2026, 9, 29, 23, 59)
  assert.equal(localDate(late), '2026-10-29')
  assert.deepEqual(validateJourney({ ...valid, departureTime: '00:01' }, late).errors, {})
  assert.equal(validateJourney({ ...valid, travelDate: '2026-10-29', departureTime: '23:58' }, late).journey, null)
})
