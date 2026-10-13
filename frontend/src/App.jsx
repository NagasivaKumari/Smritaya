import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api, tpl, MEMORY_LABEL, AGENT_LABEL, setAuthToken } from './api.js'
import Landing from './views/Landing.jsx'
import Auth from './views/Auth.jsx'
import Stand from './views/Stand.jsx'
import IngestModal from './components/IngestModal.jsx'
import Ledger, { Chambers } from './views/Ledger.jsx'
import Chamber from './views/Chamber.jsx'
import Hearing from './views/Hearing.jsx'
import Vault from './views/Vault.jsx'

const NAV_ACTIVE = {
  ledger: ['ledger', 'chamber', 'hearing'],
  stand: ['stand'],
  chambers: ['chambers'],
  vault: ['vault'],
}

const VIEW_TITLES = {
  ledger: 'All Verbal Deeds',
  stand: 'Witness Stand',
  chambers: 'Chambers & Counterparties',
  chamber: 'Person Chamber',
  hearing: 'Dispute Hearing',
  vault: 'Vault & Platform Engine',
}

const displayName = (email) =>
  (email ? email.split('@')[0].replace(/[._-]+/g, ' ') : '').replace(/\b\w/g, (c) => c.toUpperCase()) || 'Counsel'
const displayInitials = (email) => (email ? email.split('@')[0].slice(0, 2).toUpperCase() : 'S')

