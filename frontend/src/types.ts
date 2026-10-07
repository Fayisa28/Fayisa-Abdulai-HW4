export type Stock = Record<string, number>

export interface Product {
  product_id: string
  name: string
  garment_type: string
  category: string
  description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  stock: Stock
  in_stock: boolean
}

export interface ProductFilters {
  q?: string
  category?: string
  color?: string
  max_price?: number
  size?: string
  in_stock?: boolean
}
