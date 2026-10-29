import JourneyForm from '../components/JourneyForm.jsx'

const features = [
  ['01', 'Plan Ahead', 'Keep your starting point, destination, and departure details together in one clear journey overview.'],
  ['02', 'Explore Routes', 'Get a feel for route exploration with our interactive Pune demo map. Zoom, pan, and take a closer look.'],
  ['03', 'Compare Your Options', 'Switch between illustrative route alternatives and see your selection highlighted on the map.'],
]
const steps = [
  ['Tell us your plans', 'Enter your locations, travel date, and departure time.'],
  ['Open your overview', 'Review your details in one place, ready to explore.'],
  ['Explore the demo', 'Try the supported Pune journey to compare illustrative routes.'],
  ['Make it yours', 'Edit your details whenever your plans change.'],
]

export default function Home({ journey, onSaveJourney }) {
  return <main id="main-content">
    <section id="home" className="hero section">
      <div className="container hero-content">
        <div className="hero-copy">
          <span className="eyebrow">A little planning. A clearer journey.</span>
          <h1>Your Journey,<br /><span>Smarter.</span></h1>
          <p className="hero-description">Plan ahead with intelligent route insights. Explore routes, compare options, and make better travel decisions.</p>
          <div className="hero-actions">
            <a className="button primary" href="#plan-journey">Plan a Journey <span aria-hidden="true">↗</span></a>
            <a className="button secondary" href="#features">Explore Features</a>
          </div>
        </div>
        <aside className="journey-preview" aria-label="Illustrative journey preview">
          <div className="preview-heading"><strong>Your next connection</strong><span className="badge">Demo Mode</span></div>
          <div className="preview-map" aria-hidden="true">
            <svg viewBox="0 0 400 210" fill="none">
              <path className="preview-street" d="M0 40H400M0 110H400M0 180H400M65 0V210M180 0V210M310 0V210" />
              <path d="M60 155L130 155L130 65L325 65" stroke="#a3b4cf" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M60 155L225 155L225 65L325 65" stroke="#245bd6" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="60" cy="155" r="11" fill="white" stroke="#245bd6" strokeWidth="5" />
              <circle cx="325" cy="65" r="11" fill="#245bd6" stroke="white" strokeWidth="5" />
            </svg>
          </div>
          <div className="preview-stops"><div><small>FROM</small><strong>Shivajinagar, Pune</strong></div><span aria-hidden="true">→</span><div><small>TO</small><strong>Pune Railway Station</strong></div></div>
          <p>Illustrative routes. A simple way to explore your options.</p>
        </aside>
      </div>
    </section>
    <section id="plan-journey" className="section planner-section">
      <div className="container planner-card">
        <div className="section-heading"><div><span className="eyebrow">Start here</span><h2>Where would you like to go?</h2></div><span className="planner-step">01 / Your details</span></div>
        <p id="preview-description">Choose your journey details. All fields are required. Try Shivajinagar, Pune to Pune Railway Station to explore the demo routes.</p>
        <JourneyForm journey={journey} onSaveJourney={onSaveJourney} />
      </div>
    </section>
    <section id="features" className="section container" aria-labelledby="features-title">
      <div className="centered-heading"><span className="eyebrow">Less searching. More exploring.</span><h2 id="features-title">A clearer view of your next journey.</h2><p>Simple tools to bring your plans together.</p></div>
      <div className="feature-grid">{features.map(([number,title,description]) => <article className="feature-card" key={title}><span className="card-number">{number}</span><h3>{title}</h3><p>{description}</p></article>)}</div>
    </section>
    <section id="how-it-works" className="section workflow-section"><div className="container">
      <div className="centered-heading"><span className="eyebrow">How it works</span><h2>A few details. A fresh perspective.</h2><p>From your first idea to a journey overview in four simple steps.</p></div>
      <ol className="steps">{steps.map(([title,description],index) => <li key={title}><span className="step-number" aria-hidden="true">{index+1}</span><h3>{title}</h3><p>{description}</p></li>)}</ol>
    </div></section>
    <section id="about" className="section container about-section"><div><span className="eyebrow">Meet Predictive Journey Planner</span><h2>Smarter Planning for Every Journey</h2></div><p>Predictive Journey Planner brings journey details, route exploration, and travel planning into one simple experience. Our goal is to help travelers explore their options and plan with greater confidence.</p></section>
  </main>
}
