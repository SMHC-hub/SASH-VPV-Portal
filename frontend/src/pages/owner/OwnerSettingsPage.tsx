import { useNavigate } from "react-router-dom"

import { EmployeePageHeader } from "@/components/employee/EmployeePageHeader"
import { EmployeeThemeToggle } from "@/components/employee/EmployeeThemeToggle"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/store/useAuthStore"

export function OwnerSettingsPage() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  return (
    <div className="space-y-6 p-4 md:p-6">
      <EmployeePageHeader title="Account" description="Theme and session" />
      <div className="max-w-md space-y-4 rounded-xl border border-[var(--border)] bg-[var(--card)] p-5">
        <div className="text-sm">
          <p className="font-medium">{user?.full_name}</p>
          <p className="text-[var(--muted-foreground)]">{user?.email}</p>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm">Theme</span>
          <EmployeeThemeToggle />
        </div>
        <Button
          variant="outline"
          onClick={() => void logout().then(() => navigate("/owner/login"))}
        >
          Sign out
        </Button>
      </div>
    </div>
  )
}
