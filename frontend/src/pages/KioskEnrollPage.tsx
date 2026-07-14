import { useEffect, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { useMutation } from "@tanstack/react-query"
import { CheckCircle2, Loader2, QrCode } from "lucide-react"

import { PalmCapturePanel, type PalmSessionStatus } from "@/components/PalmCapturePanel"
import { PalmVeinLogo } from "@/components/PalmVeinLogo"
import { AuthLayout } from "@/components/AuthLayout"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { endpoints } from "@/lib/api"

type Step = "code" | "capture" | "done"

function parseApiError(err: unknown, fallback: string) {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === "string") return detail
  return fallback
}

export function KioskEnrollPage() {
  const [searchParams] = useSearchParams()
  const [step, setStep] = useState<Step>("code")
  const [code, setCode] = useState(() => (searchParams.get("code") || "").toUpperCase())
  const [firstHand, setFirstHand] = useState<"Left" | "Right">("Left")
  const [displayName, setDisplayName] = useState("")
  const [maskedContact, setMaskedContact] = useState<string | null>(null)
  const [registerSessionId, setRegisterSessionId] = useState("")
  const [sessionStatus, setSessionStatus] = useState<PalmSessionStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  const claim = useMutation({
    mutationFn: () => endpoints.kioskEnroll.claim(code.trim().toUpperCase(), firstHand),
    onSuccess: (data) => {
      setDisplayName(data.display_name)
      setMaskedContact(data.masked_phone || data.masked_email || null)
      setRegisterSessionId(data.register_session_id)
      setSessionStatus({
        register_session_id: data.register_session_id,
        full_name: data.display_name,
        email: data.masked_email || "",
        dataset_name: data.display_name,
        folder_id: "",
        current_hand: firstHand,
        left_captured: 0,
        right_captured: 0,
        target_per_hand: 10,
        left_complete: false,
        right_complete: false,
        both_complete: false,
        last_error: null,
      })
      setStep("capture")
      setError(null)
    },
    onError: (err) => setError(parseApiError(err, "Could not find this enrollment code")),
  })

  const switchHand = useMutation({
    mutationFn: (next: "Left" | "Right") =>
      endpoints.auth.registerSwitchHand(registerSessionId, next),
    onSuccess: (data) => setSessionStatus(data),
  })

  const finish = useMutation({
    mutationFn: () => endpoints.kioskEnroll.finish(code.trim().toUpperCase(), registerSessionId),
    onSuccess: () => {
      setStep("done")
      setError(null)
    },
    onError: (err) => setError(parseApiError(err, "Could not finish enrollment")),
  })

  useEffect(() => {
    const q = searchParams.get("code")
    if (q && q.length >= 6 && step === "code" && !claim.isPending && !claim.isSuccess) {
      setCode(q.toUpperCase())
    }
  }, [searchParams, step, claim.isPending, claim.isSuccess])

  useEffect(() => {
    if (sessionStatus?.both_complete && step === "capture" && !finish.isPending && !finish.isSuccess) {
      finish.mutate()
    }
  }, [sessionStatus?.both_complete, step, finish])

  return (
    <AuthLayout themePortal="employee" className="flex-col">
      <header className="flex items-center justify-between px-6 py-5 sm:px-8">
        <PalmVeinLogo variant="header" size={28} />
        <div className="flex gap-2">
          <Button variant="outline" className="border-white/15" asChild>
            <Link to="/kiosk">Palm login</Link>
          </Button>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pb-10 sm:px-6">
        <div className="mb-6">
          <p className="text-xs uppercase tracking-wider text-brand-muted">VeinPay kiosk</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">Mobile palm enrollment</h1>
          <p className="mt-2 max-w-2xl text-sm text-[var(--muted-foreground)]">
            Enter the code from the VeinPay mobile app (or open the QR link). Capture both palms
            here — the phone updates automatically when finished.
          </p>
        </div>

        {error ? (
          <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        {step === "code" ? (
          <div className="glass-panel max-w-lg space-y-4 p-6">
            <div className="space-y-2">
              <Label htmlFor="enroll-code">Enrollment code</Label>
              <Input
                id="enroll-code"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase().replace(/[^A-F0-9]/gi, ""))}
                placeholder="e.g. A1B2C3D4"
                className="font-mono text-lg tracking-widest"
                maxLength={12}
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label>Start with hand</Label>
              <div className="flex gap-2">
                {(["Left", "Right"] as const).map((h) => (
                  <Button
                    key={h}
                    type="button"
                    variant={firstHand === h ? "default" : "outline"}
                    className={firstHand === h ? "btn-brand" : "border-white/15"}
                    onClick={() => setFirstHand(h)}
                  >
                    {h}
                  </Button>
                ))}
              </div>
            </div>
            <Button
              className="btn-brand h-12 w-full"
              disabled={code.trim().length < 6 || claim.isPending}
              onClick={() => claim.mutate()}
            >
              {claim.isPending ? <Loader2 className="size-4 animate-spin" /> : <QrCode className="size-4" />}
              Look up &amp; start capture
            </Button>
            <p className="text-xs text-[var(--muted-foreground)]">
              QR scanning on this page can be added later — paste or type the 8-character code from
              the phone for now.
            </p>
          </div>
        ) : null}

        {step === "capture" && sessionStatus ? (
          <div className="space-y-4">
            <div className="glass-panel p-4">
              <p className="text-sm text-[var(--muted-foreground)]">Enrolling</p>
              <p className="text-xl font-semibold">{displayName}</p>
              {maskedContact ? (
                <p className="text-xs text-[var(--muted-foreground)]">{maskedContact}</p>
              ) : null}
              <p className="mt-1 font-mono text-sm tracking-wider text-brand-muted">Code {code}</p>
            </div>
            <PalmCapturePanel
              registerSessionId={registerSessionId}
              sessionStatus={sessionStatus}
              onStatusChange={setSessionStatus}
              onSwitchHand={(h) => switchHand.mutate(h)}
              switchHandPending={switchHand.isPending}
            />
            {finish.isPending ? (
              <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
                <Loader2 className="size-4 animate-spin" />
                Saving templates and notifying mobile…
              </div>
            ) : null}
          </div>
        ) : null}

        {step === "done" ? (
          <div className="glass-panel max-w-lg space-y-4 p-8 text-center">
            <CheckCircle2 className="mx-auto size-12 text-emerald-400" />
            <h2 className="text-2xl font-bold">Enrollment complete</h2>
            <p className="text-sm text-[var(--muted-foreground)]">
              Palm templates for <strong>{displayName}</strong> are saved. The mobile app should
              leave the waiting screen within a few seconds.
            </p>
            <Button
              className="btn-brand"
              onClick={() => {
                setStep("code")
                setCode("")
                setRegisterSessionId("")
                setSessionStatus(null)
                setDisplayName("")
                finish.reset()
                claim.reset()
              }}
            >
              Enroll another user
            </Button>
          </div>
        ) : null}
      </main>
    </AuthLayout>
  )
}
