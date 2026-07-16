import { useEffect, useState } from "react"

import { Link, useLocation, useNavigate } from "react-router-dom"

import { useMutation, useQuery } from "@tanstack/react-query"

import { Camera, Loader2 } from "lucide-react"

import { EmailVerifyPanel, ForgotPasswordPanel } from "@/components/auth/AuthEmailPanels"
import { AuthMethodTabs, AuthScanPanels } from "@/components/auth/AuthScanPanels"
import { AuthLayout } from "@/components/AuthLayout"
import { GoogleSignInButton } from "@/components/auth/GoogleSignInButton"
import { PalmVeinLogo } from "@/components/PalmVeinLogo"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { endpoints } from "@/lib/api"
import { mergeCartAfterLogin } from "@/lib/shopUtils"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/useAuthStore"

type AuthMode = "login" | "signup"
type SignupStep = "details" | "verify"
type LoginSubview = "default" | "forgot" | "verify"

function parseApiError(err: unknown, fallback: string) {
  const ax = err as {
    response?: { data?: { detail?: unknown }; status?: number }
    message?: string
    code?: string
  }
  const detail = ax?.response?.data?.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string }
    if (typeof first?.msg === "string") return first.msg
  }
  if (ax?.response?.status === 409) return typeof detail === "string" ? detail : "Account already exists"
  if (!ax?.response) {
    const msg = ax?.message ?? ""
    if (ax?.code === "ECONNABORTED" || /timeout/i.test(msg)) {
      return "Request timed out — try again"
    }
    if (/Network/i.test(msg)) return "Cannot reach server — is the backend running on port 8001?"
    return fallback
  }
  return fallback
}

function applyGoogleAuth(
  data: {
    status: string
    access_token?: string | null
    account_id?: number | null
    email?: string | null
    full_name?: string | null
    dataset_id?: string | null
    dataset_name?: string | null
    role?: string | null
    session_id?: number | null
    message?: string | null
  },
  setAuth: ReturnType<typeof useAuthStore.getState>["setAuth"],
  navigate: ReturnType<typeof useNavigate>,
  onError: (msg: string) => void,
  redirectTo: string,
) {
  if (data.status === "authenticated" && data.access_token) {
    setAuth(data.access_token, {
      account_id: data.account_id!,
      email: data.email!,
      full_name: data.full_name!,
      dataset_id: data.dataset_id ?? "",
      dataset_name: data.dataset_name!,
      role: data.role ?? "customer",
      session_id: data.session_id ?? null,
    })
    void mergeCartAfterLogin()
    navigate(redirectTo)
    return
  }
  onError(data.message ?? "Google sign-in failed")
}

const USERNAME_RE = /^[a-zA-Z0-9_]{3,32}$/