function Palette({ open, onClose, onToast, copy }) {
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [verdict, setVerdict] = useState(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (open) {
      setQuestion('')
      setVerdict(null)
      setTimeout(() => inputRef.current?.focus(), 30)
    }
  }, [open])

  const ask = async (q) => {
    const text = (q ?? question).trim()
    if (!text || busy) return
    setBusy(true)
    try {
      const res = await api.ask(text)
      setVerdict(res)
    } catch (e) {
      onToast(`${copy.palette.silent}: ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  if (!open) return null
  return (
    <div className="veil" onClick={onClose}>
      <div className="palette" onClick={(e) => e.stopPropagation()}>
        <input
          ref={inputRef}
          className="palette-input"
          placeholder={copy.palette.placeholder}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') ask(); if (e.key === 'Escape') onClose() }}
        />
        <div className="palette-body">
          {!verdict && (
            <>
              <div className="palette-hint">{copy.palette.hint}</div>
              <div className="palette-sugg">
                {copy.palette.suggestions.map((s) => (
                  <button key={s} onClick={() => ask(s)}>{s}</button>
                ))}
              </div>
              {busy && <p className="loading-serif" style={{ marginTop: '1.2rem' }}>{copy.palette.loading}</p>}
            </>
          )}
          {verdict && (
            <>
              <p className="testimony">{verdict.answer}</p>
              <div className="testimony-src">
                <div className="palette-hint" style={{ marginBottom: '0.5rem' }}>
                  {copy.palette.cited} · {verdict.agent}
                </div>
                {(verdict.context || []).slice(0, 4).map((c) => (
                  <button key={c.id} className="src-chip" onClick={() => onClose()}>
                    “{c.text.length > 70 ? `${c.text.slice(0, 70)}…` : c.text}” — {c.counterparty}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [view, setView] = useState({ name: 'landing' })
  const [deeds, setDeeds] = useState([])
  const [mode, setMode] = useState(null)
  const [copy, setCopy] = useState(null)
  const [content, setContent] = useState(null)
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [ingestOpen, setIngestOpen] = useState(false)
  const [signInOpen, setSignInOpen] = useState(false)
  const [user, setUser] = useState(null)
  const [toast, setToast] = useState(null)

  const toastTimer = useRef(null)
  const showToast = useCallback((msg) => {
    setToast(msg)
    clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3200)
  }, [])

  // restore a still-valid session on load
  useEffect(() => {
    api.auth.me().then((u) => { if (u) setUser(u) }).catch(() => {})
  }, [])

  const handleAuthed = useCallback((authed) => {
    setUser(authed)
    setSignInOpen(false)
    setView({ name: 'ledger' })
    showToast('Welcome to Smritaya Workspace')
  }, [showToast])

  const handleSignOut = useCallback(async () => {
    try { await api.auth.logout() } catch { /* token may already be dead */ }
    setAuthToken('')
    setUser(null)
    setView({ name: 'landing' })
    showToast('You have left the stand.')
  }, [showToast])

  const refresh = useCallback(async () => {
    try {
      const [d, h] = await Promise.all([api.deeds(), api.health()])
      setDeeds(d.deeds)
      setMode(d.mode || h.mode)
    } catch {
      setMode(null)
    }
  }, [])

  useEffect(() => {
    if (!user) { setDeeds([]); setMode(null); return }  // never fetch another account's record pre-login
    refresh()
  }, [user, refresh])
  useEffect(() => {
    api.copy().then(setCopy).catch(() => setCopy(null))
    api.content().then(setContent).catch(() => setContent(null))
  }, [])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === '/' && !paletteOpen && !(e.target instanceof HTMLInputElement) && !(e.target instanceof HTMLTextAreaElement)) {
        e.preventDefault()
        setPaletteOpen(true)
      }
      if (e.key === 'Escape') {
        setPaletteOpen(false)
        setIngestOpen(false)
        setSignInOpen(false)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [paletteOpen])

  const go = (name) => setView({ name })
  const openChamber = (name) => setView({ name: 'chamber', person: name })

  const onRemind = async (id) => {
    const res = await api.remind(id)
    showToast(copy.toasts.reminder)
    refresh()
    return res
  }
  const onHear = (id) => setView({ name: 'hearing', deedId: id })
  const onKept = async (id) => {
    await api.setStatus(id, 'kept')
    showToast(copy.toasts.kept)
    refresh()
  }

  const inApp = view.name !== 'landing'

  const NAV_ICONS = {
    ledger: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
    stand: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
        <path d="M19 10v2a7 7 0 01-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
      </svg>
    ),
    chambers: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    vault: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="5" y="11" width="14" height="10" rx="2" />
        <path d="M8 11V7a4 4 0 018 0v4" />
        <circle cx="12" cy="16" r="1" fill="currentColor" />
      </svg>
    ),
  }

  return (
    <>
      {/* Landing page layout (Before Login) */}
      {!inApp && (
        <>
          <header className="court-bar">
            <button className="wordmark-wrap" onClick={() => go('landing')} aria-label="Smritaya home">
              <div className="wordmark-badge">S</div>
              <div>
                <div className="wordmark">Smritaya</div>
                <div className="wordmark-sub">the witness for the verbal economy</div>
              </div>
            </button>
            {content && (
              <nav className="land-nav">
                {content.nav.map((n) => (
                  <a key={n.href} href={n.href}>{n.label}</a>
                ))}
                <button className="land-nav-signin" onClick={() => setSignInOpen(true)}>
                  {user ? 'Workspace' : 'Sign in'}
                </button>
                <button className="land-nav-cta" onClick={() => (user ? go('ledger') : setSignInOpen(true))}>
                  {user ? 'Open App' : 'Launch App'}
                  <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M3.293 12.293 11.586 4H6V2h8v8h-2V4.414L3.707 13.707l-1.414-1.414z"/></svg>
                </button>
              </nav>
            )}
          </header>
          <main>
            <Landing data={content} onEnter={() => (user ? go('ledger') : setSignInOpen(true))} />
          </main>
        </>
      )}

      {/* App shell: Left Sidebar + Workspace Content */}
      {inApp && (
        <div className="app-shell">
          {/* Left Sidebar */}
          <aside className="app-sidebar">
            {/* Workspace Switcher */}
            <div className="sidebar-workspace" onClick={() => go('ledger')} role="button" tabIndex={0}>
              <div className="workspace-icon">S</div>
              <div className="workspace-info">
                <span className="workspace-title">Smritaya Workspace</span>
                <span className="workspace-badge">Verbal Witness CRM</span>
              </div>
              <svg className="workspace-caret" width="12" height="12" viewBox="0 0 20 20" fill="currentColor">
                <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
              </svg>
            </div>

            {/* Quick Omnibar Search Trigger */}
            <button className="sidebar-search-btn" onClick={() => setPaletteOpen(true)}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
                </svg>
                Ask witness…
              </span>
              <kbd>/</kbd>
            </button>

            {/* Nav */}
            <div className="sidebar-group-title">Core Records</div>
            <nav className="sidebar-nav">
              <button
                className={`sidebar-nav-item ${(NAV_ACTIVE.ledger || []).includes(view.name) ? 'active' : ''}`}
                onClick={() => go('ledger')}
              >
                <span className="sidebar-nav-icon">{NAV_ICONS.ledger}</span>
                <span className="sidebar-nav-label">All Deeds</span>
                <span className="sidebar-nav-count">{deeds.length}</span>
              </button>

              <button
                className={`sidebar-nav-item ${(NAV_ACTIVE.stand || []).includes(view.name) ? 'active' : ''}`}
                onClick={() => go('stand')}
              >
                <span className="sidebar-nav-icon">{NAV_ICONS.stand}</span>
                <span className="sidebar-nav-label">Witness Stand</span>
              </button>

              <button
                className={`sidebar-nav-item ${(NAV_ACTIVE.chambers || []).includes(view.name) ? 'active' : ''}`}
                onClick={() => go('chambers')}
              >
                <span className="sidebar-nav-icon">{NAV_ICONS.chambers}</span>
                <span className="sidebar-nav-label">Chambers</span>
              </button>

              <div className="sidebar-group-title" style={{ marginTop: '0.65rem' }}>Platform</div>
              <button
                className={`sidebar-nav-item ${(NAV_ACTIVE.vault || []).includes(view.name) ? 'active' : ''}`}
                onClick={() => go('vault')}
              >
                <span className="sidebar-nav-icon">{NAV_ICONS.vault}</span>
                <span className="sidebar-nav-label">Vault & Engine</span>
              </button>
            </nav>

            {/* Footer */}
            <div className="sidebar-footer">
              {mode && (
                <div className="sidebar-lamps">
                  <div className="lamp-row">
                    <span className="lamp-dot" style={{ background: 'var(--brand-emerald)', animationDuration: '2s' }} />
                    <span className="lamp-text">Qdrant · {MEMORY_LABEL[mode.qdrant] || mode.qdrant || 'live'}</span>
                  </div>
                  <div className="lamp-row">
                    <span className="lamp-dot" style={{ background: 'var(--brand-blue)', animationDuration: '2.5s' }} />
                    <span className="lamp-text">Lyzr · {AGENT_LABEL[mode.lyzr] || mode.lyzr || 'ready'}</span>
                  </div>
                  <div className="lamp-row">
                    <span className="lamp-dot" style={{ background: mode.omi === 'omi/live' ? 'var(--brand-emerald)' : 'var(--smoke-2, #888)', animationDuration: '3s' }} />
                    <span className="lamp-text">Omi · {mode.omi === 'omi/live' ? 'notify live' : 'off'}</span>
                  </div>
                </div>
              )}
              <div className="sidebar-user">
                <div className="user-avatar">{displayInitials(user?.email)}</div>
                <div className="user-details">
                  <span className="user-name">{displayName(user?.email)}</span>
                  <span className="user-role">Legal Counsel</span>
                </div>
                <button className="signout-btn" title="Sign out of the witness" onClick={handleSignOut}>Exit</button>
              </div>
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="app-content">
            <header className="workspace-top-bar">
              <div className="breadcrumb">
                <span className="breadcrumb-root">Workspace</span>
                <span className="breadcrumb-sep">/</span>
                <span className="breadcrumb-current">{VIEW_TITLES[view.name] || 'Witness'}</span>
              </div>
              <div className="top-bar-actions">
                <button className="top-btn" onClick={() => setPaletteOpen(true)}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
                  </svg>
                  <span>Ask Witness</span>
                  <kbd style={{ fontSize: '0.62rem', background: 'var(--bg-subtle)', padding: '1px 4px', borderRadius: '3px', fontFamily: 'var(--mono)', border: '1px solid var(--border-light)' }}>/</kbd>
                </button>
                <button className="top-btn primary" onClick={() => setIngestOpen(true)}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 5v14M5 12h14"/></svg>
                  Ingest Promise
                </button>
              </div>
            </header>

            {!copy && <div className="stage"><p className="loading-serif">Convening the witness…</p></div>}
            {copy && (
              <>
                {view.name === 'stand' && (
                  <Stand
                    deeds={deeds}
                    copy={copy.stand}
                    onOpenChamber={openChamber}
                    onOpenPalette={() => setPaletteOpen(true)}
                    onOpenIngest={() => setIngestOpen(true)}
                    onGoLedger={() => go('ledger')}
                    onRemind={onRemind}
                    onHear={onHear}
                    onKept={onKept}
                    deedCopy={copy.deed}
                    onRefresh={refresh}
                    onToast={showToast}
                  />
                )}
                {view.name === 'ledger' && (
                  <Ledger deeds={deeds} copy={copy.ledger} deedCopy={copy.deed} onOpenChamber={openChamber} onRemind={onRemind} onHear={onHear} onKept={onKept} />
                )}
                {view.name === 'chambers' && <Chambers deeds={deeds} copy={copy.chambers} labels={copy.labels} onOpenChamber={openChamber} />}
                {view.name === 'chamber' && (
                  <Chamber name={view.person} copy={copy.chamber} deedCopy={copy.deed} labels={copy.labels} onBack={() => go('ledger')} onRemind={onRemind} onHear={onHear} onKept={onKept} />
                )}
                {view.name === 'hearing' && <Hearing deedId={view.deedId} copy={copy.hearing} labels={copy.labels} onBack={() => go('ledger')} />}
                {view.name === 'vault' && (
                  <Vault deeds={deeds} mode={mode} user={user} copy={copy.vault} toasts={copy.toasts} onToast={showToast} onChanged={refresh} />
                )}
              </>
            )}
          </main>
        </div>
      )}

      {/* Modals & Dialogs */}
      {signInOpen && copy?.auth && (
        <Auth copy={copy.auth} onAuthed={handleAuthed} onClose={() => setSignInOpen(false)} onToast={showToast} />
      )}
      {copy && <Palette open={paletteOpen} onClose={() => setPaletteOpen(false)} onToast={showToast} copy={copy} />}
      <IngestModal open={ingestOpen} onClose={() => setIngestOpen(false)} onRefresh={refresh} onToast={showToast} />
      {toast && <div className="toast">{toast}</div>}
    </>
  )
}
