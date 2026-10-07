import type { Product, ProductFilters } from './types'

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { credentials: 'include' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!res.ok) { const detail = await res.json().catch(() => ({})); throw new Error(detail.detail || 'Something went wrong.') }
  return res.json() as Promise<T>
}

export function login(email: string, password: string) { return postJson('/api/auth/login', { email, password }) }
export function signup(data: { first_name: string; last_name: string; email: string; password: string }) { return postJson('/api/auth/signup', data) }

export function fetchCategories(): Promise<string[]> {
  return getJson('/api/categories')
}

export function fetchProducts(filters: ProductFilters): Promise<Product[]> {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== '' && value !== false) params.set(key, String(value))
  }
  return getJson(`/api/products?${params}`)
}

export function fetchProduct(id: string): Promise<Product> {
  return getJson(`/api/products/${encodeURIComponent(id)}`)
}

export const formatPrice = (price: number) => `$${price.toFixed(2)}`
