import { Outlet, useNavigate } from "react-router-dom"
import { Home, Package, Settings, Store } from "lucide-react"

import { SidebarLayout, type SidebarNavItem } from "@/components/SidebarLayout"
import { EmployeeThemeToggle } from "@/components/employee/EmployeeThemeToggle"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/useAuthStore"
import { useEmployeeThemeStore } from "@/store/useEmployeeThemeStore"

const NAV: SidebarNavItem[] = [
  { to: "/owner/dashboard", label: "Dashboard", icon: Home, end: true, subtitle: "Sales overview" },
  { to: "/owner/products", label: "Products", icon: Package, subtitle: "Catalog & stock" },
  { to: "/owner/shop", label: "Shop profile", icon: Store, subtitle: "Name & branding" },
  { to: "/owner/settings", label: "Account", icon: Settings, subtitle: "Sign out & theme" },
]

export function OwnerShell() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const theme = useEmployeeThemeStore((s) => s.theme)
  const navigate = useNavigate()
  const isLight = theme === "light"

  return (
    <SidebarLayout
      navItems={NAV}
      logoLink="/owner/dashboard"
      logoSubtitle="Shop Owner"
      portalClassName="employee-portal"
      themeClassName={cn(isLight ? "employee-theme-light" : "employee-theme-dark")}
      backgroundVariant={isLight ? "light" : "dark"}
      sidebarClassName="employee-sidebar border-[var(--emp-sidebar-border)]"
      headerClassName="employee-sidebar border-[var(--emp-sidebar-border)]"
      userName={user?.full_name}
      userMeta={user?.email ?? undefined}
      onSignOut={() => void logout().then(() => navigate("/owner/login"))}
      headerEnd={<EmployeeThemeToggle />}
    >
      <Outlet />
    </SidebarLayout>
  )
}
