export default function JourneySummary({ journey }) {
  // Construct a local date, avoiding UTC conversion that can shift the calendar day.
  const [year, month, day] = journey.travelDate.split('-').map(Number)
  const [hours, minutes] = journey.departureTime.split(':').map(Number)
  const date = new Date(year, month - 1, day, hours, minutes)
  return <section className="journey-confirmation" aria-label="Saved journey details">
    <dl className="journey-details">
      <div><dt>Starting location</dt><dd>{journey.source}</dd></div>
      <div><dt>Destination</dt><dd>{journey.destination}</dd></div>
      <div><dt>Travel date</dt><dd><time dateTime={journey.travelDate}>{date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}</time></dd></div>
      <div><dt>Departure time</dt><dd><time dateTime={journey.departureTime}>{date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}</time></dd></div>
    </dl>
    <p>Journey details saved for this session. Refreshing clears your journey.</p>
  </section>
}
