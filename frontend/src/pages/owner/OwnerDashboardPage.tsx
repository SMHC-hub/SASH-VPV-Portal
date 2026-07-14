import { Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { AlertTriangle, Loader2, Package, ShoppingBag } from "lucide-react"

import { EmployeePageHeader } from "@/components/employee/EmployeePageHeader"
import { EmployeeStatCard } from "@/components/employee/EmployeeStatCard"
import { Button } from "@/components/ui/button"
import { endpoints } from "@/lib/api"
import { formatPkr, parseShopError } from "@/lib/shopUtils"

export function OwnerDashboardPage() {
  const dash = useQuery({
    queryKey: ["owner-dashboard"],
    queryFn: endpoints.owner.dashboard,
  })

  if (dash.isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin" />
      </div>
    )
  }

  if (dash.isError || !dash.data) {
    return (
      <p className="text-[var(--destructive)]">{parseShopError(dash.error, "Failed to load dashboard")}</p>
    )
  }

  const d = dash.data

  return (
    <div className="space-y-6 p-4 md:p-6">
      <EmployeePageHeader
        title={d.shop_name}
        description={
          d.is_approved
            ? "Your shop is approved and live on the marketplace."
            : "Shop pending admin approval — products stay hidden until approved."
        }
        action={
          <Button asChild className="btn-brand">
            <Link to="/owner/products">Manage products</Link>
          </Button>
        }
      />

      {!d.is_approved && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          Awaiting admin approval before listings go public.
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <EmployeeStatCard
          label="Today's sales"
          value={formatPkr(d.today_sales_pkr)}
          icon={<ShoppingBag className="size-4" />}
        />
        <EmployeeStatCard label="Today's orders" value={String(d.today_orders)} icon={<Package className="size-4" />} />
        <EmployeeStatCard label="Products listed" value={String(d.products_listed)} icon={<Package className="size-4" />} />
        <EmployeeStatCard
          label="Pending approval"
          value={String(d.products_pending_approval)}
          icon={<AlertTriangle className="size-4" />}
        />
      </div>

      <section className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
        <h2 className="mb-3 font-semibold">Low stock (under {d.low_stock_threshold})</h2>
        {d.low_stock.length === 0 ? (
          <p className="text-sm text-[var(--muted-foreground)]">No low-stock alerts.</p>
        ) : (
          <ul className="divide-y divide-[var(--border)]">
            {d.low_stock.map((p) => (
              <li key={p.id} className="flex justify-between py-2 text-sm">
                <span>{p.name}</span>
                <span className="font-medium text-amber-600">{p.stock_qty} left</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
