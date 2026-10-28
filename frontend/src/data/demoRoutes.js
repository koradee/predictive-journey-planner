// Illustrative schematic corridors only: not surveyed road geometry or navigation instructions.
export const demoRoutes = [
  { id: 'PUNE-A', name: 'Northern schematic corridor', isDemo: true, coordinates: [[18.5314,73.8446],[18.532,73.850],[18.534,73.857],[18.534,73.865],[18.531,73.870],[18.5285,73.8743]] },
  { id: 'PUNE-B', name: 'Southern schematic corridor', isDemo: true, coordinates: [[18.5314,73.8446],[18.527,73.847],[18.524,73.854],[18.524,73.863],[18.526,73.870],[18.5285,73.8743]] },
]
export function routesForJourney(journey) {
  const normalize = value => value.trim().toLowerCase().replace(/,/g, ' ').replace(/\s+/g, ' ')
  const source = normalize(journey.source), destination = normalize(journey.destination)
  const start = ['shivajinagar', 'shivajinagar pune']
  const end = ['pune railway station']
  if (start.includes(source) && end.includes(destination)) return demoRoutes
  if (end.includes(source) && start.includes(destination)) return demoRoutes.map(route => ({ ...route, coordinates: [...route.coordinates].reverse() }))
  return []
}
