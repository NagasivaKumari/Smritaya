import React, { useEffect, useMemo, useState } from 'react'

/* Deterministic per-name randomness so every person's seal is unique. */
function hashName(name) {
  let h = 2166136261
  for (let i = 0; i < name.length; i++) {
    h ^= name.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function mulberry(seed) {
  let a = seed
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function blobPath(name, r = 34) {
  const rnd = mulberry(hashName(name))
  const n = 9
  const pts = []
  for (let i = 0; i < n; i++) {
    const ang = (i / n) * Math.PI * 2
    const rad = r * (0.86 + rnd() * 0.28)
    pts.push([50 + Math.cos(ang) * rad, 50 + Math.sin(ang) * rad])
  }
  let d = `M ${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`
  for (let i = 0; i < n; i++) {
    const p0 = pts[i]
    const p1 = pts[(i + 1) % n]
    const mx = (p0[0] + p1[0]) / 2
    const my = (p0[1] + p1[1]) / 2
    d += ` Q ${p0[0].toFixed(1)},${p0[1].toFixed(1)} ${mx.toFixed(1)},${my.toFixed(1)}`
  }
  return d + ' Z'
}

const SEAL_COLORS = {
  intact: { wax: '#4c7a63', deep: '#2f5341', ink: '#0f2018' },
  cracked: { wax: '#a8432f', deep: '#7c2c1d', ink: '#2b0d08' },
  broken: { wax: '#9e2b25', deep: '#6e1a15', ink: '#2b0705' },
  untested: { wax: '#8d8478', deep: '#5f584e', ink: '#22201c' },
  pending: { wax: '#a8873a', deep: '#7c6226', ink: '#241c08' },
}

/**
 * The wax seal — trust rendered as an artifact, not a progress bar.
 * state: intact | cracked | broken | untested | pending
 */
export default function WaxSeal({ name = '?', state = 'untested', size = 74, detail = true }) {
  const c = SEAL_COLORS[state] || SEAL_COLORS.untested
  const path = useMemo(() => blobPath(name || '?'), [name])
  const rnd = useMemo(() => mulberry(hashName(name || '?') + 7), [name])
  const initial = (name || '?').trim().charAt(0).toUpperCase()

  const cracks =
    state === 'cracked' || state === 'broken'
      ? Array.from({ length: state === 'broken' ? 4 : 2 }, () => {
          const a = rnd() * Math.PI * 2
          const len = 16 + rnd() * 18
          const x0 = 50 + Math.cos(a) * 8
          const y0 = 50 + Math.sin(a) * 8
          const x1 = 50 + Math.cos(a + 0.35) * len
          const y1 = 50 + Math.sin(a + 0.35) * len
          return `M ${x0.toFixed(1)},${y0.toFixed(1)} L ${((x0 + x1) / 2 + (rnd() - 0.5) * 8).toFixed(1)},${((y0 + y1) / 2 + (rnd() - 0.5) * 8).toFixed(1)} L ${x1.toFixed(1)},${y1.toFixed(1)}`
        }).join(' ')
      : null

  return (
    <svg width={size} height={size} viewBox="0 0 100 100" className="wax-seal" aria-label={`seal ${state}`}>
      <defs>
        <radialGradient id={`waxg-${hashName(name || '?')}`} cx="38%" cy="32%" r="80%">
          <stop offset="0%" stopColor={c.wax} />
          <stop offset="70%" stopColor={c.deep} />
          <stop offset="100%" stopColor={c.ink} />
        </radialGradient>
      </defs>
      {state !== 'untested' && (
        <>
          <path d={path} fill={`url(#waxg-${hashName(name || '?')})`} opacity="0.96" />
          <circle cx="50" cy="50" r="24" fill="none" stroke="rgba(255,244,214,0.4)" strokeWidth="1" />
          <text
            x="50" y="58.5" textAnchor="middle"
            fontFamily="Fraunces, Georgia, serif" fontStyle="italic"
            fontSize="26" fill="rgba(255,244,214,0.85)"
          >
            {initial}
          </text>
          {cracks && <path d={cracks} stroke="rgba(24,8,5,0.85)" strokeWidth="1.4" fill="none" strokeLinecap="round" />}
          {detail && state === 'broken' && (
            <>
              <circle cx="30" cy="76" r="5" fill={c.deep} opacity="0.9" />
              <circle cx="72" cy="24" r="4" fill={c.deep} opacity="0.9" />
            </>
          )}
        </>
      )}
      {state === 'untested' && (
        <>
          <path d={path} fill="none" stroke="rgba(141,132,120,0.55)" strokeWidth="1.3" strokeDasharray="3 4" />
          <text
            x="50" y="57" textAnchor="middle"
            fontFamily="Fraunces, Georgia, serif" fontStyle="italic"
            fontSize="22" fill="rgba(141,132,120,0.8)"
          >
            {initial}
          </text>
        </>
      )}
    </svg>
  )
}
