import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type LayoutProps = {
  children: ReactNode;
  aside?: ReactNode;
};

export function Layout({ children, aside }: LayoutProps) {
  return (
    <main className="screen shell-screen">
      <div className="shell-grid">
        <section className="panel">{children}</section>
        <aside className="panel accent-panel">
          {aside ?? (
            <>
              <p className="eyebrow">MVP focus</p>
              <h2>Schedule work first.</h2>
              <p className="muted">
                This foundation branch keeps the frontend intentionally small:
                auth, routing, session persistence, and a dashboard shell over
                the existing backend.
              </p>
              <div className="callout-list">
                <div className="callout-card">
                  <strong>Already working backend</strong>
                  <span>Auth, teams, planning, scheduling, sessions</span>
                </div>
                <div className="callout-card">
                  <strong>Next frontend branches</strong>
                  <span>Timetable, team workspace, scheduling panel</span>
                </div>
              </div>
              <Link className="text-link" to="/">
                Back to landing page
              </Link>
            </>
          )}
        </aside>
      </div>
    </main>
  );
}
