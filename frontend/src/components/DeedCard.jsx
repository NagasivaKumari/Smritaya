import React, { useState } from 'react'
import WaxSeal from './WaxSeal.jsx'
import { fmtDate, fmtMoney } from '../api.js'

const SEAL_FOR_STATUS = {
  kept: 'intact',
  broken: 'broken',
  contested: 'cracked',
  pending: 'pending',
}

function Stamp({ deed, copy }) {
  if (deed.overdue && deed.status === 'pending') return <span className="stamp overdue">{copy.overdue_stamp}</span>
  return <span className={`stamp ${deed.status}`}>{deed.status}</span>
}

/** The paper artifact — the exact spoken words, metadata as marginalia. */
export default function DeedCard({ deed, copy, onOpenChamber, onRemind, onHear, onKept, compact }) {
  const [draft, setDraft] = useState(null)
  const [busy, setBusy] = useState(false)

  const remind = async () => {
    setBusy(true)
    try {
      const res = await onRemind(deed.id)
      setDraft(res?.draft || null)
    } finally {
      setBusy(false)
    }
  }

  const hearingEligible = deed.status !== 'kept'

  return (
    <article className={`paper lift deed ${compact ? 'compact' : ''}`}>
      {!compact && (
        <aside className="marginalia">
          <span>{copy.who}<b>{deed.counterparty}</b></span>
          {deed.amount != null && <span>{copy.sum}<b>{fmtMoney(deed.amount, deed.currency)}</b></span>}
          <span>{copy.due}<b>{fmtDate(deed.due_ts)}</b></span>
          <span>{copy.sworn}<b>{fmtDate(deed.ts)}</b></span>
          {deed.overdue && deed.status === 'pending' && <span className="m-overdue">{copy.overdue}</span>}
        </aside>
      )}

      {!compact && <div className="deed-seal"><WaxSeal name={deed.counterparty} state={SEAL_FOR_STATUS[deed.status] || 'pending'} size={46} detail={false} /></div>}

      <button className="who" onClick={() => onOpenChamber(deed.counterparty)}>{deed.counterparty}</button>
      <p className="quote">{deed.text}</p>

      <div className="deed-foot">
        <span>{deed.direction === 'i_owe' ? copy.you_swore : copy.they_swore}</span>
        <span className="sep" />
        <span>{deed.source}</span>
        <span className="sep" />
        <Stamp deed={deed} copy={copy} />
      </div>

      {(onRemind || onHear || onKept) && (
        <div className="deed-actions">
          {onRemind && deed.status === 'pending' && (
            <button className="pbtn" disabled={busy} onClick={remind}>{busy ? copy.drafting : copy.send_reminder}</button>
          )}
          {onHear && hearingEligible && (
            <button className="pbtn blood" onClick={() => onHear(deed.id)}>{copy.convene}</button>
          )}
          {onKept && deed.status === 'pending' && (
            <button className="pbtn" onClick={() => onKept(deed.id)}>{copy.word_kept}</button>
          )}
        </div>
      )}

      {draft && (
        <div className="paper reminder-paper">
          <div className="memo-label"><span>{copy.reminder_label}</span></div>
          <div className="memo-body">{draft}</div>
        </div>
      )}
    </article>
  )
}
