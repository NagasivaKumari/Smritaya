const API = import.meta.env.VITE_API_BASE || '/api'
const DEFAULT_UID = 'founder'
const TOKEN_KEY = 'smritaya:token'

export function authToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setAuthToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

/** The account-scoped uid for authed users; a stable uid otherwise.
 *  Override per-request with ?uid=... (Omi webhooks / multi-device demos). */
export function uid() {
  return new URLSearchParams(location.search).get('uid') || DEFAULT_UID
}

async function call(path, options = {}) {
  const sep = path.includes('?') ? '&' : '?'
  const res = await fetch(`${API}${path}${sep}uid=${encodeURIComponent(uid())}`, {
    headers: {
      'Content-Type': 'application/json',
      // ponytail: ngrok-free serves an interstitial to browser requests; this skips it
      'ngrok-skip-browser-warning': 'true',
      ...(authToken() ? { Authorization: `Bearer ${authToken()}` } : {}),
    },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${body.slice(0, 200)}`)
  }
  return res.json()
}

export const api = {
  health: () => call('/health'),

  content: () => call('/content'),

  copy: () => call('/copy'),

  auth: {
    signup: (email, password) => call('/auth/signup', { method: 'POST', body: JSON.stringify({ email, password }) }),
    login: (email, password) => call('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
    logout: () => call('/auth/logout', { method: 'POST' }),
    me: async () => {
      if (!authToken()) return null
      try {
        const res = await call('/auth/me')
        return res.user
      } catch {
        return null
      }
    },
    forgot: (email) => call('/auth/forgot', { method: 'POST', body: JSON.stringify({ email }) }),
    reset: (token, password) => call('/auth/reset', { method: 'POST', body: JSON.stringify({ token, password }) }),
    linkOmi: (omi_uid) => call('/auth/omi', { method: 'POST', body: JSON.stringify({ omi_uid }) }),
  },

  deeds: (params = {}) => {
    const q = new URLSearchParams()
    if (params.status) q.set('status', params.status)
    if (params.counterparty) q.set('counterparty', params.counterparty)
    if (params.overdue !== undefined) q.set('overdue', params.overdue)
    const qs = q.toString()
    return call(`/deeds${qs ? `?${qs}` : ''}`)
  },

  ingest: (transcript, speaker) => call('/ingest', { method: 'POST', body: JSON.stringify({ transcript, speaker, uid: uid() }) }),
  createDeed: (deed) => call('/deeds', { method: 'POST', body: JSON.stringify(deed) }),
  remind: (deed_id) => call('/remind', { method: 'POST', body: JSON.stringify({ deed_id }) }),
  setStatus: (deed_id, status) => call('/status', { method: 'POST', body: JSON.stringify({ deed_id, status }) }),
  ask: (question) => call('/ask', { method: 'POST', body: JSON.stringify({ question, uid: uid() }) }),
  hearing: (deed_id) => call('/hearing', { method: 'POST', body: JSON.stringify({ deed_id, uid: uid() }) }),
  chamber: (name) => call(`/chamber/${encodeURIComponent(name)}`),
  forget: (payload) => call('/forget', { method: 'POST', body: JSON.stringify({ ...payload, uid: uid() }) }),
}

export function fmtDate(ts) {
  if (!ts) return '—'
  return new Date(ts * 1000).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function fmtMoney(amount, currency = 'INR') {
  if (amount === null || amount === undefined) return null
  return `₹${Number(amount).toLocaleString('en-IN')}`
}

export const MEMORY_LABEL = { local: 'private', remote: 'cloud' }
export const AGENT_LABEL = { 'local-reasoner': 'on-device', 'lyzr/live': 'live' }
export const EMBEDDER_LABEL = (v) => (!v ? '—' : String(v).includes('local') || String(v).includes('fastembed') ? 'on-device' : v)

export function tpl(str, vars = {}) {
  return Object.entries(vars).reduce((s, [k, v]) => s.replace(`{${k}}`, v), str)
}
