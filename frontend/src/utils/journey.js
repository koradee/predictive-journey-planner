export function localDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

export function validateJourney(values, now = new Date()) {
  const source = values.source.trim().replace(/\s+/g, ' ')
  const destination = values.destination.trim().replace(/\s+/g, ' ')
  const errors = {}

  if (!source) errors.source = 'Enter a starting location, not just spaces.'
  if (!destination) errors.destination = 'Enter a destination, not just spaces.'
  if (source && destination && source.toLowerCase() === destination.toLowerCase()) {
    errors.destination = 'Destination must be different from the starting location.'
  }
  if (!values.travelDate) errors.travelDate = 'Choose a travel date.'
  else if (values.travelDate < localDate(now)) errors.travelDate = 'Travel date cannot be in the past.'
  if (!values.departureTime) errors.departureTime = 'Choose a departure time.'
  if (values.travelDate && values.departureTime) {
    const [year, month, day] = values.travelDate.split('-').map(Number)
    const [hours, minutes] = values.departureTime.split(':').map(Number)
    // Numeric constructor uses the user's local timezone, not UTC.
    const departure = new Date(year, month - 1, day, hours, minutes)
    if (!Number.isFinite(departure.getTime()) || departure.getFullYear() !== year ||
        departure.getMonth() !== month - 1 || departure.getDate() !== day ||
        departure.getHours() !== hours || departure.getMinutes() !== minutes) {
      errors.departureTime = 'Choose a valid local travel date and departure time.'
    } else if (departure.getTime() <= now.getTime()) {
      errors.departureTime = 'Choose a departure date and time in the future.'
    }
  }

  return {
    errors,
    journey: Object.keys(errors).length ? null : {
      source, destination, travelDate: values.travelDate, departureTime: values.departureTime,
    },
  }
}
