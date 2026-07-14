import { useState } from "react"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Check, Loader2, Store, X } from "lucide-react"

import { AdminPageHeader } from "@/components/AdminPageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { endpoints, type AdminProductModerationItem, type AdminShopModerationItem } from "@/lib/api"
import { formatPkr, parseShopError, productImageUrl } from "@/lib/shopUtils"
import { cn } from "@/lib/utils"

type Tab = "shops" | "products"

export function AdminMarketplacePage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>("shops")
  const [rejectTarget, setRejectTarget] = useState<
    { kind: "shop" | "product"; id: number; name: string } | null
  >(null)
  const [rejectReason, setRejectReason] = useState("")
  const [flash, setFlash] = useState<string | null>(null)

  const shops = useQuery({
    queryKey: ["admin-shops-pending"],
    queryFn: endpoints.admin.pendingShops,
  })
  const products = useQuery({
    queryKey: ["admin-products-pending"],
    queryFn: endpoints.admin.pendingProducts,
  })

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ["admin-shops-pending"] })
    void qc.invalidateQueries({ queryKey: ["admin-products-pending"] })
  }

  const approveShop = useMutation({
    mutationFn: (id: number) => endpoints.admin.approveShop(id),
    onSuccess: (r) => {
      setFlash(r.message)
      invalidate()
    },
    onError: (e) => setFlash(parseShopError(e, "Approve shop failed")),
  })
  const rejectShop = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      endpoints.admin.rejectShop(id, reason),
    onSuccess: (r) => {
      setFlash(r.message)
      setRejectTarget(null)
      setRejectReason("")
      invalidate()
    },
    onError: (e) => setFlash(parseShopError(e, "Reject shop failed")),
  })
  const approveProduct = useMutation({
    mutationFn: (id: number) => endpoints.admin.approveProduct(id),
    onSuccess: (r) => {
      setFlash(r.message)
      invalidate()
    },
    onError: (e) => setFlash(parseShopError(e, "Approve product failed")),
  })
  const rejectProduct = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) =>
      endpoints.admin.rejectProduct(id, reason),
    onSuccess: (r) => {
      setFlash(r.message)
      setRejectTarget(null)
      setRejectReason("")
      invalidate()
    },
    onError: (e) => setFlash(parseShopError(e, "Reject product failed")),
  })

  const pendingShops = shops.data?.shops ?? []
  const pendingProducts = products.data?.products ?? []
  const busy =
    approveShop.isPending ||
    rejectShop.isPending ||
    approveProduct.isPending ||
    rejectProduct.isPending

  const submitReject = () => {
    if (!rejectTarget || rejectReason.trim().length < 3) return
    if (rejectTarget.kind === "shop") {
      rejectShop.mutate({ id: rejectTarget.id, reason: rejectReason.trim() })
    } else {
      rejectProduct.mutate({ id: rejectTarget.id, reason: rejectReason.trim() })
    }
  }

  return (
    <div className="space-y-6">
      <AdminPageHeader
        title="Marketplace"
        description="Approve or reject pending shops and product listings before they go live."
      />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="glass-panel p-4">
          <div className="text-xs uppercase text-[var(--muted-foreground)]">Pending shops</div>
          <div className="mt-1 text-2xl font-bold tabular-nums">{pendingShops.length}</div>
        </div>
        <div className="glass-panel p-4">
          <div className="text-xs uppercase text-[var(--muted-foreground)]">Pending products</div>
          <div className="mt-1 text-2xl font-bold tabular-nums">{pendingProducts.length}</div>
        </div>
      </div>

      {flash ? (
        <div className="rounded-lg border border-[var(--border)] bg-[var(--accent)]/40 px-3 py-2 text-sm">
          {flash}
        </div>
      ) : null}

      <div className="flex gap-2">
        {(
          [
            { id: "shops" as const, label: "Shops", count: pendingShops.length },
            { id: "products" as const, label: "Products", count: pendingProducts.length },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              "rounded-lg border px-4 py-2 text-sm font-medium transition",
              tab === t.id
                ? "border-[var(--primary)]/40 bg-[color-mix(in_srgb,var(--primary)_12%,transparent)]"
                : "border-transparent hover:bg-[var(--accent)]",
            )}
          >
            {t.label}
            <span className="ml-2 tabular-nums text-[var(--muted-foreground)]">({t.count})</span>
          </button>
        ))}
      </div>

      {tab === "shops" ? (
        <ShopQueue
          loading={shops.isPending}
          items={pendingShops}
          busy={busy}
          onApprove={(id) => approveShop.mutate(id)}
          onReject={(s) => {
            setRejectTarget({ kind: "shop", id: s.id, name: s.name })
            setRejectReason("")
          }}
        />
      ) : (
        <ProductQueue
          loading={products.isPending}
          items={pendingProducts}
          busy={busy}
          onApprove={(id) => approveProduct.mutate(id)}
          onReject={(p) => {
            setRejectTarget({ kind: "product", id: p.id, name: p.name })
            setRejectReason("")
          }}
        />
      )}

      {rejectTarget ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="glass-panel w-full max-w-md space-y-4 p-5">
            <h3 className="text-lg font-semibold">Reject {rejectTarget.kind}</h3>
            <p className="text-sm text-[var(--muted-foreground)]">
              Provide a reason for rejecting <strong>{rejectTarget.name}</strong>.
            </p>
            <Input
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Reason (min 3 characters)"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setRejectTarget(null)
                  setRejectReason("")
                }}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                disabled={rejectReason.trim().length < 3 || busy}
                onClick={submitReject}
              >
                {busy ? <Loader2 className="size-4 animate-spin" /> : "Reject"}
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

