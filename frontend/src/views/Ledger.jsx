import React, { useMemo, useState } from 'react'
import DeedCard from '../components/DeedCard.jsx'
import WaxSeal from '../components/WaxSeal.jsx'
import { fmtDate, fmtMoney } from '../api.js'

function avatarColor(name) {
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  const colors = [
    'linear-gradient(135deg, #6366f1, #4f46e5)',
    'linear-gradient(135deg, #10b981, #059669)',
    'linear-gradient(135deg, #f59e0b, #d97706)',
    'linear-gradient(135deg, #ec4899, #db2777)',
    'linear-gradient(135deg, #8b5cf6, #7c3aed)',
    'linear-gradient(135deg, #06b6d4, #0891b2)',
  ]
  return colors[Math.abs(hash) % colors.length]
}

export default function Ledger({ deeds, copy, deedCopy, onOpenChamber, onRemind, onHear, onKept }) {
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [viewMode, setViewMode] = useState('table') // 'table' | 'cards'

  const filteredByStatus = useMemo(() => {
    if (filter === 'all') return deeds
    if (filter === 'overdue') return deeds.filter((d) => d.overdue && d.status === 'pending')
    return deeds.filter((d) => d.status === filter)
  }, [deeds, filter])

  const shown = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return filteredByStatus
    return filteredByStatus.filter(
      (d) =>
        d.counterparty.toLowerCase().includes(q) ||
        d.text.toLowerCase().includes(q) ||
        (d.topic && d.topic.toLowerCase().includes(q))
    )
  }, [filteredByStatus, search])

  const counts = useMemo(() => {
    const c = { all: deeds.length, overdue: 0, pending: 0, broken: 0, contested: 0, kept: 0 }
    for (const d of deeds) {
      if (d.overdue && d.status === 'pending') c.overdue++
      c[d.status] = (c[d.status] || 0) + 1
    }
    return c
  }, [deeds])

  return (
    <div className="stage" style={{ maxWidth: viewMode === 'table' ? '1120px' : '860px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div className="eyebrow">{copy.eyebrow}</div>
          <h1 className="h-display" style={{ fontSize: 'clamp(2.2rem,4.5vw,3.2rem)' }}>
            {copy.title}<em>{copy.title_em}</em>
          </h1>
        </div>

        {/* View Mode & Search Controls */}
        <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center', marginTop: '1.5rem' }}>
          <div
            style={{
              display: 'flex',
              background: 'var(--ink-2)',
              border: '1px solid var(--hairline-strong)',
              borderRadius: '4px',
              padding: '2px',
            }}
          >
            <button
              onClick={() => setViewMode('table')}
              style={{
                fontFamily: 'var(--mono)',
                fontSize: '0.58rem',
                letterSpacing: '0.15em',
                padding: '0.4rem 0.8rem',
                borderRadius: '3px',
                background: viewMode === 'table' ? 'var(--ink-3)' : 'transparent',
                color: viewMode === 'table' ? 'var(--gold)' : 'var(--smoke)',
                border: viewMode === 'table' ? '1px solid var(--hairline)' : 'none',
              }}
            >
              田 Table
            </button>
            <button
              onClick={() => setViewMode('cards')}
              style={{
                fontFamily: 'var(--mono)',
                fontSize: '0.58rem',
                letterSpacing: '0.15em',
                padding: '0.4rem 0.8rem',
                borderRadius: '3px',
                background: viewMode === 'cards' ? 'var(--ink-3)' : 'transparent',
                color: viewMode === 'cards' ? 'var(--gold)' : 'var(--smoke)',
                border: viewMode === 'cards' ? '1px solid var(--hairline)' : 'none',
              }}
            >
              ░ Slips
            </button>
          </div>
        </div>
      </div>

      {/* Filter Row + Search Input */}
      <div className="table-toolbar">
        <div className="filter-row">
          {copy.filters.map((f) => (
            <button
              key={f.id}
              className={`filter-chip ${filter === f.id ? 'active' : ''}`}
              onClick={() => setFilter(f.id)}
            >
              {f.label} <span className="count">{counts[f.id] || 0}</span>
            </button>
          ))}
        </div>

        <div className="search-input-wrap">
          <svg className="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search records or people…"
          />
        </div>
      </div>

      {shown.length === 0 && <p className="lede" style={{ marginTop: '2rem' }}>{copy.empty}</p>}

      {/* Data Table View */}
      {viewMode === 'table' && shown.length > 0 && (
        <div className="witness-table-container">
          <table className="witness-table">
            <thead>
              <tr>
                <th>Party</th>
                <th>Spoken Quote</th>
                <th>Stakes</th>
                <th>Due Date</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((d) => (
                <tr key={d.id} className="table-row-hover">
                  {/* Party with Avatar */}
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button
                      onClick={() => onOpenChamber(d.counterparty)}
                      className="table-party-cell"
                    >
                      <div
                        className="party-avatar"
                        style={{ background: avatarColor(d.counterparty) }}
                      >
                        {d.counterparty.charAt(0).toUpperCase()}
                      </div>
                      <span>{d.counterparty}</span>
                    </button>
                  </td>

                  {/* Verbatim Spoken Quote */}
                  <td className="quote-cell">
                    <div>“{d.text}”</div>
                    {d.topic && <div className="quote-topic">#{d.topic}</div>}
                  </td>

                  {/* Stakes */}
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {d.amount != null ? (
                      <span style={{ fontFamily: 'var(--mono)', fontWeight: 600, color: 'var(--text-main)', fontSize: '0.88rem' }}>
                        {fmtMoney(d.amount, d.currency)}
                      </span>
                    ) : (
                      <span style={{ color: 'var(--text-faint)', fontSize: '0.8rem' }}>—</span>
                    )}
                  </td>

                  {/* Due Date */}
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <span style={{ fontFamily: 'var(--mono)', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {fmtDate(d.due_ts)}
                    </span>
                  </td>

                  {/* Status Pill */}
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {d.overdue && d.status === 'pending' ? (
                      <span className="status-pill overdue">
                        <span className="status-dot" style={{ animation: 'lamp-breathe 1.5s infinite' }} />
                        Overdue
                      </span>
                    ) : (
                      <span className={`status-pill ${d.status}`}>
                        <span className="status-dot" />
                        {d.status}
                      </span>
                    )}
                  </td>

                  {/* Actions */}
                  <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <div className="table-actions">
                      {onRemind && d.status === 'pending' && (
                        <button className="t-btn" onClick={() => onRemind(d.id)}>
                          Remind
                        </button>
                      )}
                      {onHear && d.status !== 'kept' && (
                        <button className="t-btn danger" onClick={() => onHear(d.id)}>
                          Hearing
                        </button>
                      )}
                      {onKept && d.status === 'pending' && (
                        <button className="t-btn success" onClick={() => onKept(d.id)}>
                          Kept
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Cards Slips View Mode */}
      {viewMode === 'cards' && shown.map((d) => (
        <DeedCard key={d.id} deed={d} copy={deedCopy} onOpenChamber={onOpenChamber} onRemind={onRemind} onHear={onHear} onKept={onKept} />
      ))}
    </div>
  )
}

export function Chambers({ deeds, copy, labels, onOpenChamber }) {
  const people = useMemo(() => {
    const map = new Map()
    for (const d of deeds) {
      const p = map.get(d.counterparty) || { name: d.counterparty, kept: 0, broken: 0, pending: 0, contested: 0, stake: 0 }
      p[d.status] = (p[d.status] || 0) + 1
      if (d.status === 'pending' && d.direction === 'owed_to_me') p.stake += d.amount || 0
      map.set(d.counterparty, p)
    }
    return [...map.values()].sort((a, b) => b.broken - a.broken || b.stake - a.stake)
  }, [deeds])

  const sealOf = (p) => {
    const decided = p.kept + p.broken
    if (!decided) return p.pending || p.contested ? 'pending' : 'untested'
    const ratio = p.kept / decided
    return ratio >= 0.75 ? 'intact' : ratio >= 0.4 ? 'cracked' : 'broken'
  }

  return (
    <div className="stage">
      <div className="eyebrow">{copy.eyebrow}</div>
      <h1 className="h-display" style={{ fontSize: 'clamp(2.2rem,4.5vw,3.2rem)' }}>
        {copy.title}<em>{copy.title_em}</em>
      </h1>
      <p className="lede">{copy.lede}</p>

      <div className="doors" style={{ justifyContent: 'flex-start', gap: '2.6rem', marginTop: '3rem' }}>
        {people.map((p) => (
          <button key={p.name} className="door" onClick={() => onOpenChamber(p.name)}>
            <WaxSeal name={p.name} state={sealOf(p)} size={86} />
            <div className="d-name" style={{ marginTop: '0.7rem' }}>{p.name}</div>
            <div className="d-num" style={{ marginTop: '0.4rem' }}>
              {p.kept} {labels.kept} · {p.broken} {labels.broken}{p.pending ? ` · ${p.pending} ${labels.pending}` : ''}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
