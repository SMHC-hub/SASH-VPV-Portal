import { Navigate, useLocation } from "react-router-dom"

import { useAuthStore } from "@/store/useAuthStore"

function roleHome(role: string | undefined) {
  if (role === "admin") return "/dashboard"
  if (role === "customer") return "/"
  if (role === "shop_owner") return "/owner/dashboard"
  return "/employee/dashboard"
}

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)
  const location = useLocation()

  if (!token) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (role !== "admin") return <Navigate to={roleHome(role)} replace />
  return <>{children}</>
}

export function EmployeeRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)
  const location = useLocation()

  if (!token) return <Navigate to="/employee/login" replace state={{ from: location.pathname }} />
  if (role === "admin") return <Navigate to="/dashboard" replace />
  if (role === "customer") return <Navigate to="/" replace />
  if (role === "shop_owner") return <Navigate to="/owner/dashboard" replace />
  if (role !== "employee") return <Navigate to="/employee/login" replace />
  return <>{children}</>
}

export function ShopOwnerRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)
  const location = useLocation()

  if (!token) return <Navigate to="/owner/login" replace state={{ from: location.pathname }} />
  if (role !== "shop_owner") return <Navigate to={roleHome(role)} replace />
  return <>{children}</>
}

export function CustomerRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)
  const location = useLocation()

  if (!token) return <Navigate to="/user/login" replace state={{ from: location.pathname }} />
  if (role === "admin") return <Navigate to="/dashboard" replace />
  if (role === "employee") return <Navigate to="/employee/dashboard" replace />
  if (role === "shop_owner") return <Navigate to="/owner/dashboard" replace />
  if (role !== "customer") return <Navigate to="/user/login" replace />
  return <>{children}</>
}

/** @deprecated use AdminRoute */
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return <AdminRoute>{children}</AdminRoute>
}

export function PublicOnlyRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)
  if (token && role === "admin") return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export function EmployeePublicRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)
  if (token && role === "employee") return <Navigate to="/employee/dashboard" replace />
  if (token && role === "shop_owner") return <Navigate to="/owner/dashboard" replace />
  return <>{children}</>
}

export function ShopOwnerPublicRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)
  if (token && role === "shop_owner") return <Navigate to="/owner/dashboard" replace />
  return <>{children}</>
}

export function CustomerPublicRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  const role = useAuthStore((s) => s.user?.role)
  if (token && role === "customer") return <Navigate to="/" replace />
  return <>{children}</>
}
