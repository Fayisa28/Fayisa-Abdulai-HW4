import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchCategories, fetchProducts } from '../api'
import ProductCard from '../components/ProductCard'
import type { Product } from '../types'

const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
const PRICES = [40, 60, 80, 100]

export default function Shop() {
  // Filters live in the URL so results are shareable and survive the back button.
  const [params, setParams] = useSearchParams()
  const [categories, setCategories] = useState<string[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState(params.get('q') ?? '')

  const category = params.get('category') ?? ''
  const size = params.get('size') ?? ''
  const maxPrice = params.get('max_price') ?? ''
  const inStock = params.get('in_stock') === 'true'
  const q = params.get('q') ?? ''

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next)
  }

  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  // Debounce typing so we don't query on every keystroke.
  useEffect(() => {
    const id = setTimeout(() => {
      if (search !== q) setParam('q', search.trim())
    }, 300)
    return () => clearTimeout(id)
  }, [search])

  useEffect(() => {
    setLoading(true)
    setError('')
    fetchProducts({
      q,
      category,
      size,
      max_price: maxPrice ? Number(maxPrice) : undefined,
      in_stock: inStock,
    })
      .then(setProducts)
      .catch(() => setError('Could not load products. Is the backend running?'))
      .finally(() => setLoading(false))
  }, [q, category, size, maxPrice, inStock])

  return (
    <div className="shop">
      <section className="hero">
        <h1>Carry Yale With You</h1>
        <p>Find thoughtfully selected Yale apparel and gifts made for students, alumni, families, and friends of the university.</p>
        <input
          className="search"
          type="search"
          placeholder="Search products, colleges, sports…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </section>

      <div className="chips">
        <button className={!category ? 'chip active' : 'chip'} onClick={() => setParam('category', '')}>
          All
        </button>
        {categories.map((c) => (
          <button key={c} className={category === c ? 'chip active' : 'chip'} onClick={() => setParam('category', c)}>
            {c}
          </button>
        ))}
      </div>

      <div className="filters">
        <label>
          Size
          <select value={size} onChange={(e) => setParam('size', e.target.value)}>
            <option value="">Any</option>
            {SIZES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label>
          Max price
          <select value={maxPrice} onChange={(e) => setParam('max_price', e.target.value)}>
            <option value="">Any</option>
            {PRICES.map((p) => (
              <option key={p} value={p}>
                Under ${p}
              </option>
            ))}
          </select>
        </label>
        <label className="checkbox">
          <input type="checkbox" checked={inStock} onChange={(e) => setParam('in_stock', e.target.checked ? 'true' : '')} />
          In stock only
        </label>
        <span className="muted count">{loading ? 'Loading…' : `${products.length} products`}</span>
      </div>

      {error && <p className="error">{error}</p>}
      {!loading && !error && products.length === 0 && <p className="empty">No products match those filters.</p>}
      <div className="grid">
        {products.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
    </div>
  )
}
