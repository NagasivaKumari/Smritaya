import React, { useState } from 'react'
import { api, uid, fmtDate, tpl, MEMORY_LABEL, AGENT_LABEL, EMBEDDER_LABEL } from '../api.js'

function value(key, mode) {
  if (!mode) return '—'
  if (key === 'memory') return MEMORY_LABEL[mode.qdrant] || 'ready'
  if (key === 'embedder') return EMBEDDER_LABEL(mode.embedder)
  if (key === 'reasoning') return AGENT_LABEL[mode.lyzr] || 'ready'
  if (key === 'points') return mode.points
  if (key === 'omi') return mode.omi === 'omi/live' ? 'live' : 'off'
  return '—'
}

/** The Vault — privacy as a legal right, registry as a public record. */
export default function Vault({ deeds, mode, user, copy, toasts, onToast, onChanged }) {
  const [confirming, setConfirming] = useState(null)
  const [omiUid, setOmiUid] = useState(user?.omi_uid || '')
  const [linking, setLinking] = useState(false)
  // the account's own uid when signed in — that is what Omi must post to
  const witnessId = user?.uid || uid()

  const saveOmi = async () => {
    setLinking(true)
    try {
      await api.auth.linkOmi(omiUid.trim())
      onToast(tpl(toasts.omi_linked, { id: omiUid.trim() || '—' }))
      onChanged?.()
    } finally {
      setLinking(false)
    }
  }

  const strike = async (deed) => {
    setConfirming(null)
    await api.forget({ deed_id: deed.id })
    onToast(tpl(toasts.struck, { text: deed.text.slice(0, 34) }))
    onChanged()
  }

  const strikeAll = async (name) => {
    await api.forget({ counterparty: name })
    onToast(tpl(toasts.chamber_emptied, { name }))
    onChanged()
  }

  const names = [...new Set(deeds.map((d) => d.counterparty))]

  return (
    <div className="stage">
      <div className="eyebrow">{copy.eyebrow}</div>
      <h1 className="h-display" style={{ fontSize: 'clamp(2.2rem,4.5vw,3.2rem)' }}>
        {copy.title}<em>{copy.title_em}</em>
      </h1>

      {copy.articles.map((segments, i) => (
        <p className="article" key={i}>
          {segments.map((s, j) => (s.t != null ? <span key={j}>{s.t}</span> : <em key={j}>{s.em}</em>))}
        </p>
      ))}

      <div className="registry-panel">
        <div className="eyebrow" style={{ fontSize: '0.58rem' }}>{copy.where}</div>
        <div className="registry-grid">
          {copy.rows.map((r) => (
            <div key={r.key}><div className="k">{r.label}</div><div className="v">{value(r.key, mode)}</div></div>
          ))}
        </div>
      </div>

      <div className="registry-panel">
        <div className="eyebrow" style={{ fontSize: '0.58rem' }}>{copy.witness_id}</div>
        <div style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', marginTop: '0.6rem', wordBreak: 'break-all' }}>{witnessId}</div>
      </div>

      <div className="registry-panel">
        <div className="eyebrow" style={{ fontSize: '0.58rem' }}>{copy.omi_connect}</div>
        <p style={{ fontSize: '0.82rem', color: 'var(--smoke-2)', marginTop: '0.7rem', lineHeight: 1.5 }}>{copy.omi_lede}</p>
        <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.8rem', flexWrap: 'wrap' }}>
          <input
            className="omi-input"
            placeholder={copy.omi_ph}
            value={omiUid}
            onChange={(e) => setOmiUid(e.target.value)}
            style={{ flex: '1 1 220px', background: 'transparent', border: '1px solid var(--smoke-2)', color: 'inherit', padding: '0.5rem 0.7rem', fontFamily: 'var(--mono)', fontSize: '0.78rem' }}
          />
          <button className="copy-btn" disabled={linking} onClick={saveOmi}>{linking ? copy.omi_saving : copy.omi_save}</button>
        </div>
        <div className="k" style={{ fontFamily: 'var(--mono)', fontSize: '0.56rem', letterSpacing: '0.24em', textTransform: 'uppercase', color: omiUid ? 'var(--gold, #c9a227)' : 'var(--smoke-2)', marginTop: '0.7rem' }}>
          {omiUid ? copy.omi_linked : copy.omi_unlinked}
        </div>
      </div>

      <div className="registry-panel">
        <div className="eyebrow" style={{ fontSize: '0.58rem' }}>{copy.strike}</div>
        <div style={{ marginTop: '0.8rem' }}>
          {deeds.map((d) => (
            <div key={d.id} className="strike-row">
              <div className="s-text">
                <b>{d.counterparty}</b> · {fmtDate(d.ts)} — “{d.text.length > 64 ? `${d.text.slice(0, 64)}…` : d.text}”
              </div>
              {confirming === d.id ? (
                <span style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="copy-btn" style={{ color: 'var(--wax)', borderColor: 'var(--wax)' }} onClick={() => strike(d)}>{copy.confirm}</button>
                  <button className="copy-btn" onClick={() => setConfirming(null)}>{copy.spare}</button>
                </span>
              ) : (
                <button className="copy-btn" onClick={() => setConfirming(d.id)}>{copy.strike_btn}</button>
              )}
            </div>
          ))}
        </div>
        {names.length > 0 && (
          <div style={{ marginTop: '1.2rem' }}>
            <div className="k" style={{ fontFamily: 'var(--mono)', fontSize: '0.56rem', letterSpacing: '0.28em', textTransform: 'uppercase', color: 'var(--smoke-2)' }}>{copy.strike_chamber}</div>
            <div className="palette-sugg" style={{ marginTop: '0.7rem' }}>
              {names.map((n) => (
                <button key={n} onClick={() => strikeAll(n)}>{tpl(copy.forget, { name: n })}</button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
