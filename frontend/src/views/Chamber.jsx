import React, { useEffect, useState } from 'react'
import WaxSeal from '../components/WaxSeal.jsx'
import DeedCard from '../components/DeedCard.jsx'
import { api, fmtMoney, tpl } from '../api.js'

export default function Chamber({ name, copy, deedCopy, labels, onBack, onRemind, onHear, onKept }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let live = true
    setData(null)
    api.chamber(name).then((d) => live && setData(d)).catch((e) => live && setError(e.message))
    return () => { live = false }
  }, [name])

  if (error) return <div className="stage"><p className="lede">{tpl(copy.sealed, { error })}</p></div>
  if (!data) return <div className="stage"><p className="loading-serif">{copy.opening}</p></div>

  const t = data.trust
  const tag = copy.tags[t.seal] || copy.tags.untested

  return (
    <div className="stage">
      <button className="src-chip" style={{ marginBottom: '1.4rem' }} onClick={onBack}>{copy.back}</button>
      <div className="chamber-head">
        <WaxSeal name={data.counterparty} state={t.seal} size={170} />
        <div>
          <h1 className="chamber-name">{data.counterparty}</h1>
          <div className="chamber-tag">{tag}</div>
          <div className="stat-row">
            <div className="stat kept"><div className="n">{t.kept}</div><div className="l">{labels.kept}</div></div>
            <div className="stat broken"><div className="n">{t.broken}</div><div className="l">{labels.broken}</div></div>
            <div className="stat"><div className="n">{t.pending}</div><div className="l">{labels.pending}</div></div>
            {t.at_stake > 0 && (
              <div className="stat gold"><div className="n">{fmtMoney(t.at_stake)}</div><div className="l">{labels.at_stake}</div></div>
            )}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '3rem' }}>
        <div className="eyebrow">{copy.eyebrow}</div>
        {data.deeds.map((d) => (
          <DeedCard key={d.id} deed={d} copy={deedCopy} onOpenChamber={() => {}} onRemind={onRemind} onHear={onHear} onKept={onKept} />
        ))}
        {data.deeds.length === 0 && <p className="lede">{copy.empty}</p>}
      </div>
    </div>
  )
}
