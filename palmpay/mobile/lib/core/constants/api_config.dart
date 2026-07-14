/// API base URL for the standalone VeinPay backend (port 8001).
///
/// Override at run time:
///   flutter run --dart-define=API_HOST=192.168.1.42
/// Production (Oracle + Nginx + TLS):
///   --dart-define=API_HOST=api.yourname.duckdns.org --dart-define=API_HTTPS=true --dart-define=API_PORT=443
///
/// Defaults:
/// - `10.0.2.2` — Android emulator → host machine
/// - Use your PC's LAN IP on a physical phone
abstract final class ApiConfig {
  static const _rawHost = String.fromEnvironment('API_HOST', defaultValue: '10.0.2.2');
  static const _rawPort = String.fromEnvironment('API_PORT', defaultValue: '8001');
  static const _useHttps = bool.fromEnvironment('API_HTTPS', defaultValue: false);

  /// Strips accidental trailing slashes from `--dart-define=API_HOST=...`.
  static String get host => _rawHost.replaceAll(RegExp(r'[\\/]+$'), '').trim();

  static String get port => _rawPort.trim();

  static String get baseUrl {
    final scheme = _useHttps ? 'https' : 'http';
    if (_useHttps && port == '443') return '$scheme://$host';
    return '$scheme://$host:$port';
  }

  static const health = '/api/health';
  static const palmpayHealth = '/api/palmpay/health';
  static const palmpayProfile = '/api/palmpay/profile';
  static const publicStats = '/api/public/stats';
  static const authRegisterPhone = '/api/palmpay/auth/register/phone';
  static const authLoginEmail = '/api/palmpay/auth/login/email';
  static const authForgotPassword = '/api/palmpay/auth/password/forgot';
  static const authResetPassword = '/api/palmpay/auth/password/reset';
  static const authSignupStart = '/api/palmpay/auth/register/signup-start';
  static const authSignupVerifyPhone = '/api/palmpay/auth/register/verify-phone-signup';
  static const authSignupVerifyEmail = '/api/palmpay/auth/register/verify-email-signup';
  static const authSignupFinish = '/api/palmpay/auth/register/finish-signup';
  static const authVerifyOtp = '/api/palmpay/auth/register/verify-otp';
  static const authConfirmOtpSignup = '/api/palmpay/auth/register/confirm-otp';
  static const authCompleteSignup = '/api/palmpay/auth/register/complete-signup';
  static const authAccountCheck = '/api/palmpay/auth/account/check';
  static const authLoginPin = '/api/palmpay/auth/login/pin';
  static const authSetLoginPin = '/api/palmpay/auth/pin/set';
  static const authResetLoginPin = '/api/palmpay/auth/pin/reset';
  static const authRefresh = '/api/palmpay/auth/token/refresh';
  static const authDevices = '/api/palmpay/auth/devices';
  static const authNotificationPreferences = '/api/palmpay/auth/notifications/preferences';
  static const kycStatus = '/api/palmpay/kyc/status';
  static const kycSubmit = '/api/palmpay/kyc/submit';
  static const palmEnrollInitiate = '/api/palmpay/palm/enrollment/initiate';
  static const palmEnrollStatus = '/api/palmpay/palm/enrollment/status';
  static const kioskEnrollComplete = '/api/palmpay/kiosk/enrollment/complete';
  static const wallet = '/api/palmpay/wallet';
  static const walletLimits = '/api/palmpay/wallet/limits';
  static const walletSettings = '/api/palmpay/wallet/settings';
  static const walletTransactions = '/api/palmpay/wallet/transactions';
  static const transactions = '/api/palmpay/transactions';
  static String transactionDetail(String reference) => '/api/palmpay/transactions/$reference';
  static const analyticsSummary = '/api/palmpay/analytics/summary';
  static const topupInitiate = '/api/palmpay/topup/jazzcash/initiate';
  static const topupSimulateExisting = '/api/palmpay/topup/jazzcash/simulate-existing';
  static const transferLookup = '/api/palmpay/transfer/lookup';
  static const transferInitiate = '/api/palmpay/transfer/initiate';
  static const transferConfirm = '/api/palmpay/transfer/confirm';
  static const paymentMerchants = '/api/palmpay/payment/merchants';
  static const notificationsUnread = '/api/palmpay/notifications/unread';
  static String notificationRead(int id) => '/api/palmpay/notifications/$id/read';
}
