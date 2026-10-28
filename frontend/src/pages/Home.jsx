import JourneyForm from '../components/JourneyForm.jsx'

const features = [
  ['01', 'Future Traffic Prediction', 'Explore how traffic may change for a selected travel date and departure time.'],
  ['02', 'Smart Route Optimization', 'Compare possible routes using predicted traffic conditions to support better journey decisions.'],
  ['03', 'Best Departure Time', 'Identify promising departure windows based on future traffic estimates.'],
]
const steps = [
  ['Enter journey details', 'Choose your starting location, destination, travel date, and departure time.'],
  ['Predict future traffic conditions', 'The planned AI model will estimate traffic for your selected journey.'],
  ['Compare possible routes', 'The planned route engine will evaluate alternative paths.'],
  ['View recommended journey', 'The planned results will help you choose a route and departure time.'],
]

export default function Home({ journey, onSaveJourney }) {
  return (
    <>
      <main id="main-content">
        <section id="home" className="hero section">
          <div className="container hero-content">
            <span className="eyebrow">A smarter way forward · Academic project</span>
            <h1>Plan Smarter<br />Journeys <span>with AI</span></h1>
            <p className="hero-description">Look ahead, before you head out. We’re building a journey planner that will use future traffic prediction to help you explore better routes and departure times.</p>
            <div className="hero-actions">
              <a className="button primary" href="#plan-journey">Plan Your Journey <span aria-hidden="true">↗</span></a>
              <a className="button secondary" href="#how-it-works">How It Works <span aria-hidden="true">↓</span></a>
            </div>
            <p className="hero-note"><span className="status-dot" /> Stage 5 · Journey overview demonstration</p>
          </div>
        </section>

        <section id="plan-journey" className="section planner-section">
          <div className="container planner-card">
            <div className="section-heading">
              <div><span className="eyebrow">Your next journey</span><h2>Where would you like to go?</h2></div>
              <span className="badge">Session only</span>
            </div>
            <p id="preview-description">Save your journey details for this session. All fields are required. Route planning and AI predictions are planned for a later stage.</p>
            <JourneyForm journey={journey} onSaveJourney={onSaveJourney} />
          </div>
        </section>

        <section className="section container" aria-labelledby="features-title">
          <div className="centered-heading"><span className="eyebrow">Built with a purpose</span><h2 id="features-title">Better journeys start with better insights.</h2><p>Three capabilities we plan to bring together. These features are not implemented yet.</p></div>
          <div className="feature-grid">{features.map(([number, title, description]) => (
            <article className="feature-card" key={title}><span className="card-number">{number}</span><span className="planned-label">Planned capability</span><h3>{title}</h3><p>{description}</p></article>
          ))}</div>
        </section>

        <section id="how-it-works" className="section workflow-section">
          <div className="container"><div className="centered-heading"><span className="eyebrow">The intended workflow</span><h2>From details to direction.</h2><p>You can enter journey details today. Prediction, comparison, and recommendations will follow in later stages.</p></div>
            <ol className="steps">{steps.map(([title, description], index) => (
              <li key={title}><span className="step-number" aria-hidden="true">{index + 1}</span><span className="planned-label">{index === 0 ? 'Journey form available' : 'Planned'}</span><h3>{title}</h3><p>{description}</p></li>
            ))}</ol>
          </div>
        </section>

        <section id="about" className="section container about-section">
          <div><span className="eyebrow">About the project</span><h2>Learning today.<br />Planning for tomorrow.</h2></div>
          <div><p>Predictive Journey Planner Using AI for Future Traffic and Route Optimization is a final-year Information Technology academic project exploring how predictive models can support informed travel decisions.</p><p>This stage presents the homepage and session-only journey form using React and Vite. Future work will explore FastAPI, XGBoost, NetworkX, and OpenStreetMap. An OpenStreetMap basemap supports a schematic Pune route demonstration. No AI model or routing engine is connected yet.</p></div>
        </section>
      </main>
      <footer className="site-footer"><div className="container footer-content"><strong>Predictive Journey Planner</strong><span>A final-year IT academic project · Built for learning and exploration.</span></div></footer>
    </>
  )
}
