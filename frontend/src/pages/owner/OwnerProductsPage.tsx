import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2, Plus, Trash2 } from "lucide-react"

import { EmployeePageHeader } from "@/components/employee/EmployeePageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { endpoints, type OwnerProduct } from "@/lib/api"
import { formatPkr, parseShopError, productImageUrl } from "@/lib/shopUtils"

export function OwnerProductsPage() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<OwnerProduct | null>(null)
  const [name, setName] = useState("")
  const [category, setCategory] = useState("Electronics")
  const [price, setPrice] = useState("100")
  const [stock, setStock] = useState("10")
  const [shortDesc, setShortDesc] = useState("")
  const [msg, setMsg] = useState<string | null>(null)

  const products = useQuery({
    queryKey: ["owner-products"],
    queryFn: () => endpoints.owner.products(),
  })

  const resetForm = () => {
    setEditing(null)
    setName("")
    setCategory("Electronics")
    setPrice("100")
    setStock("10")
    setShortDesc("")
    setShowForm(false)
  }

  const openEdit = (p: OwnerProduct) => {
    setEditing(p)
    setName(p.name)
    setCategory(p.category || "Electronics")
    setPrice(String(p.price_pkr))
    setStock(String(p.stock_qty))
    setShortDesc(p.short_desc || "")
    setShowForm(true)
  }

  const save = useMutation({
    mutationFn: async () => {
      const body = {
        name: name.trim(),
        category,
        short_desc: shortDesc || null,
        price_pkr: Number(price),
        stock_qty: Number(stock),
        is_active: true,
      }
      if (editing) return endpoints.owner.updateProduct(editing.id, body)
      return endpoints.owner.createProduct(body)
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["owner-products"] })
      void qc.invalidateQueries({ queryKey: ["owner-dashboard"] })
      setMsg(editing ? "Product updated (pending re-approval if material change)" : "Product created — pending admin approval")
      resetForm()
    },
    onError: (e) => setMsg(parseShopError(e, "Save failed")),
  })

  const del = useMutation({
    mutationFn: (id: number) => endpoints.owner.deleteProduct(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["owner-products"] })
      void qc.invalidateQueries({ queryKey: ["owner-dashboard"] })
    },
  })

  const toggleActive = useMutation({
    mutationFn: (p: OwnerProduct) =>
      endpoints.owner.updateProduct(p.id, { is_active: !p.is_active }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["owner-products"] }),
  })

  return (
    <div className="space-y-6 p-4 md:p-6">
      <EmployeePageHeader
        title="Products"
        description="Add and edit listings. New or materially changed products need admin approval."
        action={
          <Button
            className="btn-brand"
            onClick={() => {
              resetForm()
              setShowForm(true)
            }}
          >
            <Plus className="size-4" /> Add product
          </Button>
        }
      />

      {msg && (
        <div className="rounded-md border border-[var(--border)] bg-[var(--card)] px-3 py-2 text-sm">{msg}</div>
      )}

      {showForm && (
        <form
          className="grid gap-3 rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 sm:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault()
            save.mutate()
          }}
        >
          <div className="space-y-2 sm:col-span-2">
            <Label>Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label>Category</Label>
            <Input value={category} onChange={(e) => setCategory(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Price (PKR)</Label>
            <Input type="number" min={1} step="1" value={price} onChange={(e) => setPrice(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label>Stock</Label>
            <Input type="number" min={0} value={stock} onChange={(e) => setStock(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label>Short description</Label>
            <Input value={shortDesc} onChange={(e) => setShortDesc(e.target.value)} />
          </div>
          <div className="flex gap-2 sm:col-span-2">
            <Button type="submit" className="btn-brand" disabled={save.isPending}>
              {save.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
              {editing ? "Save changes" : "Create product"}
            </Button>
            <Button type="button" variant="outline" onClick={resetForm}>
              Cancel
            </Button>
          </div>
        </form>
      )}

      {products.isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="size-6 animate-spin" />
        </div>
      ) : products.isError ? (
        <p className="text-[var(--destructive)]">{parseShopError(products.error, "Failed to load")}</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-[var(--border)] bg-[var(--muted)]/40 text-xs uppercase tracking-wide text-[var(--muted-foreground)]">
              <tr>
                <th className="px-3 py-2">Product</th>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2">Price</th>
                <th className="px-3 py-2">Stock</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {(products.data?.products ?? []).map((p) => {
                const img = productImageUrl(p.images)
                return (
                <tr key={p.id} className="border-b border-[var(--border)]">
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 shrink-0 overflow-hidden rounded-md bg-[var(--muted)]">
                        {img ? (
                          <img src={img} alt="" className="h-full w-full object-cover" />
                        ) : null}
                      </div>
                      <span className="font-medium">{p.name}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2">{p.category}</td>
                  <td className="px-3 py-2">{formatPkr(p.price_pkr)}</td>
                  <td className="px-3 py-2">{p.stock_qty}</td>
                  <td className="px-3 py-2">
                    <span className="text-xs">
                      {p.is_approved ? "Approved" : "Pending"}
                      {" · "}
                      {p.is_active ? "Active" : "Hidden"}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex justify-end gap-1">
                      <Button size="sm" variant="outline" onClick={() => openEdit(p)}>
                        Edit
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => toggleActive.mutate(p)}>
                        {p.is_active ? "Hide" : "Show"}
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => {
                          if (window.confirm(`Delete ${p.name}?`)) del.mutate(p.id)
                        }}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              )})}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