function ShopQueue({
  loading,
  items,
  busy,
  onApprove,
  onReject,
}: {
  loading: boolean
  items: AdminShopModerationItem[]
  busy: boolean
  onApprove: (id: number) => void
  onReject: (shop: AdminShopModerationItem) => void
}) {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="size-6 animate-spin" />
      </div>
    )
  }
  if (items.length === 0) {
    return (
      <div className="glass-panel p-8 text-center text-sm text-[var(--muted-foreground)]">
        No shops awaiting approval.
      </div>
    )
  }
  return (
    <ul className="space-y-3">
      {items.map((s) => (
        <li key={s.id} className="glass-panel flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-[var(--muted)]">
            <Store className="size-5 text-[var(--muted-foreground)]" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-semibold">{s.name}</div>
            <p className="text-xs text-[var(--muted-foreground)]">
              {s.owner_name || "Owner"} · {s.owner_email || "—"} · {s.product_count} products
            </p>
            {s.description ? (
              <p className="mt-1 line-clamp-2 text-sm text-[var(--muted-foreground)]">{s.description}</p>
            ) : null}
            {s.rejection_reason ? (
              <p className="mt-1 text-xs text-[var(--destructive)]">Prior: {s.rejection_reason}</p>
            ) : null}
          </div>
          <div className="flex gap-2">
            <Button size="sm" disabled={busy} onClick={() => onApprove(s.id)}>
              <Check className="size-4" />
              Approve
            </Button>
            <Button size="sm" variant="outline" disabled={busy} onClick={() => onReject(s)}>
              <X className="size-4" />
              Reject
            </Button>
          </div>
        </li>
      ))}
    </ul>
  )
}

function ProductQueue({
  loading,
  items,
  busy,
  onApprove,
  onReject,
}: {
  loading: boolean
  items: AdminProductModerationItem[]
  busy: boolean
  onApprove: (id: number) => void
  onReject: (product: AdminProductModerationItem) => void
}) {
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="size-6 animate-spin" />
      </div>
    )
  }
  if (items.length === 0) {
    return (
      <div className="glass-panel p-8 text-center text-sm text-[var(--muted-foreground)]">
        No products awaiting approval.
      </div>
    )
  }
  return (
    <ul className="space-y-3">
      {items.map((p) => {
        const img = productImageUrl(p.images)
        return (
          <li key={p.id} className="glass-panel flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
            <div className="h-16 w-16 shrink-0 overflow-hidden rounded-lg bg-[var(--muted)]">
              {img ? (
                <img src={img} alt="" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-[10px] text-[var(--muted-foreground)]">
                  No image
                </div>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-semibold">{p.name}</div>
              <p className="text-xs text-[var(--muted-foreground)]">
                {p.shop_name || "Shop"} · {p.category || "—"} · {formatPkr(p.price_pkr)} · stock{" "}
                {p.stock_qty}
              </p>
              {p.short_desc ? (
                <p className="mt-1 line-clamp-2 text-sm text-[var(--muted-foreground)]">{p.short_desc}</p>
              ) : null}
              {p.rejection_reason ? (
                <p className="mt-1 text-xs text-[var(--destructive)]">Prior: {p.rejection_reason}</p>
              ) : null}
            </div>
            <div className="flex gap-2">
              <Button size="sm" disabled={busy} onClick={() => onApprove(p.id)}>
                <Check className="size-4" />
                Approve
              </Button>
              <Button size="sm" variant="outline" disabled={busy} onClick={() => onReject(p)}>
                <X className="size-4" />
                Reject
              </Button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