export function MemberAuthPage({ initialMode }: { initialMode: AuthMode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [mode, setMode] = useState<AuthMode>(initialMode)
  const [signupStep, setSignupStep] = useState<SignupStep>("details")
  const [authNotice, setAuthNotice] = useState<string | null>(null)

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loginMethod, setLoginMethod] = useState<"palm" | "email">("email")
  const [loginSubview, setLoginSubview] = useState<LoginSubview>("default")
  const [lastProbeUrl, setLastProbeUrl] = useState<string | null>(null)
  const [loginError, setLoginError] = useState<string | null>(null)
  const [debouncedEmail, setDebouncedEmail] = useState("")

  const [username, setUsername] = useState("")
  const [signupEmail, setSignupEmail] = useState("")
  const [signupPassword, setSignupPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [captchaAnswer, setCaptchaAnswer] = useState("")
  const [emailSent, setEmailSent] = useState(true)
  const [signupDevCode, setSignupDevCode] = useState<string | null>(null)
  const [signupError, setSignupError] = useState<string | null>(null)

  const postAuthPath = () => {
    const from = (location.state as { from?: string } | null)?.from
    if (typeof from === "string" && from.startsWith("/") && !from.startsWith("/user/")) {
      return from
    }
    return "/"
  }

  const handleAuthSuccess = (accessToken: string, user: {
    account_id: number
    email: string
    full_name: string
    dataset_id: string
    dataset_name: string
    role?: string
    session_id?: number | null
  }) => {
    setAuth(accessToken, { ...user, role: user.role ?? "customer" })
    void mergeCartAfterLogin()
    navigate(postAuthPath())
  }

  const captcha = useQuery({ queryKey: ["captcha"], queryFn: endpoints.auth.captcha })

  useEffect(() => {
    setMode(initialMode)
  }, [initialMode])

  useEffect(() => {
    const state = location.state as { notice?: string; email?: string; from?: string } | null
    const notice = state?.notice
    const from = state?.from
    if (typeof notice === "string" && notice.trim()) {
      setAuthNotice(notice.trim())
    }
    if (typeof state?.email === "string" && state.email.includes("@")) {
      setEmail(state.email)
    }
    if (notice || state?.email) {
      navigate(location.pathname, {
        replace: true,
        state: from ? { from } : {},
      })
    }
  }, [location.state, location.pathname, navigate])

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedEmail(email.trim().toLowerCase()), 400)
    return () => window.clearTimeout(t)
  }, [email])

  const signInOptions = useQuery({
    queryKey: ["customer-sign-in-options", debouncedEmail],
    queryFn: () => endpoints.auth.customerSignInOptions(debouncedEmail),
    enabled: debouncedEmail.includes("@") && debouncedEmail.length > 5,
  })

  const palmsEnrolled = Boolean(signInOptions.data?.palms_enrolled)

  useEffect(() => {
    if (!palmsEnrolled && loginMethod === "palm") {
      setLoginMethod("email")
    }
  }, [palmsEnrolled, loginMethod])

  const goLogin = () => {
    if (mode === "login") return
    setMode("login")
    const from = (location.state as { from?: string } | null)?.from
    navigate("/user/login", { replace: true, state: from ? { from } : {} })
  }

  const goSignup = () => {
    if (mode === "signup" && signupStep === "details") return
    if (signupStep !== "details") return
    setMode("signup")
    const from = (location.state as { from?: string } | null)?.from
    navigate("/user/signup", { replace: true, state: from ? { from } : {} })
  }

  const passwordLogin = useMutation({
    mutationFn: () => endpoints.auth.loginCustomer(email, password),
    onSuccess: (data) => {
      handleAuthSuccess(data.access_token, { ...data.user, role: data.user.role ?? "customer" })
    },
    onError: (err) => {
      const msg = parseApiError(err, "Invalid email or password")
      setLoginError(msg)
      if (msg.toLowerCase().includes("not verified")) {
        setLoginSubview("verify")
      }
    },
  })

  const palmLogin = useMutation({
    mutationFn: endpoints.auth.loginCustomerPalm,
    onSuccess: (data) => {
      if (data.probe_image_url) {
        setLastProbeUrl(`${data.probe_image_url}&t=${Date.now()}`)
      }
      if (!data.matched || !data.access_token) {
        setLoginError(data.message ?? "Palm not recognized")
        return
      }
      handleAuthSuccess(data.access_token, {
        account_id: data.account_id!,
        email: data.email!,
        full_name: data.full_name!,
        dataset_id: data.dataset_id ?? "",
        dataset_name: data.dataset_name!,
        role: data.role ?? "customer",
        session_id: data.session_id ?? null,
      })
    },
    onError: () => setLoginError("Palm login failed"),
  })

  const googleLogin = useMutation({
    mutationFn: (credential: string) => endpoints.auth.googleAuth(credential, "login"),
    onSuccess: (data) => {
      applyGoogleAuth(data, setAuth, navigate, setLoginError, postAuthPath())
    },
    onError: (err) => setLoginError(parseApiError(err, "Google sign-in failed")),
  })

  const startRegister = useMutation({
    mutationFn: () =>
      endpoints.auth.registerCustomerStart({
        username: username.trim(),
        email: signupEmail.trim(),
        password: signupPassword,
        confirm_password: confirmPassword,
        captcha_id: captcha.data!.captcha_id,
        captcha_answer: Number(captchaAnswer),
      }),
    onSuccess: (data) => {
      setEmailSent(data.email_sent)
      setSignupDevCode(data.dev_code ?? null)
      setSignupStep("verify")
      setSignupError(null)
      setCaptchaAnswer("")
      void captcha.refetch()
    },
    onError: (err) => {
      setSignupError(parseApiError(err, "Registration failed"))
      setCaptchaAnswer("")
      void captcha.refetch()
    },
  })

  const inVerification = signupStep === "verify" && mode === "signup"

  const googleSignup = useMutation({
    mutationFn: (credential: string) => endpoints.auth.googleAuth(credential, "signup"),
    onSuccess: (data) => {
      if (data.status === "authenticated" && data.access_token) {
        setSignupError(null)
        applyGoogleAuth(data, setAuth, navigate, setSignupError, postAuthPath())
        return
      }
      if (data.status === "registered" || data.email) {
        setSignupError(null)
        const from = (location.state as { from?: string } | null)?.from
        navigate("/user/login", {
          replace: true,
          state: {
            notice:
              data.account_created === false
                ? "Account already exists. Sign in with Google."
                : data.message || "Google account created. Sign in with Google to continue.",
            email: data.email ?? undefined,
            ...(from ? { from } : {}),
          },
        })
        return
      }
      setSignupError(data.message ?? "Google sign-up failed")
    },
    onError: (err) =>
      setSignupError(parseApiError(err, "Google sign-up timed out — check internet and try again")),
  })

  const panelWidth =
    mode === "login" && loginMethod === "palm" && palmsEnrolled ? "max-w-2xl" : "max-w-md"

  const signupCanSubmit =
    USERNAME_RE.test(username.trim()) &&
    signupEmail.trim() &&
    signupPassword.length >= 8 &&
    signupPassword === confirmPassword &&
    captchaAnswer.trim()

  return (
    <AuthLayout themePortal="customer">
      <div className={cn("glass-panel w-full p-8", panelWidth)}>
        <div className="mb-4 flex justify-center">
          <PalmVeinLogo variant="full" size={72} subtitle="Member portal" />
        </div>

        {authNotice && mode === "login" && loginSubview === "default" ? (
          <div className="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
            {authNotice}
          </div>
        ) : null}

        {!inVerification && loginSubview === "default" && (
          <div className="mb-6 flex rounded-lg border border-[var(--border)] bg-[color-mix(in_srgb,var(--accent)_40%,transparent)] p-1">
            <button
              type="button"
              onClick={goLogin}
              className={cn(
                "flex-1 rounded-md py-2.5 text-sm font-semibold transition-all duration-300",
                mode === "login"
                  ? "btn-brand shadow-sm"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]",
              )}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={goSignup}
              className={cn(
                "flex-1 rounded-md py-2.5 text-sm font-semibold transition-all duration-300",
                mode === "signup"
                  ? "btn-brand shadow-sm"
                  : "text-[var(--muted-foreground)] hover:text-[var(--foreground)]",
              )}
            >
              Sign up
            </button>
          </div>
        )}

        {!inVerification && mode === "login" && loginSubview === "forgot" && (
          <ForgotPasswordPanel
            defaultEmail={email}
            onBack={() => setLoginSubview("default")}
          />
        )}

        {!inVerification && mode === "login" && loginSubview === "verify" && (
          <EmailVerifyPanel
            email={email}
            onVerified={(data) => handleAuthSuccess(data.access_token, data.user)}
            onBack={() => setLoginSubview("default")}
          />
        )}

        {!inVerification && (mode === "signup" || loginSubview === "default") ? (
          <div className="member-auth-slider overflow-hidden">
            <div
              className={cn(
                "member-auth-track flex w-[200%]",
                mode === "signup" ? "is-signup" : "is-login",
              )}
            >
              <div className="w-1/2 shrink-0 pr-1">
                <h1 className="mb-1 text-center text-xl font-bold">Member sign in</h1>
                <p className="mb-6 text-center text-sm text-[var(--muted-foreground)]">
                  Sign in with email, or palm if you have enrolled
                </p>

                <AuthMethodTabs
                  value={loginMethod}
                  onChange={setLoginMethod}
                  showPalm={palmsEnrolled}
                />

                {loginMethod === "email" || !palmsEnrolled ? (
                  <div className="space-y-4">
                    <GoogleSignInButton
                      intent="login"
                      disabled={googleLogin.isPending}
                      onCredential={(credential) => {
                        setLoginError(null)
                        googleLogin.mutate(credential)
                      }}
                    />
                    {googleLogin.isPending ? (
                      <div className="flex items-center justify-center gap-2 text-sm text-[var(--muted-foreground)]">
                        <Loader2 className="size-4 animate-spin" />
                        Signing in with Google…
                      </div>
                    ) : null}
                    <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                      <span className="h-px flex-1 bg-[var(--border)]" />
                      or email
                      <span className="h-px flex-1 bg-[var(--border)]" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="member-email">Email</Label>
                      <Input
                        id="member-email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@example.com"
                        autoComplete="email"
                      />
                      {signInOptions.data?.exists && !signInOptions.data.email_verified && (
                        <button
                          type="button"
                          className="text-xs text-amber-600 underline"
                          onClick={() => setLoginSubview("verify")}
                        >
                          Email not verified — enter your code
                        </button>
                      )}
                      {signInOptions.data?.exists && signInOptions.data.email_verified && !palmsEnrolled && (
                        <p className="text-xs text-[var(--muted-foreground)]">
                          Palm login unlocks after you enroll from the Enrollment tab.
                        </p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="member-password">Password</Label>
                      <Input
                        id="member-password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="current-password"
                      />
                    </div>
                    <div className="flex justify-end">
                      <button
                        type="button"
                        className="text-xs text-[var(--muted-foreground)] hover:text-[var(--primary)] hover:underline"
                        onClick={() => {
                          setLoginError(null)
                          setLoginSubview("forgot")
                        }}
                      >
                        Forgot password?
                      </button>
                    </div>
                    <Button
                      className="btn-brand w-full"
                      size="lg"
                      disabled={passwordLogin.isPending || !email || !password}
                      onClick={() => {
                        setLoginError(null)
                        passwordLogin.mutate()
                      }}
                    >
                      {passwordLogin.isPending ? (
                        <>
                          <Loader2 className="size-4 animate-spin" />
                          Signing in…
                        </>
                      ) : (
                        "Sign in"
                      )}
                    </Button>
                    {loginError && <p className="text-center text-sm text-red-500">{loginError}</p>}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <AuthScanPanels probeUrl={lastProbeUrl} />
                    <Button
                      className="btn-brand w-full"
                      size="lg"
                      disabled={palmLogin.isPending}
                      onClick={() => {
                        setLoginError(null)
                        palmLogin.mutate()
                      }}
                    >
                      {palmLogin.isPending ? (
                        <>
                          <Loader2 className="size-4 animate-spin" />
                          Scanning…
                        </>
                      ) : (
                        <>
                          <Camera className="size-4" />
                          Scan palm to sign in
                        </>
                      )}
                    </Button>
                    {loginError && <p className="text-center text-sm text-red-500">{loginError}</p>}
                  </div>
                )}
              </div>

              <div className="w-1/2 shrink-0 pl-1">
                <h1 className="mb-1 text-center text-xl font-bold">Create account</h1>
                <p className="mb-6 text-center text-sm text-[var(--muted-foreground)]">
                  Sign up with Google for instant access, or use email with 6-digit verification
                </p>
                <div className="space-y-4">
                  <GoogleSignInButton
                    intent="signup"
                    disabled={googleSignup.isPending}
                    onCredential={(credential) => {
                      setSignupError(null)
                      googleSignup.mutate(credential)
                    }}
                  />
                  {googleSignup.isPending ? (
                    <div className="flex items-center justify-center gap-2 text-sm text-[var(--muted-foreground)]">
                      <Loader2 className="size-4 animate-spin" />
                      Creating your account with Google…
                    </div>
                  ) : null}
                  <div className="flex items-center gap-3 text-xs uppercase tracking-wider text-[var(--muted-foreground)]">
                    <span className="h-px flex-1 bg-[var(--border)]" />
                    or email
                    <span className="h-px flex-1 bg-[var(--border)]" />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="member-username">Username</Label>
                    <Input
                      id="member-username"
                      value={username}
                      onChange={(e) =>
                        setUsername(e.target.value.replace(/[^a-zA-Z0-9_]/g, "").slice(0, 32))
                      }
                      placeholder="letters, numbers, underscore"
                      autoComplete="username"
                    />
                    {username.trim() && !USERNAME_RE.test(username.trim()) ? (
                      <p className="text-xs text-amber-400">Use 3–32 characters: letters, numbers, _</p>
                    ) : null}
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="member-signup-email">Email</Label>
                    <Input
                      id="member-signup-email"
                      type="email"
                      value={signupEmail}
                      onChange={(e) => setSignupEmail(e.target.value)}
                      autoComplete="email"
                    />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <Label>Password</Label>
                      <Input
                        type="password"
                        value={signupPassword}
                        onChange={(e) => setSignupPassword(e.target.value)}
                        autoComplete="new-password"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label>Confirm password</Label>
                      <Input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        autoComplete="new-password"
                      />
                    </div>
                  </div>
                  <div className="rounded-lg border border-[var(--border)] p-4">
                    <Label className="text-xs uppercase text-[var(--muted-foreground)]">
                      Are you human?
                    </Label>
                    <p className="mt-1 text-sm">{captcha.data?.question ?? "Loading…"}</p>
                    <Input
                      className="mt-2"
                      type="number"
                      value={captchaAnswer}
                      onChange={(e) => setCaptchaAnswer(e.target.value)}
                    />
                  </div>
                  <Button
                    className="btn-brand w-full"
                    disabled={!signupCanSubmit || startRegister.isPending}
                    onClick={() => {
                      setSignupError(null)
                      startRegister.mutate()
                    }}
                  >
                    {startRegister.isPending ? (
                      <>
                        <Loader2 className="size-4 animate-spin" />
                        Creating account…
                      </>
                    ) : (
                      "Create account"
                    )}
                  </Button>
                  {signupError && <p className="text-center text-sm text-red-500">{signupError}</p>}
                </div>
              </div>
            </div>
          </div>
        ) : inVerification ? (
          <EmailVerifyPanel
            email={signupEmail}
            emailSent={emailSent}
            initialDevCode={signupDevCode}
            onVerified={(data) => handleAuthSuccess(data.access_token, data.user)}
            onBack={() => {
              setSignupStep("details")
              setSignupDevCode(null)
              setSignupError(null)
              setCaptchaAnswer("")
              void captcha.refetch()
            }}
          />
        ) : null}

        {!inVerification && loginSubview === "default" && (
          <p className="mt-6 text-center text-xs text-[var(--muted-foreground)]">
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
            Shop owner?{" "}
            <Link to="/owner/login" className="hover:text-[var(--primary)] hover:underline">
              Shop owner sign in
            </Link>
          </p>
        )}
      </div>
    </AuthLayout>
  )
}
