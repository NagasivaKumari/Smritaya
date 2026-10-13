import React, { useState } from 'react'
import { api, setAuthToken } from '../api.js'

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const MIN_PW = 8

function backendError(e, fallback) {
  const m = String(e?.message || '')
  const i = m.indexOf('{')
  if (i !== -1) {
    try { return JSON.parse(m.slice(i)).error || fallback } catch { /* fall through */ }
  }
  return fallback
}

// lucide-style eye paths
const EyeOpen = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
)
const EyeClosed = ({ size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-10-8-10-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 10 8 10 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
    <line x1="1" y1="1" x2="23" y2="23" />
  </svg>
)

function PasswordField({ copy, label, value, onChange, placeholder, error, autoFocus }) {
  const [show, setShow] = useState(false)
  return (
    <label className="auth-field">
      <span className="auth-label">{label}</span>
      <div className="auth-input-wrap">
        <input
          type={show ? 'text' : 'password'}
          className="auth-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          autoFocus={autoFocus}
        />
        <button
          type="button"
          className="auth-eye"
          onClick={() => setShow((v) => !v)}
          aria-label={show ? copy.hide : copy.show}
        >
          {show ? <EyeClosed /> : <EyeOpen />}
        </button>
      </div>
      {error && <span className="auth-error">{error}</span>}
    </label>
  )
}

function Strength({ copy, pw }) {
  const l = pw.length
  if (l === 0) return null
  const n = l < MIN_PW ? 0 : l < 10 ? 1 : l < 14 ? 2 : 3
  const tone = ['auth-weak', 'auth-ok', 'auth-strong'][Math.max(0, n - 1)]
  return (
    <div className={`auth-strength ${tone}`}>
      {Array.from({ length: 3 }, (_, i) => <i key={i} className={i < n ? 'on' : ''} />)}
      <span>{copy.strength[n]}</span>
    </div>
  )
}

export default function Auth({ copy, onAuthed, onClose, onToast }) {
  const [mode, setMode] = useState('signin') // signin | signup | reset
  const [step, setStep] = useState(0)        // reset: 0 email → 1 link → 2 new password
  const [email, setEmail] = useState('')
  const [pw, setPw] = useState('')
  const [pw2, setPw2] = useState('')
  const [resetToken, setResetToken] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const [fieldErr, setFieldErr] = useState({})

  const enter = async (fn) => {
    setBusy(true)
    setErr(null)
    try {
      const res = await fn()
      setAuthToken(res.token)
      onAuthed(res.user)
    } catch (e) {
      setErr(backendError(e, 'Something went wrong — try again.'))
    } finally {
      setBusy(false)
    }
  }

  const validateFields = () => {
    const fe = {}
    if (!EMAIL_RE.test(email.trim().toLowerCase())) fe.email = 'Enter a valid email address.'
    if (pw.length && pw.length < MIN_PW) fe.pw = `At least ${MIN_PW} characters.`
    if (pw2 && pw !== pw2) fe.pw2 = 'Passwords do not match.'
    setFieldErr(fe)
    return Object.keys(fe).length === 0
  }

  const onSignin = (e) => {
    e.preventDefault()
    if (!validateFields()) return
    enter(() => api.auth.login(email.trim().toLowerCase(), pw))
  }

  const onSignup = (e) => {
    e.preventDefault()
    if (!validateFields() || pw2 !== pw) {
      if (pw2 !== pw) setFieldErr((f) => ({ ...f, pw2: 'Passwords do not match.' }))
      return
    }
    enter(() => api.auth.signup(email.trim().toLowerCase(), pw))
  }

  const onRequestReset = async (e) => {
    e.preventDefault()
    if (!EMAIL_RE.test(email.trim().toLowerCase())) {
      setFieldErr({ email: 'Enter a valid email address.' })
      return
    }
    setBusy(true)
    setErr(null)
    try {
      const res = await api.auth.forgot(email.trim().toLowerCase())
      if (res.reset_token) {
        setResetToken(res.reset_token)
        setStep(1)
      } else {
        setErr(copy.reset_no_account)
      }
    } catch (ex) {
      setErr(backendError(ex, 'Something went wrong — try again.'))
    } finally {
      setBusy(false)
    }
  }

  const onCompleteReset = async (e) => {
    e.preventDefault()
    const fe = {}
    if (pw.length < MIN_PW) fe.pw = `At least ${MIN_PW} characters.`
    if (pw !== pw2) fe.pw2 = 'Passwords do not match.'
    setFieldErr(fe)
    if (Object.keys(fe).length) return
    setBusy(true)
    setErr(null)
    try {
      await api.auth.reset(resetToken, pw)
      onToast(copy.reset_done)
      setMode('signin')
      setStep(0)
      setPw('')
      setPw2('')
      setResetToken(null)
    } catch (ex) {
      setErr(backendError(ex, 'Something went wrong — try again.'))
    } finally {
      setBusy(false)
    }
  }

  const titles = { signin: copy.signin_title, signup: copy.signup_title, reset: copy.reset_title }
  const resetting = mode === 'reset'

  return (
    <div className="veil auth-veil" onClick={onClose}>
      <div className="auth-card" onClick={(e) => e.stopPropagation()}>
        <div className="auth-mark">
          <div className="wordmark-badge">S</div>
          <div className="wordmark" style={{ fontSize: '1.3rem' }}>Smritaya</div>
          <div className="wordmark-sub" style={{ fontSize: '0.75rem' }}>the witness for the verbal economy</div>
        </div>

        <h1 className="auth-title">{titles[mode]}</h1>

        {!resetting && (
          <form onSubmit={mode === 'signin' ? onSignin : onSignup} noValidate>
            <label className="auth-field">
              <span className="auth-label">{copy.email}</span>
              <div className="auth-input-wrap">
                <input
                  className="auth-input"
                  type="email"
                  value={email}
                  autoFocus
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={copy.email_ph}
                />
              </div>
              {fieldErr.email && <span className="auth-error">{fieldErr.email}</span>}
            </label>

            <PasswordField
              copy={copy}
              label={copy.password}
              value={pw}
              onChange={setPw}
              placeholder={copy.password_ph}
              error={fieldErr.pw}
            />
            {mode === 'signin' && (
              <div className="auth-row">
                <button type="button" className="auth-link" onClick={() => { setMode('reset'); setStep(0); setErr(null) }}>
                  {copy.forgot}
                </button>
              </div>
            )}
            {mode === 'signup' && (
              <>
                <PasswordField
                  copy={copy}
                  label={copy.confirm}
                  value={pw2}
                  onChange={setPw2}
                  placeholder={copy.password_ph}
                  error={fieldErr.pw2}
                  autoFocus
                />
                <Strength copy={copy} pw={pw} />
              </>
            )}

            {err && <p className="auth-error auth-banner">{err}</p>}
            <button className="land-btn solid auth-submit" type="submit" disabled={busy}>
              {busy ? '…' : mode === 'signin' ? copy.signin_btn : copy.signup_btn}
            </button>
          </form>
        )}

        {resetting && step === 0 && (
          <form onSubmit={onRequestReset} noValidate>
            <label className="auth-field">
              <span className="auth-label">{copy.email}</span>
              <div className="auth-input-wrap">
                <input
                  className="auth-input"
                  type="email"
                  value={email}
                  autoFocus
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={copy.email_ph}
                />
              </div>
              {fieldErr.email && <span className="auth-error">{fieldErr.email}</span>}
            </label>
            {err && <p className="auth-error auth-banner">{err}</p>}
            <button className="land-btn solid auth-submit" type="submit" disabled={busy}>
              {busy ? '…' : copy.send_btn}
            </button>
          </form>
        )}

        {resetting && step === 1 && (
          <div className="auth-reset-link">
            <p className="auth-reset-sent">{copy.reset_sent} →</p>
            <p className="auth-reset-hint">{copy.reset_hint}</p>
            <button className="auth-link auth-reset-open" onClick={() => setStep(2)}>
              {copy.reset_link_label}
            </button>
            <p className="auth-reset-token">{resetToken}</p>
          </div>
        )}

        {resetting && step === 2 && (
          <form onSubmit={onCompleteReset} noValidate>
            <PasswordField
              copy={copy}
              label={copy.password}
              value={pw}
              onChange={setPw}
              placeholder={copy.password_ph}
              error={fieldErr.pw}
              autoFocus
            />
            <PasswordField
              copy={copy}
              label={copy.confirm}
              value={pw2}
              onChange={setPw2}
              placeholder={copy.password_ph}
              error={fieldErr.pw2}
            />
            <Strength copy={copy} pw={pw} />
            {err && <p className="auth-error auth-banner">{err}</p>}
            <button className="land-btn solid auth-submit" type="submit" disabled={busy}>
              {busy ? '…' : copy.set_btn}
            </button>
          </form>
        )}

        <div className="auth-switch">
          {mode !== 'reset' ? (
            <button type="button" className="auth-link" onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}>
              {mode === 'signin' ? copy.to_signup : copy.to_signin}
            </button>
          ) : (
            <button type="button" className="auth-link" onClick={() => { setMode('signin'); setStep(0) }}>
              {copy.to_signin}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}