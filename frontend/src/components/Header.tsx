import { NavLink } from "react-router-dom";

const NAV_LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium transition ${
    isActive ? "bg-surface-raised text-text-primary" : "text-text-secondary hover:text-text-primary"
  }`;

export function Header() {
  return (
    <header className="border-b border-border bg-canvas/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-text-primary">
            SEC Filing Analyzer
          </h1>
          <p className="text-sm text-text-secondary">
            AI-powered analysis of SEC 10-K and 10-Q filings.
          </p>
        </div>
        <nav className="flex gap-1">
          <NavLink to="/" end className={NAV_LINK_CLASS}>
            Dashboard
          </NavLink>
          <NavLink to="/compare" className={NAV_LINK_CLASS}>
            Compare Filings
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
