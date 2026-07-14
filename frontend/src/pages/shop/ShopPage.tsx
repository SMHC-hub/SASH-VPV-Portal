import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2, Search, ShoppingCart, Star } from "lucide-react"

import { CustomerPageHeader } from "@/components/customer/CustomerPageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { endpoints, type ShopProductCard } from "@/lib/api"
import { formatPkr, parseShopError, productImageUrl } from "@/lib/shopUtils"
import { cn } from "@/lib/utils"

export function ShopPage() {
  const qc = useQueryClient()
  const [category, setCategory] = useState<string | undefined>()
  const [search, setSearch] = useState("")
  const [searchQ, setSearchQ] = useState("")
  const [sort, setSort] = useState("newest")
  const [page, setPage] = useState(1)
  const [banner, setBanner] = useState<string | null>(null)

  const cats = useQuery({
    queryKey: ["shop-categories"],
    queryFn: endpoints.shop.categories,
  })

  const products = useQuery({
    queryKey: ["shop-products", category, searchQ, sort, page],
    queryFn: () =>
      endpoints.shop.products({
        category,
        search: searchQ || undefined,
        sort,
        page,
        limit: 12,
      }),
  })

  const cart = useQuery({
    queryKey: ["cart"],
    queryFn: endpoints.cart.summary,
    refetchInterval: 30_000,
  })

  const add = useMutation({
    mutationFn: (p: ShopProductCard) => endpoints.cart.add(p.id, 1),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["cart"] })
      setBanner("Added to cart")
      setTimeout(() => setBanner(null), 2000)
    },
    onError: (e) => setBanner(parseShopError(e, "Could not add to cart")),
  })

  const cartCount = cart.data?.item_count ?? 0
  const list = products.data?.products ?? []
  const totalPages = products.data?.total_pages ?? 0

  const categoryPills = useMemo(() => {
    const items = cats.data?.categories ?? []
    return [{ name: "All", product_count: products.data?.count ?? 0 }, ...items]
  }, [cats.data, products.data?.count])

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <CustomerPageHeader
        title="Shop"
        description="Browse products and pay with palm vein via your VeinPay wallet."
        action={
          <Button asChild className="btn-brand relative">
            <Link to="/member/cart">
              <ShoppingCart className="size-4" />
              Cart
              {cartCount > 0 && (
                <span className="absolute -right-2 -top-2 flex size-5 items-center justify-center rounded-full bg-[var(--primary)] text-[10px] font-bold text-[var(--primary-foreground)]">
                  {cartCount > 99 ? "99+" : cartCount}
                </span>
              )}
            </Link>
          </Button>
        }
      />

      {banner && (
        <div className="mb-4 rounded-md border border-[var(--border)] bg-[var(--card)] px-3 py-2 text-sm">
          {banner}
        </div>
      )}

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <form
          className="flex flex-1 gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            setPage(1)
            setSearchQ(search.trim())
          }}
        >
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
            <Input
              className="pl-9"
              placeholder="Search products or shops…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button type="submit" variant="outline">
            Search
          </Button>
        </form>
        <select
          className="h-9 rounded-md border border-[var(--border)] bg-[var(--card)] px-3 text-sm"
          value={sort}
          onChange={(e) => {
            setSort(e.target.value)
            setPage(1)
          }}
        >
          <option value="newest">Newest</option>
          <option value="price_asc">Price ↑</option>
          <option value="price_desc">Price ↓</option>
          <option value="rating">Top rated</option>
          <option value="name">Name</option>
        </select>
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        {categoryPills.map((c) => {
          const active = (c.name === "All" && !category) || c.name === category
          return (
            <button
              key={c.name}
              type="button"
              onClick={() => {
                setCategory(c.name === "All" ? undefined : c.name)
                setPage(1)
              }}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                active
                  ? "border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-foreground)]"
                  : "border-[var(--border)] text-[var(--muted-foreground)] hover:bg-[var(--accent)]",
              )}
            >
              {c.name}
            </button>
          )
        })}
      </div>

      {products.isLoading ? (
        <div className="flex justify-center py-16 text-[var(--muted-foreground)]">
          <Loader2 className="size-6 animate-spin" />
        </div>
      ) : products.isError ? (
        <div className="customer-card p-6 text-sm text-[var(--destructive)]">
          {parseShopError(products.error, "Failed to load products")}
        </div>
      ) : list.length === 0 ? (
        <div className="customer-card p-8 text-center text-sm text-[var(--muted-foreground)]">
          No products found.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {list.map((p) => (
            <article key={p.id} className="customer-card flex flex-col overflow-hidden">
              <Link to={`/member/shop/${p.slug}`} className="block aspect-[4/3] overflow-hidden bg-[var(--muted)]">
                {productImageUrl(p.images) ? (
                  <img
                    src={productImageUrl(p.images)!}
                    alt={p.name}
                    className="h-full w-full object-cover transition-transform duration-300 hover:scale-[1.03]"
                    loading="lazy"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-xs text-[var(--muted-foreground)]">
                    {p.category || "Product"}
                  </div>
                )}
              </Link>
              <div className="flex flex-1 flex-col gap-2 p-4">
                <Link to={`/member/shop/${p.slug}`} className="font-semibold leading-snug hover:underline">
                  {p.name}
                </Link>
                <p className="line-clamp-2 text-xs text-[var(--muted-foreground)]">
                  {p.short_desc || p.name}
                </p>
                <div className="flex items-center gap-1 text-xs text-[var(--muted-foreground)]">
                  <Star className="size-3 fill-amber-400 text-amber-400" />
                  {p.avg_rating.toFixed(1)} · {p.shop_name}
                </div>
                <div className="mt-auto flex items-center justify-between gap-2 pt-2">
                  <span className="font-bold text-[var(--primary)]">{formatPkr(p.price_pkr)}</span>
                  <Button
                    size="sm"
                    className="btn-brand"
                    disabled={p.stock_status === "out_of_stock" || add.isPending}
                    onClick={() => add.mutate(p)}
                  >
                    Add
                  </Button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-sm text-[var(--muted-foreground)]">
            Page {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
