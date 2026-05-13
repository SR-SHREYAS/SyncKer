import type { ReactNode } from "react";

type AuthStatusShellProps = {
  title: string;
  description: string;
  actions?: ReactNode;
};

export function AuthStatusShell({
  title,
  description,
  actions,
}: AuthStatusShellProps) {
  return (
    <main className="screen shell-screen">
      <section className="panel status-panel">
        <p className="eyebrow">SyncKer</p>
        <h1>{title}</h1>
        <p className="muted">{description}</p>
        {actions ? <div className="status-actions">{actions}</div> : null}
      </section>
    </main>
  );
}
