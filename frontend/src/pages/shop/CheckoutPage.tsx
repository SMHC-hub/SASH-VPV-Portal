import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { CheckCircle2, Loader2 } from "lucide-react"

import { CustomerPageHeader } from "@/components/customer/CustomerPageHeader"
import { LiveFeedFrame } from "@/components/GlassPanel"
import { LiveFeed } from "@/components/LiveFeed"
import { LiveFeedToolbar } from "@/components/LiveFeedToolbar"
import { Button } from "@/components/ui/button"
import { endpoints } from "@/lib/api"
import { formatPkr, parseShopError } from "@/lib/shopUtils"

type Step = "review" | "scan" | "done"

export function CheckoutPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [step, setStep] = useState<Step>("review")
  const [error, setError] = useState<string | null>(null)
  const [orderId, setOrderId] = useState<number | null>(null)
  const [orderNumber, setOrderNumber] = useState<string | null>(null)
  const [matchThreshold, setMatchThreshold] = useState(0.32)
  const [receipt, setReceipt] = useState<{
    total_pkr: number
    new_balance_pkr?: number | null
    palm_confidence?: number | null
    message: string
  } | null>(null)

  const validation = useQuery({
    queryKey: ["checkout-validate"],
    queryFn: endpoints.checkout.validate,
  })

  const initiate = useMutation({
    mutationFn: endpoints.checkout.initiate,
    onSuccess: (data) => {
      setOrderId(data.order_id)
      setOrderNumber(data.order_number)
      if (typeof data.confidence_required === "number") {
        setMatchThreshold(data.confidence_required)
      }
      setStep("scan")
      setError(null)
    },
    onError: (e) => setError(parseShopError(e, "Could not start checkout")),
  })

  const pay = useMutation({
    mutationFn: async () => {
      if (!orderId) throw new Error("No order")
      return endpoints.checkout.palmPay(orderId)
    },
    onSuccess: (data) => {
      setReceipt({
        total_pkr: data.total_pkr,
        new_balance_pkr: data.new_balance_pkr,
        palm_confidence: data.palm_confidence,
        message: data.message,
      })
      setStep("done")
      setError(null)
      void qc.invalidateQueries({ queryKey: ["cart"] })
    },
    onError: (e) => {
      const msg = parseShopError(e, "Payment failed")
      setError(
        msg.includes("timeout")
          ? "Scan timed out — hold palm steady on the scanner and try again."
          : msg,
      )
    },
  })

  const cancel = useMutation({
    mutationFn: () => endpoints.checkout.cancel(orderId!),
    onSuccess: () => {
      setOrderId(null)
      setStep("review")
      void qc.invalidateQueries({ queryKey: ["checkout-validate"] })
    },
  })

  const v = validation.data

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 sm:px-6">
      <CustomerPageHeader
        title="Checkout"
        description="Confirm your order and scan your palm to pay from VeinPay."
      />

      {validation.isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="size-6 animate-spin" />
        </div>
      ) : step === "done" && receipt ? (
        <div className="customer-card space-y-4 p-6 text-center">
          <CheckCircle2 className="mx-auto size-12 text-emerald-500" />
          <h2 className="text-xl font-bold">Order confirmed</h2>
          {orderNumber && <p className="text-sm text-[var(--muted-foreground)]">#{orderNumber}</p>}
          <p className="text-lg font-semibold text-[var(--primary)]">
            VeinPay debited {formatPkr(receipt.total_pkr)}
          </p>
          {receipt.palm_confidence != null && (
            <p className="text-sm text-[var(--muted-foreground)]">
              Palm match: {Math.round(receipt.palm_confidence * 100)}%
            </p>
          )}
          {receipt.new_balance_pkr != null && (
            <p className="text-sm text-[var(--muted-foreground)]">
              New balance: {formatPkr(receipt.new_balance_pkr)}
            </p>
          )}
          <p className="text-sm">Check the VeinPay app for your receipt.</p>
          <Button className="btn-brand" onClick={() => navigate("/member/shop")}>
            Continue shopping
          </Button>
        </div>
      ) : step === "scan" ? (
        <div className="customer-card space-y-4 p-6">
          <LiveFeedToolbar className="mb-2" showDistance />
          <LiveFeedFrame>
            <LiveFeed size="standard" />
          </LiveFeedFrame>
          <p className="text-center text-sm font-medium">Place your palm on the scanner</p>
          <p className="text-center text-xs text-[var(--muted-foreground)]">
            Order {orderNumber} · Live 1:1 vein match required (cosine ≥{" "}
            {matchThreshold.toFixed(2)} / {Math.round(matchThreshold * 100)}%) before VeinPay debit
          </p>
          {error && <p className="text-sm text-[var(--destructive)]">{error}</p>}
          <div className="flex flex-wrap gap-2">
            <Button className="btn-brand" disabled={pay.isPending} onClick={() => pay.mutate()}>
              {pay.isPending ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Scanning &amp; matching…
                </>
              ) : (
                <>Scan &amp; Pay {v ? formatPkr(v.cart_total) : ""}</>
              )}
            </Button>
            <Button
              variant="outline"
              disabled={!orderId || cancel.isPending || pay.isPending}
              onClick={() => cancel.mutate()}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="customer-card space-y-4 p-5">
          {!v ? (
            <p className="text-[var(--destructive)]">Could not validate checkout</p>
          ) : (
            <>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt>Items</dt>
                  <dd>{v.item_count}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Order total</dt>
                  <dd className="font-semibold">{formatPkr(v.cart_total)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>VeinPay balance</dt>
                  <dd>{formatPkr(v.wallet_balance)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Palm enrolled</dt>
                  <dd>{v.palm_enrolled ? "Yes" : "No"}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Status</dt>
                  <dd className="font-medium">{v.action_required.replaceAll("_", " ")}</dd>
                </div>
              </dl>

              {v.warnings?.map((w) => (
                <p key={w} className="text-sm text-amber-600">
                  {w}
                </p>
              ))}

              {v.action_required === "enroll_palm" && (
                <Button asChild className="btn-brand">
                  <Link to="/member/enrollment">Enroll your palm first</Link>
                </Button>
              )}
              {v.action_required === "topup_wallet" && (
                <p className="text-sm text-[var(--destructive)]">
                  Insufficient balance
                  {v.shortfall != null ? ` — top up at least ${formatPkr(v.shortfall)} in VeinPay` : ""}.
                </p>
              )}
              {v.action_required === "empty_cart" && (
                <Button asChild variant="outline">
                  <Link to="/member/shop">Browse shop</Link>
                </Button>
              )}
              {v.action_required === "proceed_to_scan" && (
                <Button
                  className="btn-brand"
                  disabled={initiate.isPending}
                  onClick={() => initiate.mutate()}
                >
                  {initiate.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
                  Proceed to palm scan
                </Button>
              )}
              {error && <p className="text-sm text-[var(--destructive)]">{error}</p>}
            </>
          )}
        </div>
      )}
    </div>
  )
}
