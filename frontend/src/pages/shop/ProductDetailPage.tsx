import { useState } from "react"
import { Link, useParams } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ArrowLeft, Loader2, Star } from "lucide-react"

import { CustomerPageHeader } from "@/components/customer/CustomerPageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { endpoints } from "@/lib/api"
import { formatPkr, parseShopError, productImageUrl } from "@/lib/shopUtils"

export function ProductDetailPage() {
  const { slug = "" } = useParams()
  const qc = useQueryClient()
  const [qty, setQty] = useState(1)
  const [msg, setMsg] = useState<string | null>(null)

  const product = useQuery({
    queryKey: ["shop-product", slug],
    queryFn: () => endpoints.shop.product(slug),
    enabled: Boolean(slug),
  })

  const add = useMutation({
    mutationFn: () => endpoints.cart.add(product.data!.id, qty),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["cart"] })
      setMsg("Added to cart")
    },
    onError: (e) => setMsg(parseShopError(e, "Could not add")),
  })

  if (product.isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin text-[var(--muted-foreground)]" />
      </div>
    )
  }

  if (product.isError || !product.data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <p className="text-[var(--destructive)]">{parseShopError(product.error, "Product not found")}</p>
        <Button asChild variant="outline" className="mt-4">
          <Link to="/member/shop">Back to shop</Link>
        </Button>
      </div>
    )
  }

  const p = product.data

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 sm:px-6">
      <Button asChild variant="ghost" size="sm" className="mb-4 -ml-2">
        <Link to="/member/shop">
          <ArrowLeft className="size-4" /> Back
        </Link>
      </Button>
      <CustomerPageHeader title={p.name} description={`Sold by ${p.shop_name}`} />

      <div className="grid gap-6 md:grid-cols-2">
        <div className="customer-card aspect-square overflow-hidden bg-[var(--muted)]">
          {productImageUrl(p.images) ? (
            <img
              src={productImageUrl(p.images)!}
              alt={p.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-[var(--muted-foreground)]">
              {p.category || "Product image"}
            </div>
          )}
        </div>
        <div className="customer-card space-y-4 p-5">
          <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
            <Star className="size-4 fill-amber-400 text-amber-400" />
            {p.avg_rating.toFixed(1)} ({p.review_count} reviews)
          </div>
          <p className="text-3xl font-bold text-[var(--primary)]">{formatPkr(p.price_pkr)}</p>
          <p className="text-sm text-[var(--muted-foreground)]">
            {p.stock_status === "out_of_stock"
              ? "Out of stock"
              : p.stock_status === "low_stock"
                ? `Only ${p.stock_qty} left`
                : "In stock"}
          </p>
          <p className="text-sm leading-relaxed">{p.description || p.short_desc}</p>
          <div className="flex items-center gap-3">
            <label className="text-sm" htmlFor="qty">
              Qty
            </label>
            <Input
              id="qty"
              type="number"
              min={1}
              max={Math.max(1, p.stock_qty)}
              className="w-20"
              value={qty}
              onChange={(e) => setQty(Math.max(1, Number(e.target.value) || 1))}
            />
          </div>
          {msg && <p className="text-sm">{msg}</p>}
          <div className="flex flex-wrap gap-2">
            <Button
              className="btn-brand"
              disabled={p.stock_status === "out_of_stock" || add.isPending}
              onClick={() => add.mutate()}
            >
              {add.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
              Add to cart
            </Button>
            <Button asChild variant="outline">
              <Link to="/member/cart">View cart</Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
