import React, { useEffect, useState } from 'react'
import InkLine from '../components/InkLine.jsx'
import WaxSeal from '../components/WaxSeal.jsx'
import { fmtMoney } from '../api.js'

function Title({ a, b }) {
  return <h2 className="h-sub">{a}<br /><em>{b}</em></h2>
}

function Cards({ cards }) {
  return (
    <div className="land-grid three">
      {cards.map((p) => (
        <div className="land-cell" key={p.big}>
          <div className="land-big">{p.big}</div>
          <div className="land-k">{p.k}</div>
          <p className="land-d">{p.d}</p>
        </div>
      ))}
    </div>
  )
}

function Loop({ steps }) {
  return (
    <div className="loop">
      {steps.map((s) => (
        <div className="loop-step" key={s.n}>
          <div className="loop-n">{s.n}</div>
          <div className="loop-t">{s.t}</div>
          <p className="land-d">{s.d}</p>
        </div>
      ))}
    </div>
  )
}

function Stack({ cards }) {
  return (
    <div className="land-grid three">
      {cards.map((s) => (
        <div className="paper land-card" key={s.name}>
          <div className="land-card-role">{s.role}</div>
          <div className="land-card-name">{s.name}</div>
          <p className="land-card-d">{s.d}</p>
        </div>
      ))}
    </div>
  )
}

function Trust({ pillars }) {
  return (
    <div className="land-grid three">
      {pillars.map((p) => (
        <div className="land-cell seal-cell" key={p.t}>
          <WaxSeal name={p.t} state={p.seal} size={64} />
          <div className="land-k">{p.t}</div>
          <p className="land-d">{p.d}</p>
        </div>
      ))}
    </div>
  )
}

const KINDS = { cards: Cards, loop: Loop, stack: Stack, trust: Trust }

function Section({ s }) {
  const Body = KINDS[s.kind]
  return (
    <section className="land-sect" id={s.id}>
      <div className="eyebrow">{s.eyebrow}</div>
      <Title a={s.title} b={s.title_em} />
      {Body && <Body cards={s.cards} steps={s.steps} pillars={s.pillars} />}
    </section>
  )
}

function Stats({ eyebrow, title, title_em, stats }) {
  return (
    <section className="land-sect land-live">
      <div className="eyebrow">{eyebrow}</div>
      <Title a={title} b={title_em} />
      <div className="stat-row">
        {stats.map((s) => (
          <div className={`stat ${s.tone || ''}`} key={s.label}>
            <div className="n">{s.format === 'money' ? fmtMoney(s.value) : s.value}</div>
            <div className="l">{s.label}</div>
          </div>
        ))}
      </div>
    </section>
  )
}

function Footer({ footer, onEnter }) {
  return (
    <footer className="land-foot">
      <div className="foot-top">
        <div className="foot-brand">
          <span className="wordmark">{footer.wordmark_pre}<em>{footer.wordmark_em}</em>{footer.wordmark_post}</span>
          <p>{footer.tagline}</p>
        </div>
        {footer.columns.map((col) => (
          <div className="foot-col" key={col.h}>
            <div className="foot-h">{col.h}</div>
            {col.links.map((l) =>
              l.action === 'enter' ? (
                <button key={l.label} onClick={onEnter}>{l.label}</button>
              ) : l.href ? (
                <a key={l.label} href={l.href}>{l.label}</a>
              ) : (
                <span key={l.label}>{l.label}</span>
              )
            )}
          </div>
        ))}
      </div>
      <div className="foot-bottom">
        <span>{footer.copyright}</span>
        <span className="caps">{footer.note}</span>
      </div>
    </footer>
  )
}

