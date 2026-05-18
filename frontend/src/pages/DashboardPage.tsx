import { useNavigate } from "react-router-dom";

import { useAuth } from "../app/AuthContext";
import { PersonalTimetablePanel } from "../components/PersonalTimetablePanel";

const dashboardSections = [
  {
    title: "Team Timetable",
    description:
      "This area will render the shared team board once we wire the team workspace APIs.",
  },
  {
    title: "Collaboration Panel",
    description:
      "This panel will generate and apply AI-assisted scheduling suggestions after the shell foundation is merged.",
  },
];

export function DashboardPage() {
  const navigate = useNavigate();
  const { currentUser, logout } = useAuth();

  function handleLogout(): void {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <main className="screen dashboard-screen">
      <section className="dashboard-topbar">
        <div>
          <p className="eyebrow">Workspace dashboard</p>
          <h1>{currentUser?.username ?? "Authenticated user"}</h1>
          <p className="muted">{currentUser?.email}</p>
        </div>

        <button className="secondary-button" onClick={handleLogout} type="button">
          Log out
        </button>
      </section>

      <section className="dashboard-grid">
        <div className="dashboard-primary-column">
          <PersonalTimetablePanel />
        </div>

        {dashboardSections.map((section) => (
          <article className="panel dashboard-card" key={section.title}>
            <h2>{section.title}</h2>
            <p className="muted">{section.description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
