import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Home, LayoutDashboard, Microscope, History, Users, Menu, X, Leaf } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/farms', label: 'Farms', icon: Users },
  { to: '/analyze', label: 'Analyze', icon: Microscope },
  { to: '/history', label: 'History', icon: History },
];

export default function Layout({ children }) {
  const { user, logout, isAuthenticated } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    setMobileOpen(false);
    navigate('/login');
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand" onClick={() => setMobileOpen(false)}>
          <Leaf size={22} />
          <span>AgriForge</span>
        </Link>

        <button
          type="button"
          className="mobile-nav-toggle"
          onClick={() => setMobileOpen((open) => !open)}
          aria-label="Toggle navigation"
        >
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        <nav className={`top-nav ${mobileOpen ? 'open' : ''}`}>
          <div className="nav-links">
            <NavLink to="/" end className="nav-link" onClick={() => setMobileOpen(false)}>
              <Home size={18} />
              <span>Home</span>
            </NavLink>
            {isAuthenticated &&
              navItems.map(({ to, label, icon: Icon }) => (
                <NavLink key={to} to={to} className="nav-link" onClick={() => setMobileOpen(false)}>
                  <Icon size={18} />
                  <span>{label}</span>
                </NavLink>
              ))}
          </div>

          <div className="nav-actions">
            {isAuthenticated ? (
              <>
                <div className="user-chip">{user?.full_name || user?.email || 'Farmer'}</div>
                <button type="button" className="secondary-btn" onClick={handleLogout}>
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="secondary-btn" onClick={() => setMobileOpen(false)}>
                  Login
                </Link>
                <Link to="/register" className="primary-btn" onClick={() => setMobileOpen(false)}>
                  Register
                </Link>
              </>
            )}
          </div>
        </nav>
      </header>

      <main className="content">{children}</main>
    </div>
  );
}
