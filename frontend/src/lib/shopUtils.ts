import { clearCartSessionId, getCartSessionId } from "@/lib/cartSession"
import { endpoints } from "@/lib/api"

/** After customer login — merge guest cart into backend user cart. */
export async function mergeCartAfterLogin(): Promise<void> {
  try {
    const sessionId = getCartSessionId()
    await endpoints.cart.merge(sessionId)
    clearCartSessionId()
    // start a fresh guest session id for future anonymous browsing
    getCartSessionId()
  } catch {
    /* non-fatal — user can still shop */
  }
}

export function formatPkr(amount: number): string {
  return `PKR ${amount.toLocaleString("en-PK", { maximumFractionDigits: 0 })}`
}

/** Resolve primary product image URL from API images JSON. */
export function productImageUrl(
  images: unknown[] | null | undefined,
  fallback?: string | null,
): string | null {
  if (fallback) return fallback
  if (!images || images.length === 0) return null
  const first = images[0]
  if (typeof first === "string" && first) return first
  if (first && typeof first === "object" && "url" in first) {
    const url = (first as { url?: unknown }).url
    if (typeof url === "string" && url) return url
  }
  return null
}

export function parseShopError(err: unknown, fallback: string): string {
  const ax = err as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = ax?.response?.data?.detail
  if (typeof detail === "string") return detail
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const d = detail as { message?: string; confidence?: number; required?: number }
    if (typeof d.message === "string") {
      if (typeof d.confidence === "number" && typeof d.required === "number") {
        return `${d.message} (${Math.round(d.confidence * 100)}% — need ≥ ${Math.round(d.required * 100)}%)`
      }
      return d.message
    }
  }
  if (Array.isArray(detail) && detail[0] && typeof (detail[0] as { msg?: string }).msg === "string") {
    return (detail[0] as { msg: string }).msg
  }
  if (!ax?.response && ax?.message?.includes("Network")) {
    return "Cannot reach server — start the PalmPay backend on :8001"
  }
  return fallback
}
