import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCategories, fetchProducts } from '../api'
import ProductCard from '../components/ProductCard'
import type { Product } from '../types'

export default function Home() {
  const [categories, setCategories] = useState<string[]>([])
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories([]))
    // Feature a handful of in-stock pieces so the landing page always shows real merchandise.
    fetchProducts({ in_stock: true }).then((items) => setFeatured(items.slice(0, 4))).catch(() => setFeatured([]))
  }, [])

  return (
    <div className="home">
      <section className="home-hero">
        <p className="home-kicker">Officially licensed Yale apparel</p>
        <h1>Casual comfort, classic Bulldog pride.</h1>
        <p className="home-lede">
          Campus Customs brings Yale into everyday life — hoodies, crewnecks, and tees tied to the
          residential colleges, graduate schools, teams, and traditions that make this community home.
        </p>
        <Link to="/products" className="home-cta">Shop the collection</Link>
      </section>

      <section className="home-section">
        <h2>Shop by category</h2>
        <div className="chips">
          {categories.map((c) => (
            <Link key={c} to={`/products?category=${encodeURIComponent(c)}`} className="chip">
              {c}
            </Link>
          ))}
        </div>
      </section>

      {featured.length > 0 && (
        <section className="home-section">
          <div className="home-section-head">
            <h2>Fresh off the shelf</h2>
            <Link to="/products" className="home-link">View all →</Link>
          </div>
          <div className="grid">
            {featured.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
