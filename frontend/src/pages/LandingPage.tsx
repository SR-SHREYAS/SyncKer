import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <main className="screen landing-screen">
      <section className="hero-panel">
        <p className="eyebrow">SyncKer MVP</p>
        <h1>Coordinate work, not just calendars.</h1>
        <p className="hero-copy">
          SyncKer is a team timetable and collaboration scheduler. People manage
          their own work blocks, then the scheduler finds the best collaboration
          slot across the group with minimal disruption.
        </p>
        <div className="hero-actions">
          <Link className="primary-button" to="/register">
            Create account
          </Link>
          <Link className="secondary-button" to="/login">
            Log in
          </Link>
        </div>
      </section>

      <section className="hero-grid">
        <article className="info-card">
          <span>01</span>
          <h2>Personal timetable</h2>
          <p>Each participant manages tasks and planned time blocks.</p>
        </article>
        <article className="info-card">
          <span>02</span>
          <h2>Shared team view</h2>
          <p>The team gets one readable board across participants.</p>
        </article>
        <article className="info-card">
          <span>03</span>
          <h2>AI-assisted collaboration</h2>
          <p>The scheduler proposes a workable meeting slot, then applies it.</p>
        </article>
      </section>
    </main>
  );
}
