import React, { useEffect, useRef, useState } from 'react'
import { api, fmtMoney } from '../api.js'

const QUICK_SCENARIOS = [
  {
    label: 'Ramesh (Wardrobe)',
    text: 'Bhai wardrobe Sunday tak complete ho jayega pakka, total eight thousand rupees lagega.',
  },
  {
    label: 'Sharmaji (Leakage)',
    text: 'Advance mil gaya hai, Wednesday tak ceiling leakage repair electrician theek kar dega, tension mat lo.',
  },
  {
    label: 'Vikas (Loan)',
    text: 'Emergency ke liye 25,000 transfer kar de bhai, next month salary aate hi pakka clear kar dunga.',
  },
  {
    label: 'Ananya (Design Fee)',
    text: 'Deliver the brand guidelines on Monday and we will release the remaining forty thousand immediately.',
  },
]

export default function IngestModal({ open, onClose, onRefresh, onToast }) {
  const [transcript, setTranscript] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [busy, setBusy] = useState(false)
  const [justWitnessed, setJustWitnessed] = useState([])
  const [statusMsg, setStatusMsg] = useState('')

  const recognitionRef = useRef(null)

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return
    const recognizer = new SpeechRecognition()
    recognizer.continuous = true
    recognizer.interimResults = true
    recognizer.lang = 'en-IN'
    recognizer.onresult = (event) => {
      let currentText = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        currentText += event.results[i][0].transcript
      }
      setTranscript((prev) => {
        const base = prev.trim()
        return base ? `${base} ${currentText.trim()}` : currentText.trim()
      })
    }
    recognizer.onerror = () => setIsRecording(false)
    recognizer.onend = () => setIsRecording(false)
    recognitionRef.current = recognizer
  }, [])

  useEffect(() => {
    if (!open) {
      recognitionRef.current?.stop?.()
      setIsRecording(false)
      setStatusMsg('')
      setJustWitnessed([])
    }
  }, [open])

  const toggleRecording = () => {
    if (!recognitionRef.current) {
      onToast?.('Speech recognition not supported in this browser. Type or paste spoken text instead.')
      return
    }
    if (isRecording) {
      recognitionRef.current.stop()
      setIsRecording(false)
    } else {
      try {
        recognitionRef.current.start()
        setIsRecording(true)
        setStatusMsg('Listening to ambient speech… speak now')
      } catch {
        setIsRecording(false)
      }
    }
  }

  const handleSubmit = async () => {
    const text = transcript.trim()
    if (!text || busy) return
    setBusy(true)
    setStatusMsg('Lyzr Extractor analyzing spoken commitments & committing to Qdrant…')
    try {
      if (isRecording) {
        recognitionRef.current?.stop()
        setIsRecording(false)
      }
      const res = await api.ingest(text)
      if (res.deeds && res.deeds.length > 0) {
        setJustWitnessed(res.deeds)
        setTranscript('')
        setStatusMsg(`Witnessed ${res.deeds.length} agreement(s) sworn into the Qdrant record.`)
        onToast?.(`Sworn into record: ${res.deeds.length} agreement(s)`)
        onRefresh?.()
      } else {
        setStatusMsg('The witness detected no explicit promise or agreement in the transcript.')
      }
    } catch (err) {
      setStatusMsg(`Witness error: ${err.message}`)
      onToast?.(`Failed to ingest: ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  if (!open) return null

  return (
    <div className="veil" onClick={onClose}>
      <div
        className="witness-card"
        style={{ maxWidth: '780px', width: '100%', margin: '0 1rem', maxHeight: '90vh', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="witness-header">
          <span className="caps" style={{ color: 'var(--brand-blue)' }}>
            ⚡ Ambient Witness · Voice & Spoken Agreements
          </span>
          <span style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button onClick={toggleRecording} className={`mic-btn ${isRecording ? 'active' : ''}`}>
              <span
                className="mic-dot"
                style={{ animation: isRecording ? 'lamp-breathe 1s infinite' : 'none' }}
              />
              {isRecording ? 'Listening… Stop' : 'Record Speech (Mic)'}
            </button>
            <button className="mic-btn" onClick={onClose}>Close</button>
          </span>
        </div>

        <textarea
          className="witness-input"
          autoFocus
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
              e.preventDefault()
              handleSubmit()
            }
          }}
          placeholder="Speak into microphone or paste spoken promise… (Ctrl+Enter to witness)"
          rows={3}
        />

        <div className="scenarios-row">
          <span style={{ fontFamily: 'var(--mono)', fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            TEST PRESETS:
          </span>
          {QUICK_SCENARIOS.map((qs) => (
            <button key={qs.label} onClick={() => setTranscript(qs.text)} className="scenario-chip">
              {qs.label}
            </button>
          ))}
        </div>

        <div style={{ marginTop: '1.2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.82rem', color: busy ? 'var(--brand-blue)' : 'var(--text-muted)' }}>
            {statusMsg || 'Words spoken here are parsed into deeds by Lyzr and indexed in Qdrant.'}
          </span>
          <button
            onClick={handleSubmit}
            disabled={busy || !transcript.trim()}
            className="top-btn primary"
            style={{
              padding: '0.55rem 1.2rem',
              opacity: busy || !transcript.trim() ? 0.5 : 1,
              cursor: busy || !transcript.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {busy ? 'Extracting with Lyzr…' : 'Witness Word →'}
          </button>
        </div>

        {justWitnessed.length > 0 && (
          <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-light)', paddingTop: '1.2rem' }}>
            <div className="caps" style={{ color: 'var(--brand-emerald)', marginBottom: '0.6rem' }}>
              ✓ Recently Extracted & Sworn Deed(s)
            </div>
            {justWitnessed.map((d) => (
              <div
                key={d.id}
                style={{
                  background: '#f8fafc',
                  border: '1px solid var(--border-light)',
                  borderLeft: '3px solid var(--brand-emerald)',
                  borderRadius: '6px',
                  padding: '0.85rem 1rem',
                  marginBottom: '0.6rem',
                }}
              >
                <div style={{ fontSize: '0.98rem', fontWeight: 500, color: 'var(--text-main)' }}>
                  “{d.text}”
                </div>
                <div
                  style={{
                    marginTop: '0.4rem',
                    fontFamily: 'var(--mono)',
                    fontSize: '0.74rem',
                    color: 'var(--text-secondary)',
                  }}
                >
                  Counterparty: <b>{d.counterparty}</b> · Amount: <b>{fmtMoney(d.amount)}</b> · Status:{' '}
                  <span className="status-pill pending"><span className="status-dot" />{d.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
