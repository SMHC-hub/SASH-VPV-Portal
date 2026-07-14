import { Link, useNavigate } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2, Minus, Plus, Trash2 } from "lucide-react"

import { CustomerPageHeader } from "@/components/customer/CustomerPageHeader"
import { Button } from "@/components/ui/button"
import { endpoints } from "@/lib/api"
import { formatPkr, parseShopError, productImageUrl } from "@/lib/shopUtils"
import { useAuthStore } from "@/store/useAuthStore"

export function CartPage() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)
  const isCustomer = useAuthStore((s) => s.isCustomer())

  const cart = useQuery({ queryKey: ["cart"], queryFn: endpoints.cart.get })

  const update = useMutation({
    mutationFn: ({ id, quantity }: { id: number; quantity: number }) =>
      endpoints.cart.update(id, quantity),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["cart"] }),
  })
  const remove = useMutation({
    mutationFn: (id: number) => endpoints.cart.remove(id),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["cart"] }),
  })
  const clear = useMutation({
    mutationFn: endpoints.cart.clear,
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["cart"] }),
  })

  const data = cart.data
  const items = data?.items ?? []

  const checkout = () => {
    if (!token || !isCustomer) {
      navigate("/user/login", { state: { from: "/member/checkout" } })
      return
    }
    navigate("/member/checkout")
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
      <CustomerPageHeader
        title="Your cart"
        description="Pay with Palm Vein (VeinPay Wallet) at checkout."
        action={
          <Button asChild variant="outline" size="sm">
            <Link to="/member/shop">Continue shopping</Link>
          </Button>
        }
      />

      {cart.isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="size-6 animate-spin" />
        </div>
      ) : cart.isError ? (
        <p className="text-[var(--destructive)]">{parseShopError(cart.error, "Failed to load cart")}</p>
      ) : items.length === 0 ? (
        <div className="customer-card p-8 text-center text-sm text-[var(--muted-foreground)]">
          Cart is empty.{" "}
          <Link to="/member/shop" className="text-[var(--primary)] underline">
            Browse the shop
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.warnings?.map((w) => (
            <div
              key={w}
              className="rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm"
            >
              {w}
            </div>
          ))}

          <ul className="space-y-3">
            {items.map((item) => (
              <li key={item.id} className="customer-card flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
                <Link
                  to={`/member/shop/${item.product_slug}`}
                  className="h-16 w-16 shrink-0 overflow-hidden rounded-md bg-[var(--muted)]"
                >
                  {productImageUrl(null, item.image_url) ? (
                    <img
                      src={productImageUrl(null, item.image_url)!}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  ) : null}
                </Link>
                <div className="flex-1">
                  <Link
                    to={`/member/shop/${item.product_slug}`}
                    className="font-semibold hover:underline"
                  >
                    {item.name}
                  </Link>
                  <p className="text-xs text-[var(--muted-foreground)]">{item.shop_name}</p>
                  <p className="mt-1 text-sm font-medium">{formatPkr(item.unit_price)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    size="icon"
                    variant="outline"
                    disabled={update.isPending || item.quantity <= 1}
                    onClick={() => update.mutate({ id: item.id, quantity: item.quantity - 1 })}
                  >
                    <Minus className="size-4" />
                  </Button>
                  <span className="w-8 text-center text-sm">{item.quantity}</span>
                  <Button
                    size="icon"
                    variant="outline"
                    disabled={update.isPending}
                    onClick={() => update.mutate({ id: item.id, quantity: item.quantity + 1 })}
                  >
                    <Plus className="size-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => remove.mutate(item.id)}
                    aria-label="Remove"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
                <div className="text-right font-semibold sm:w-28">{formatPkr(item.line_total)}</div>
              </li>
            ))}
          </ul>

          <div className="customer-card space-y-2 p-5">
            <div className="flex justify-between text-sm">
              <span>Subtotal</span>
              <span>{formatPkr(data!.subtotal_pkr)}</span>
            </div>
            <div className="flex justify-between text-sm text-[var(--muted-foreground)]">
              <span>Platform fee</span>
              <span>{formatPkr(data!.platform_fee_pkr)}</span>
            </div>
            <div className="flex justify-between border-t border-[var(--border)] pt-2 text-lg font-bold">
              <span>Total</span>
              <span className="text-[var(--primary)]">{formatPkr(data!.total_pkr)}</span>
            </div>
            <p className="text-xs text-[var(--muted-foreground)]">
              Payment method: Pay with Palm Vein (VeinPay Wallet)
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              <Button className="btn-brand" onClick={checkout}>
                Proceed to pay
              </Button>
              <Button variant="outline" onClick={() => clear.mutate()} disabled={clear.isPending}>
                Clear cart
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
