import { Link, NavLink, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import Shop from './pages/Shop'
import ProductPage from './pages/ProductPage'
import ChatBubble from './components/ChatBubble'
import AuthPage from './pages/AuthPage'

export default function App() {
  return (
    <>
      <header className="site-header">
        <Link to="/" className="logo">
          Campus <span>Customs</span>
        </Link>
        <nav className="site-nav" aria-label="Main navigation">
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/products">Products</NavLink>
          <NavLink to="/about">About Us</NavLink>
          <NavLink to="/login">Log In</NavLink>
          <NavLink to="/create-account" className="nav-cta">Create Account</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Shop />} />
          <Route path="/products/:id" element={<ProductPage />} />
          <Route path="/about" element={<section className="info-page"><h1>Made for the Yale Community</h1><p>Campus Customs brings the spirit of Yale into everyday life with classic university apparel, meaningful gifts, and pieces that celebrate the people, places, and traditions that make this community special.</p><p>Browse our collection and find something to carry your Yale connection wherever you go.</p></section>} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/create-account" element={<AuthPage mode="signup" />} />
          <Route path="*" element={<p className="empty">Page not found.</p>} />
        </Routes>
      </main>
      <ChatBubble />
      <footer className="site-footer">Campus Customs · Official Yale apparel</footer>
    </>
  )
}
