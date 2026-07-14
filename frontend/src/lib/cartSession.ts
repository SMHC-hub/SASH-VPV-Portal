/** Guest cart session id (X-Session-Id) persisted in localStorage. */
const KEY = "veinpay-cart-session"

function randomId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID()
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

export function getCartSessionId(): string {
  try {
    let id = localStorage.getItem(KEY)
    if (!id) {
      id = randomId()
      localStorage.setItem(KEY, id)
    }
    return id
  } catch {
    return randomId()
  }
}

export function clearCartSessionId() {
  try {
    localStorage.removeItem(KEY)
  } catch {
    /* ignore */
  }
}
