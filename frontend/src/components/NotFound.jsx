import { Home, PlugZap, Zap } from "lucide-react";
import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <section className="not-found app-page">
      <div className="not-found-art" aria-hidden="true">
        <Zap className="spark" size={42} fill="currentColor" />
        <PlugZap size={118} />
      </div>
      <strong>404</strong>
      <h1>Page Not Found</h1>
      <p>The page you're looking for doesn't exist or has been moved.</p>
      <Link className="not-found-home-button" to="/">
        <Home size={17} />
        <span>Go Back Home</span>
      </Link>
    </section>
  );
}
