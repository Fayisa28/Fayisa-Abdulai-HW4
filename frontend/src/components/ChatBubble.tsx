import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { formatPrice } from '../api'
import type { Product } from '../types'

export default function ChatBubble() {
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [reply, setReply] = useState('')
  const [products, setProducts] = useState<Product[]>([])
  const [busy, setBusy] = useState(false)
  const [history, setHistory] = useState<{ role: string; content: string }[]>([])
  const location = useLocation()
  const loadHistory = async () => { const res = await fetch('/api/chat/history', { credentials: 'include' }); if (res.ok) setHistory(await res.json()) }
  const send = async (event: FormEvent) => {
    event.preventDefault(); if (!message.trim() || busy) return
    setBusy(true)
    try {
      const product = document.body.dataset.productContext
      const selectedSize = document.body.dataset.sizeContext
      const pageContext = [location.pathname, product && `product_id=${product}`, selectedSize && `selected_size=${selectedSize}`].filter(Boolean).join(' | ')
      const res = await fetch('/api/chat', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: message.trim(), page_context: pageContext }) })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Chat is temporarily unavailable.')
      setReply(data.reply); setProducts(data.products || []); setHistory((items) => [...items, { role: 'user', content: message.trim() }, { role: 'assistant', content: data.reply }]); setMessage('')
    } catch (error) { setReply(error instanceof Error ? error.message : 'Chat is temporarily unavailable.'); setProducts([]) }
    finally { setBusy(false) }
  }
  return (
    <div className={`chat-widget ${open ? 'open' : ''}`}>
      {open && (
        <section className="chat-panel" aria-label="Campus Customs chat">
          <div className="chat-panel-header">
            <strong>Campus Customs</strong>
            <button onClick={() => setOpen(false)} aria-label="Close chat">×</button>
          </div>
          <div className="chat-panel-body">
            {history.slice(-4).map((item, index) => <p className="chat-history-line" key={`${item.role}-${index}`}><strong>{item.role === 'user' ? 'You' : 'Campus Customs'}:</strong> {item.content}</p>)}
            <p>{reply || 'Ask us to find Yale gear by type, style, color, or price.'}</p>
            {products.length > 0 && <div className="chat-results">{products.map((product) => <Link className="chat-product" key={product.product_id} to={`/products/${product.product_id}`} onClick={() => setOpen(false)}><img src={product.image_url} alt="" /><span><strong>{product.name}</strong><small>{formatPrice(product.price)}</small></span></Link>)}</div>}
            <form className="chat-form" onSubmit={send}><input aria-label="Ask about products" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Ask about Yale gear…" /><button disabled={busy}>{busy ? '…' : 'Send'}</button></form>
          </div>
        </section>
      )}
      <button className="chat-toggle" onClick={() => { const next = !open; setOpen(next); if (next) loadHistory() }} aria-expanded={open}>
        <span aria-hidden="true">✦</span> Chat with us
      </button>
    </div>
  )
}
