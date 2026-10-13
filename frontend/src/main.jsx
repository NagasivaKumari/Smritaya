import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import Connect from './views/Connect.jsx'
import './styles.css'

// Omi's Auth URL points at /connect so it can append ?uid=<omi_uid> and link the account.
const isConnect = window.location.pathname.replace(/\/+$/, '') === '/connect'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isConnect ? <Connect /> : <App />}
  </React.StrictMode>,
)
