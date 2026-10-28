import RouteMap from './RouteMap.jsx'
import { useEffect, useRef, useState } from 'react'

function localDate() {
  const today = new Date()
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
}

export default function JourneyForm({ journey, onSaveJourney }) {
  const [values, setValues] = useState(journey ?? {
    source: '', destination: '', travelDate: '', departureTime: '',
  })
  const [errors, setErrors] = useState({})
  const [editing, setEditing] = useState(false)
  const confirmationRef = useRef(null)
  const sourceRef = useRef(null)

  useEffect(() => {
    if (journey && !editing) confirmationRef.current?.focus()
    if (editing) sourceRef.current?.focus()
  }, [journey, editing])

  function handleChange(event) {
    const { name, value } = event.target
    setValues(current => ({ ...current, [name]: value }))
  }

  function handleSubmit(event) {
    event.preventDefault()
    const source = values.source.trim()
    const destination = values.destination.trim()
    const nextErrors = {}

    if (!source) nextErrors.source = 'Enter a starting location, not just spaces.'
    if (!destination) nextErrors.destination = 'Enter a destination, not just spaces.'
    if (source && destination && source.toLowerCase() === destination.toLowerCase()) {
      nextErrors.destination = 'Destination must be different from the starting location.'
    }
    if (!values.travelDate) nextErrors.travelDate = 'Choose a travel date.'
    else if (values.travelDate < localDate()) nextErrors.travelDate = 'Travel date cannot be in the past.'
    if (!values.departureTime) nextErrors.departureTime = 'Choose a departure time.'

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) {
      event.currentTarget.elements.namedItem(Object.keys(nextErrors)[0])?.focus()
      return
    }

    onSaveJourney({ source, destination, travelDate: values.travelDate, departureTime: values.departureTime })
    setEditing(false)
  }

  if (journey && !editing) {
    return (
      <>
      <section className="journey-confirmation" aria-labelledby="confirmation-title">
        <h3 id="confirmation-title" tabIndex="-1" ref={confirmationRef}>Journey details saved for this session</h3>
        <dl className="journey-details">
          <div><dt>Source</dt><dd>{journey.source}</dd></div>
          <div><dt>Destination</dt><dd>{journey.destination}</dd></div>
          <div><dt>Travel date</dt><dd>{journey.travelDate}</dd></div>
          <div><dt>Departure time</dt><dd>{journey.departureTime}</dd></div>
        </dl>
        <p><strong>Status:</strong> Journey details saved for this session</p>
        <p>Route predictions will become available in a later stage. No travel times or route recommendations are generated. Refreshing this page clears the saved journey.</p>
        <button type="button" className="button secondary" onClick={() => setEditing(true)}>Edit journey details</button>
      </section>
      <RouteMap key={JSON.stringify(journey)} journey={journey} />
      </>
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-describedby="preview-description" className="journey-form">
      <div className="field">
        <label htmlFor="start">Starting location (required)</label>
        <input ref={sourceRef} id="start" name="source" type="text" required value={values.source} onChange={handleChange} placeholder="Enter starting location" autoComplete="off" aria-invalid={Boolean(errors.source)} aria-describedby={errors.source ? 'source-error' : undefined} />
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
      <div className="form-bottom"><span>Details stay in this session only. No predictions connected.</span><button className="button primary" type="submit">Save journey details <span aria-hidden="true">→</span></button></div>
    </form>
  )
}
