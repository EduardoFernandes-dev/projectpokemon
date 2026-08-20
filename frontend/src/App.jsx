import { Link, NavLink, Route, Routes } from 'react-router-dom'
import HomePage from './pages/HomePage'
import PokemonDetailPage from './pages/PokemonDetailPage'
import TmsPage from './pages/TmsPage'
import MoveDetailPage from './pages/MoveDetailPage'

function Sidebar() {
  return (
    <aside className="sidebar">
      <nav className="sidebar-nav" aria-label="Main navigation">
        <NavLink
          to="/"
          end
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
        >
          Pokédex
        </NavLink>
        <NavLink
          to="/tms"
          className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
        >
          TMs
        </NavLink>
      </nav>
    </aside>
  )
}

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <Link to="/" className="app-title-link">
          <h1 className="app-title">
            <span className="title-icon">⚡</span>
            Pokédex
          </h1>
        </Link>
      </header>

      <div className="app-body">
        <Sidebar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/pokemon/:id" element={<PokemonDetailPage />} />
          <Route path="/tms" element={<TmsPage />} />
          <Route path="/move/:id" element={<MoveDetailPage />} />
          <Route
            path="*"
            element={
              <div className="no-results">
                Page not found.{' '}
                <Link to="/" className="back-link inline">
                  Back to Pokédex
                </Link>
              </div>
            }
          />
        </Routes>
      </div>
    </div>
  )
}
