import { useEffect, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"

import { EmployeePageHeader } from "@/components/employee/EmployeePageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { endpoints } from "@/lib/api"
import { parseShopError } from "@/lib/shopUtils"

export function OwnerShopPage() {
  const qc = useQueryClient()
  const shop = useQuery({ queryKey: ["owner-shop"], queryFn: endpoints.owner.shop })
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState("")
  const [msg, setMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!shop.data) return
    setName(shop.data.name)
    setDescription(shop.data.description || "")
    setCategory(shop.data.category || "")
  }, [shop.data])

  const save = useMutation({
    mutationFn: () =>
      endpoints.owner.updateShop({
        name: name.trim(),
        description,
        category,
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["owner-shop"] })
      void qc.invalidateQueries({ queryKey: ["owner-dashboard"] })
      setMsg("Shop profile saved")
    },
    onError: (e) => setMsg(parseShopError(e, "Save failed")),
  })

  if (shop.isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="size-6 animate-spin" />
      </div>
    )
  }

  if (shop.isError || !shop.data) {
    return <p className="text-[var(--destructive)]">{parseShopError(shop.error, "Shop not found")}</p>
  }

  return (
    <div className="space-y-6 p-4 md:p-6">
      <EmployeePageHeader
        title="Shop profile"
        description={`Slug: ${shop.data.slug} · Commission ${(shop.data.commission_rate * 100).toFixed(0)}%`}
      />
      {msg && <p className="text-sm">{msg}</p>}
      <form
        className="max-w-xl space-y-4 rounded-xl border border-[var(--border)] bg-[var(--card)] p-5"
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
      >
        <div className="space-y-2">
          <Label>Shop name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="space-y-2">
          <Label>Category</Label>
          <Input value={category} onChange={(e) => setCategory(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label>Description</Label>
          <textarea
            className="min-h-24 w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <p className="text-xs text-[var(--muted-foreground)]">
          Status: {shop.data.is_approved ? "Approved" : "Pending approval"}
          {shop.data.rejection_reason ? ` — ${shop.data.rejection_reason}` : ""}
        </p>
        <Button type="submit" className="btn-brand" disabled={save.isPending}>
          {save.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
          Save profile
        </Button>
      </form>
    </div>
  )
}
