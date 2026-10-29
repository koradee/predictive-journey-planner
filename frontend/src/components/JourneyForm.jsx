import { useState } from 'react'

import { localDate, validateJourney } from '../utils/journey.js'

export default function JourneyForm({ journey, onSaveJourney }) {
  const [values, setValues] = useState(journey ?? {
    source: '', destination: '', travelDate: '', departureTime: '',
  })
  const [errors, setErrors] = useState({})

  function handleChange(event) {
    const { name, value } = event.target
    setValues(current => ({ ...current, [name]: value }))
  }

  function handleSubmit(event) {
    event.preventDefault()
    const { errors: nextErrors, journey: validatedJourney } = validateJourney(values)

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) {
      event.currentTarget.elements.namedItem(Object.keys(nextErrors)[0])?.focus()
      return
    }

    onSaveJourney(validatedJourney)
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-describedby="preview-description" className="journey-form">
      <div className="field">
        <label htmlFor="start">Starting location (required)</label>
        <input id="start" name="source" type="text" required value={values.source} onChange={handleChange} placeholder="Enter starting location" autoComplete="off" aria-invalid={Boolean(errors.source)} aria-describedby={errors.source ? 'source-error' : undefined} />
        {errors.source && <p className="field-error" id="source-error" role="alert">{errors.source}</p>}
      </div>
      <div className="field">
        <label htmlFor="destination">Destination (required)</label>
        <input id="destination" name="destination" type="text" required value={values.destination} onChange={handleChange} placeholder="Enter destination" autoComplete="off" aria-invalid={Boolean(errors.destination)} aria-describedby={errors.destination ? 'destination-error' : undefined} />
        {errors.destination && <p className="field-error" id="destination-error" role="alert">{errors.destination}</p>}
      </div>
      <div className="field">
        <label htmlFor="travel-date">Travel date (required)</label>
        <input id="travel-date" name="travelDate" type="date" required min={localDate()} value={values.travelDate} onChange={handleChange} aria-invalid={Boolean(errors.travelDate)} aria-describedby={errors.travelDate ? 'date-error' : undefined} />
        {errors.travelDate && <p className="field-error" id="date-error" role="alert">{errors.travelDate}</p>}
      </div>
      <div className="field">
        <label htmlFor="departure-time">Departure time (required)</label>
        <input id="departure-time" name="departureTime" type="time" required value={values.departureTime} onChange={handleChange} aria-invalid={Boolean(errors.departureTime)} aria-describedby={errors.departureTime ? 'time-error' : undefined} />
        {errors.departureTime && <p className="field-error" id="time-error" role="alert">{errors.departureTime}</p>}
      </div>
      <div className="form-bottom"><span>Your plans stay here until you refresh the page.</span><button className="button primary" type="submit">Find Routes <span aria-hidden="true">→</span></button></div>
    </form>
  )
}
