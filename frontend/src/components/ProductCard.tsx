import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link to={`/products/${product.product_id}`} className="card">
      <div className="card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {!product.in_stock && <span className="badge">Sold out</span>}
      </div>
      <div className="card-body">
        <h3>{product.name}</h3>
        <p className="muted">{product.category}</p>
        <p className="price">{formatPrice(product.price)}</p>
        <p className="card-description">{product.description}</p>
      </div>
    </Link>
  )
}
