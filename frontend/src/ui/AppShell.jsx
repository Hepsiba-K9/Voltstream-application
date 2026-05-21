import {
  BarChart3,
  Bot,
  Cpu,
  FileText,
  Home,
  ToggleLeft,
  Zap,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { FloatingAssistant } from "../components/FloatingAssistant";

const links = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/devices", label: "Devices", icon: ToggleLeft },
  { to: "/billing", label: "Billing", icon: FileText },
  { to: "/assistant", label: "VoltSenseBot", icon: Bot },
  { to: "/agent", label: "Volt Agent", icon: Cpu },
];

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">
            <Zap size={21} fill="currentColor" />
            <i />
            <i />
          </span>
          <div>
            <strong>VoltStream</strong>
            <small>Energy Monitoring</small>
          </div>
        </div>

        <nav className="top-nav" aria-label="Top navigation">
          {links.map(({ to, label }) => (
            <NavLink key={to} to={to} end={to === "/"}>
              {label}
            </NavLink>
          ))}
        </nav>

      </header>

      <aside className="sidebar">
        <nav className="nav-links" aria-label="Primary navigation">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="content">
        <Outlet />
      </main>

      <FloatingAssistant />
    </div>
  );
}
