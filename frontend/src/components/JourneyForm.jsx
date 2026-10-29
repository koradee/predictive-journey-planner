import { useState } from 'react'

function localDate() {
  const today = new Date()
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
}

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
    const source = values.source.trim().replace(/\s+/g, ' ')
    const destination = values.destination.trim().replace(/\s+/g, ' ')
    const nextErrors = {}

    if (!source) nextErrors.source = 'Enter a starting location, not just spaces.'
    if (!destination) nextErrors.destination = 'Enter a destination, not just spaces.'
    if (source && destination && source.toLowerCase() === destination.toLowerCase()) {
      nextErrors.destination = 'Destination must be different from the starting location.'
    }
    if (!values.travelDate) nextErrors.travelDate = 'Choose a travel date.'
    else if (values.travelDate < localDate()) nextErrors.travelDate = 'Travel date cannot be in the past.'
    if (!values.departureTime) nextErrors.departureTime = 'Choose a departure time.'
    if (values.travelDate && values.departureTime) {
      const [year, month, day] = values.travelDate.split('-').map(Number)
      const [hours, minutes] = values.departureTime.split(':').map(Number)
      // Numeric constructor uses the user's local timezone, not UTC.
      const departure = new Date(year, month - 1, day, hours, minutes)
      if (!Number.isFinite(departure.getTime()) || departure.getFullYear() !== year ||
          departure.getMonth() !== month - 1 || departure.getDate() !== day ||
          departure.getHours() !== hours || departure.getMinutes() !== minutes) {
        nextErrors.departureTime = 'Choose a valid local travel date and departure time.'
      } else if (departure.getTime() <= Date.now()) {
        nextErrors.departureTime = 'Choose a departure date and time in the future.'
      }
    }

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) {
      event.currentTarget.elements.namedItem(Object.keys(nextErrors)[0])?.focus()
      return
    }

    onSaveJourney({ source, destination, travelDate: values.travelDate, departureTime: values.departureTime })
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
      <div className="form-bottom"><span>Your plans stay here until you refresh the page.</span><button className="button primary" type="submit">View Journey <span aria-hidden="true">→</span></button></div>
    </form>
  )
}
