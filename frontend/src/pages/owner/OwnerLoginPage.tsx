import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { useMutation } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"

import { AuthLayout } from "@/components/AuthLayout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { endpoints } from "@/lib/api"
import { parseShopError } from "@/lib/shopUtils"
import { useAuthStore } from "@/store/useAuthStore"

export function OwnerLoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState("demo-shop@example.com")
  const [password, setPassword] = useState("DemoShop123!")
  const [error, setError] = useState<string | null>(null)

  const login = useMutation({
    mutationFn: () => endpoints.auth.login(email, password),
    onSuccess: (data) => {
      const role = data.user.role ?? ""
      if (role !== "shop_owner") {
        setError(
          role === "employee"
            ? "Employee accounts use /employee/login"
            : role === "customer"
              ? "Members use /user/login"
              : "This portal is for shop owners only",
        )
        return
      }
      setAuth(data.access_token, { ...data.user, role: "shop_owner" })
      navigate("/owner/dashboard")
    },
    onError: (err) => setError(parseShopError(err, "Invalid email or password")),
  })

  return (
    <AuthLayout themePortal="employee" logoSubtitle="Shop Owner">
      <div className="mx-auto w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Shop Owner</h1>
          <p className="mt-1 text-sm text-[var(--muted-foreground)]">
            Manage products and inventory for VeinPay Shop
          </p>
        </div>
        <form
          className="space-y-4 rounded-xl border border-[var(--border)] bg-[var(--card)] p-6"
          onSubmit={(e) => {
            e.preventDefault()
            setError(null)
            login.mutate()
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error && <p className="text-sm text-[var(--destructive)]">{error}</p>}
          <Button type="submit" className="btn-brand w-full" disabled={login.isPending}>
            {login.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Sign in
          </Button>
        </form>
        <p className="text-center text-xs text-[var(--muted-foreground)]">
          Admin?{" "}
          <Link to="/login" className="hover:text-[var(--primary)] hover:underline">
            Admin sign in
          </Link>
          {" · "}
          Employee?{" "}
          <Link to="/employee/login" className="hover:text-[var(--primary)] hover:underline">
            Employee sign in
          </Link>
          {" · "}
          Member?{" "}
          <Link to="/user/login" className="hover:text-[var(--primary)] hover:underline">
            Member sign in
          </Link>
        </p>
      </div>
    </AuthLayout>
  )
}