function MotionRail({ nav }) {
  const [active, setActive] = useState(null)

  useEffect(() => {
    const els = (nav || [])
      .map((n) => document.getElementById(n.href.slice(1)))
      .filter(Boolean)
    if (!els.length) return
    // band = rail height down to 45% of viewport; last hit wins, so it holds at rest
    const io = new IntersectionObserver(
      (es) => es.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: '-56px 0px -55% 0px' }
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [nav])

  if (!nav || !nav.length) return null
  return (
    <nav className="motion-rail" aria-label="Sections">
      {nav.map((n) => {
        const id = n.href.slice(1)
        return (
          <a
            key={n.href}
            href={n.href}
            className={active === id ? 'is-active' : undefined}
            aria-current={active === id ? 'true' : undefined}
          >{n.label}</a>
        )
      })}
    </nav>
  )
}

function Marquee({ words }) {
  if (!words || !words.length) return null
  return (
    <div className="marquee" aria-hidden="true">
      {/* doubled so the -50% translate loops seamlessly */}
      <div>
        {[...words, ...words].map((w, i) => <span key={i}>{w}</span>)}
      </div>
    </div>
  )
}

export default function Landing({ data, onEnter }) {
  if (!data) {
    return (
      <div className="stage stand">
        <p className="loading-serif">Convening the witness…</p>
      </div>
    )
  }

  const { hero } = data

  return (
    <div className="landing">
      <section className="land-hero">
        <div className="eyebrow">{hero.eyebrow}</div>
        <h1 className="h-display">
          {hero.title}<br /><em>{hero.title_em}</em>
        </h1>
        <p className="lede">{hero.lede}</p>
        <div className="land-cta">
          <button className="land-btn solid" onClick={onEnter}>{hero.primary_cta}</button>
          <a className="land-btn ghost" href={hero.secondary_href}>{hero.secondary_cta}</a>
        </div>

        {/* Live Workspace Mockup Card */}
        <div className="land-preview-frame">
          <div className="land-preview-header">
            <div className="land-preview-dots">
              <span className="land-preview-dot" />
              <span className="land-preview-dot" />
              <span className="land-preview-dot" />
            </div>
            <div className="land-preview-title">Smritaya Workspace · Live Verbal Deeds (Qdrant & Lyzr Engine)</div>
            <button
              onClick={onEnter}
              style={{
                fontSize: '0.74rem',
                fontWeight: 600,
                color: 'var(--brand-blue)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              Open in App →
            </button>
          </div>
          <div className="land-preview-body">
            <table className="witness-table">
              <thead>
                <tr>
                  <th>Counterparty</th>
                  <th>Spoken Promise (Verbatim)</th>
                  <th>Stakes</th>
                  <th>Due Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr className="table-row-hover">
                  <td>
                    <div className="table-party-cell">
                      <div className="party-avatar" style={{ background: '#6366f1' }}>R</div>
                      <span>Ramesh (Carpenter)</span>
                    </div>
                  </td>
                  <td className="quote-cell">
                    “Wardrobe Sunday tak complete ho jayega pakka, total eight thousand rupees lagega.”
                    <div className="quote-topic">#craft #advance</div>
                  </td>
                  <td><span style={{ fontFamily: 'var(--mono)', fontWeight: 600, color: 'var(--text-main)' }}>₹8,000</span></td>
                  <td><span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>This Sunday</span></td>
                  <td><span className="status-pill pending"><span className="status-dot" />Pending</span></td>
                </tr>
                <tr className="table-row-hover">
                  <td>
                    <div className="table-party-cell">
                      <div className="party-avatar" style={{ background: '#10b981' }}>S</div>
                      <span>Sharmaji (Contractor)</span>
                    </div>
                  </td>
                  <td className="quote-cell">
                    “Advance mil gaya hai, Wednesday tak ceiling leakage repair theek ho jayega.”
                    <div className="quote-topic">#repairs #home</div>
                  </td>
                  <td><span style={{ fontFamily: 'var(--mono)', fontWeight: 600, color: 'var(--text-main)' }}>₹5,000</span></td>
                  <td><span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Wednesday</span></td>
                  <td><span className="status-pill kept"><span className="status-dot" />Kept</span></td>
                </tr>
                <tr className="table-row-hover">
                  <td>
                    <div className="table-party-cell">
                      <div className="party-avatar" style={{ background: '#f59e0b' }}>V</div>
                      <span>Vikas (Colleague)</span>
                    </div>
                  </td>
                  <td className="quote-cell">
                    “Emergency ke liye 25,000 transfer kar de, next month salary aate hi clear kar dunga.”
                    <div className="quote-topic">#personal-loan</div>
                  </td>
                  <td><span style={{ fontFamily: 'var(--mono)', fontWeight: 600, color: 'var(--text-main)' }}>₹25,000</span></td>
                  <td><span style={{ fontSize: '0.8rem', color: '#b91c1c', fontWeight: 600 }}>10 Oct 2026</span></td>
                  <td><span className="status-pill overdue"><span className="status-dot" />Overdue</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <MotionRail nav={data.nav} />

      <Stats eyebrow={data.stats_eyebrow} title={data.stats_title} title_em={data.stats_title_em} stats={data.stats} />

      <Marquee words={data.marquee} />

      {data.sections.map((s) => <Section key={s.id} s={s} />)}

      <section className="land-final">
        <h2 className="h-display">{data.final.title}<br /><em>{data.final.title_em}</em></h2>
        <p className="lede">{data.final.lede}</p>
        <div className="land-cta">
          <button className="land-btn solid" onClick={onEnter}>{data.final.cta}</button>
        </div>
      </section>

      <Footer footer={data.footer} onEnter={onEnter} />
    </div>
  )
}
