import { useState } from 'react'
import type { ChangeEvent, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login, signup } from '../api'

export default function AuthPage({ mode }: { mode: 'login' | 'signup' }) {
  const isSignup = mode === 'signup'
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError('')
    if (isSignup && form.password !== form.confirm) { setError('Passwords do not match.'); return }
    setBusy(true)
    try {
      if (isSignup) await signup(form)
      else await login(form.email, form.password)
      navigate('/')
    } catch (err) { setError(err instanceof Error ? err.message : 'Please check your details and try again.') }
    finally { setBusy(false) }
  }
  const update = (key: keyof typeof form) => (event: ChangeEvent<HTMLInputElement>) => setForm({ ...form, [key]: event.target.value })
  return <section className="auth-page"><div className="auth-card">
    <p className="auth-kicker">Campus Customs</p><h1>{isSignup ? 'Create your account' : 'Welcome back'}</h1>
    <p className="muted">{isSignup ? 'Save your favorite Yale gear and shop with ease.' : 'Sign in to continue browsing your campus collection.'}</p>
    <form onSubmit={submit}>
      {isSignup && <div className="form-row"><label>First name<input required value={form.first_name} onChange={update('first_name')} /></label><label>Last name<input value={form.last_name} onChange={update('last_name')} /></label></div>}
      <label>Email<input required type="email" value={form.email} onChange={update('email')} /></label>
      <label>Password<input required minLength={isSignup ? 12 : 1} type="password" value={form.password} onChange={update('password')} /></label>
      {isSignup && <label>Confirm password<input required minLength={12} type="password" value={form.confirm} onChange={update('confirm')} /></label>}
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="auth-submit" disabled={busy}>{busy ? 'Please wait…' : isSignup ? 'Create account' : 'Log in'}</button>
    </form>
    <p className="auth-switch">{isSignup ? 'Already have an account?' : 'New to Campus Customs?'} <Link to={isSignup ? '/login' : '/create-account'}>{isSignup ? 'Log in' : 'Create account'}</Link></p>
  </div></section>
}
