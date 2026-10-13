import React, { useEffect, useRef, useState } from 'react'
import WaxSeal from '../components/WaxSeal.jsx'
import { api, fmtDate, fmtMoney, tpl } from '../api.js'

function CopyBtn({ text, copy }) {
  const [done, setDone] = useState(false)
  return (
    <button
      className="copy-btn"
      onClick={() => {
        navigator.clipboard?.writeText(text).then(() => {
          setDone(true)
          setTimeout(() => setDone(false), 1600)
        })
      }}
    >
      {done ? copy.copied : copy.copy}
    </button>
  )
}

function Act({ num, title, children, ready, word }) {
  const ref = useRef(null)
  useEffect(() => {
    if (ready && ref.current) ref.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [ready])
  if (!ready) return null
  return (
    <section className="act" ref={ref}>
      <div className="act-head">
        <span className="act-num">{word} {num}</span>
        <span className="act-title">{title}</span>
      </div>
      {children}
    </section>
  )
}

/** The Hearing — the witness convenes: Summons → Evidence → Pattern → The Memo. */
export default function Hearing({ deedId, copy, labels, onBack }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [stage, setStage] = useState(1)

  useEffect(() => {
    api.hearing(deedId).then(setData).catch((e) => setError(e.message))
  }, [deedId])

  useEffect(() => {
    if (!data) return
    const timers = [
      setTimeout(() => setStage(2), 1400),
      setTimeout(() => setStage(3), 2800),
      setTimeout(() => setStage(4), 4200),
    ]
    return () => timers.forEach(clearTimeout)
  }, [data])

  if (error) return <div className="stage"><p className="lede">{tpl(copy.error, { error })}</p></div>
  if (!data) return <div className="stage"><p className="loading-serif">{copy.loading}</p></div>

  const { acts } = data
  const d = acts.evidence[0]
  const [a1, a2, a3, a4] = copy.acts

  return (
    <div className="stage" style={{ maxWidth: 780 }}>
      <button className="src-chip" onClick={onBack}>{copy.back}</button>

      <div className="eyebrow" style={{ marginTop: '2rem' }}>{copy.eyebrow}</div>
      <h1 className="h-display" style={{ fontSize: 'clamp(2rem,4vw,2.9rem)' }}>
        <em>{d.counterparty}</em> {copy.title}
      </h1>

      <Act num={a1.num} title={a1.title} word={copy.act_word} ready={stage >= 1}>
        <p className="summons-text">{acts.summons.narrative}</p>
      </Act>

      <Act num={a2.num} title={a2.title} word={copy.act_word} ready={stage >= 2}>
        {acts.evidence.map((e) => (
          <div key={e.id} className="paper memo-paper" style={{ marginBottom: '1rem' }}>
            <div className="memo-label">
              <span>{copy.exhibit} · {e.counterparty} · {fmtDate(e.ts)}</span>
              <span>{e.source}</span>
            </div>
            <div className="memo-body" style={{ fontStyle: 'italic' }}>“{e.text}”</div>
            <div className="cite">
              {e.status}{e.amount != null ? ` · ${fmtMoney(e.amount, e.currency)}` : ''}{e.due_ts ? ` · ${copy.due} ${fmtDate(e.due_ts)}` : ''}
            </div>
          </div>
        ))}
      </Act>

      <Act num={a3.num} title={a3.title} word={copy.act_word} ready={stage >= 3}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.8rem' }}>
          <WaxSeal name={d.counterparty} state={acts.pattern.trust.seal} size={110} />
          <div>
            <p className="summons-text" style={{ fontSize: 'clamp(1.1rem,2.2vw,1.4rem)' }}>
              {acts.pattern.narrative || copy.pattern_fallback}
            </p>
            <div className="stat-row" style={{ marginTop: '1rem' }}>
              <div className="stat kept"><div className="n">{acts.pattern.trust.kept}</div><div className="l">{labels.kept}</div></div>
              <div className="stat broken"><div className="n">{acts.pattern.trust.broken}</div><div className="l">{labels.broken}</div></div>
              {acts.pattern.trust.at_stake > 0 && (
                <div className="stat gold"><div className="n">{fmtMoney(acts.pattern.trust.at_stake)}</div><div className="l">{labels.at_stake}</div></div>
              )}
            </div>
          </div>
        </div>
      </Act>

      <Act num={a4.num} title={a4.title} word={copy.act_word} ready={stage >= 4}>
        <div className="paper memo-paper">
          <div className="memo-label"><span>{copy.memo_labels.gentle}</span><CopyBtn text={acts.memo.gentle} copy={copy} /></div>
          <div className="memo-body">{acts.memo.gentle}</div>
        </div>
        <div className="paper memo-paper">
          <div className="memo-label"><span>{copy.memo_labels.firm}</span><CopyBtn text={acts.memo.firm} copy={copy} /></div>
          <div className="memo-body">{acts.memo.firm}</div>
        </div>
        <div className="paper memo-paper formal">
          <div className="memo-label"><span>{copy.memo_labels.formal}</span><CopyBtn text={acts.memo.formal} copy={copy} /></div>
          <div className="memo-body">{acts.memo.formal}</div>
        </div>
        <p className="advice">{acts.memo.advice}</p>
      </Act>
    </div>
  )
}
