import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice } from '../api'
import type { Product } from '../types'

const LOW_STOCK = 5

export default function ProductPage() {
  const { id = '' } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState('')
  const [size, setSize] = useState('')

  useEffect(() => {
    document.body.dataset.productContext = id
    return () => { delete document.body.dataset.productContext; delete document.body.dataset.sizeContext }
  }, [id])

  useEffect(() => {
    if (size) document.body.dataset.sizeContext = size
    else delete document.body.dataset.sizeContext
  }, [size])

  useEffect(() => {
    setProduct(null)
    setSize('')
    fetchProduct(id)
      .then(setProduct)
      .catch(() => setError('Product not found.'))
  }, [id])

  if (error) return <p className="empty">{error} <Link to="/">Back to shop</Link></p>
  if (!product) return <p className="empty">Loading…</p>

  const qty = size ? product.stock[size] ?? 0 : 0

  return (
    <div className="product-page">
      <Link to="/" className="back">← Back to shop</Link>
      <div className="product-layout">
        <img src={product.image_url} alt={product.name} className="product-image" />
        <div className="product-info">
          <p className="muted">{product.category}</p>
          <h1>{product.name}</h1>
          <p className="price large">{formatPrice(product.price)}</p>
          <p>{product.description}</p>

          <h4>Colors</h4>
          <div className="tags">
            {product.colors.map((c) => (
              <span key={c} className="tag">{c}</span>
            ))}
          </div>

          <h4>Size</h4>
          <div className="sizes">
            {Object.entries(product.stock).map(([s, n]) => (
              <button
                key={s}
                className={`size ${size === s ? 'active' : ''}`}
                disabled={n <= 0}
                onClick={() => setSize(s)}
                title={n <= 0 ? 'Sold out' : `${n} left`}
              >
                {s}
              </button>
            ))}
          </div>
          <p className="stock-note">
            {!product.in_stock
              ? 'Sold out in all sizes.'
              : !size
                ? 'Select a size to check availability.'
                : qty <= LOW_STOCK
                  ? `Only ${qty} left in ${size}. Order soon!`
                  : `In stock in ${size}.`}
          </p>
        </div>
      </div>
    </div>
  )
}
