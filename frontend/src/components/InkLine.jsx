import React from 'react'

export default function InkLine() {
  return (
    <div style={{ margin: '1.5rem auto 2rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3px', height: '28px' }} aria-hidden="true">
      {[8, 14, 22, 16, 10, 20, 26, 14, 18, 24, 12, 16, 22, 18, 10, 24, 14, 8].map((h, i) => (
        <span
          key={i}
          style={{
            width: '3px',
            height: `${h}px`,
            background: 'linear-gradient(180deg, var(--brand-blue), #93c5fd)',
            borderRadius: '9999px',
            opacity: 0.6,
            animation: `lamp-breathe ${1.2 + (i % 4) * 0.25}s infinite ease-in-out`,
          }}
        />
      ))}
    </div>
  )
}
