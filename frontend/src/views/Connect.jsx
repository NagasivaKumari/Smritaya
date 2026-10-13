import React, { useEffect, useState } from 'react'
import { api, authToken } from '../api.js'

/** Landing page Omi opens from an app's Auth URL. Omi appends ?uid=<omi_uid>;
 *  if the visitor is signed in we link that uid to their account, then stop. */
export default function Connect() {
  const omiUid = new URLSearchParams(location.search).get('uid') || ''
  const signedIn = !!authToken()
  const [state, setState] = useState(!omiUid ? 'noid' : signedIn ? 'linking' : 'signin')
  const [err, setErr] = useState('')

  useEffect(() => {
    if (state !== 'linking') return
    api.auth
      .linkOmi(omiUid)
      .then(() => setState('done'))
      .catch((e) => { setErr(e.message); setState('error') })
  }, [state, omiUid])

  const message = {
    linking: <>Linking <b>{omiUid}</b>…</>,
    done: <>Linked. Your Omi <b>{omiUid}</b> now feeds this ledger, and nudges reach your app.</>,
    signin: <>Sign in to Smritaya first, then reopen this link to connect {omiUid || 'your Omi'}.</>,
    noid: <>This link carries no Omi id. Open it from within the Omi app.</>,
    error: <>Couldn’t link ({err}). Open Smritaya and paste your Omi id in the Vault instead.</>,
  }[state]

  return (
    <div className="stage" style={{ maxWidth: 560, margin: '14vh auto', padding: '0 1.5rem', textAlign: 'center' }}>
      <div className="eyebrow">Smritaya · connect your Omi</div>
      <h1 className="h-display" style={{ fontSize: 'clamp(1.8rem,4vw,2.6rem)', margin: '0.6rem 0' }}>
        {state === 'done' ? 'The witness' : 'Your Omi'}
      </h1>
      <p className="article" style={{ margin: '1rem 0 1.6rem' }}>{message}</p>
      <a className="copy-btn" href="/">Open Smritaya</a>
    </div>
  )
}
