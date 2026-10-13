import React, { useMemo } from 'react'
import InkLine from '../components/InkLine.jsx'
import DeedCard from '../components/DeedCard.jsx'
import { fmtMoney } from '../api.js'

export default function Stand({
  deeds,
  copy,
  deedCopy,
  onOpenChamber,
  onOpenPalette,
  onOpenIngest,
  onGoLedger,
}) {
  const values = useMemo(() => {
    const pending = deeds.filter((d) => d.status === 'pending')
    const overdue = pending.filter((d) => d.overdue)
    const stake = pending.filter((d) => d.direction === 'owed_to_me').reduce((s, d) => s + (d.amount || 0), 0)
    const names = new Set(deeds.map((d) => d.counterparty))
    return { pending: pending.length, overdue: overdue.length, stake, chambers: names.size }
  }, [deeds])

  const latest = deeds[0]
  const doorAction = {
    palette: onOpenPalette,
    ledger: onGoLedger,
    witness: onOpenIngest,
  }

  return (
    <div className="stage stand">
      <div className="eyebrow">{copy.eyebrow}</div>
      <h1 className="h-display">
        {copy.title}<br /><em>{copy.title_em}</em>
      </h1>
      <p className="lede">{copy.lede}</p>

      <InkLine />

      <div className="stat-row" style={{ justifyContent: 'center' }}>
        {copy.stats.map((s) => (
          <div className={`stat ${s.tone || ''}`} key={s.key}>
            <div className="n">{s.format === 'money' ? fmtMoney(values[s.key]) ?? '—' : values[s.key]}</div>
            <div className="l">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="doors">
        {copy.doors.map((d) => (
          <button className="door" key={d.name} onClick={doorAction[d.action] || (() => {})}>
            <div className="d-num">{d.num}</div>
            <div className="d-name">{d.name}</div>
          </button>
        ))}
      </div>

      {latest && (
        <div className="latest-slip">
          <div className="eyebrow" style={{ marginTop: '2.5rem' }}>{copy.latest}</div>
          <DeedCard deed={latest} copy={deedCopy} onOpenChamber={onOpenChamber} compact />
        </div>
      )}
    </div>
  )
}
