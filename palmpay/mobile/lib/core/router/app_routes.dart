abstract final class AppRoutes {
  static const splash = '/splash';
  static const login = '/login';
  static const forgotPassword = '/forgot-password';
  static const resetPassword = '/reset-password';
  static const signupDetails = '/signup/details';
  static const signupVerifyPhone = '/signup/verify-phone';
  static const signupVerifyEmail = '/signup/verify-email';
  static const signupPin = '/signup/pin';
  static const kyc = '/kyc';
  static const setupSpendingPin = '/onboarding/payment-pin';
  static const palmEnroll = '/palm-enroll';
  static const enrollSuccess = '/enroll-success';
  static const home = '/home';
  static const scan = '/scan';
  static const analytics = '/analytics';
  static const profile = '/profile';
  static const addMoney = '/wallet/add-money';
  static const sendMoney = '/wallet/send';
  static const sendConfirm = '/wallet/send/confirm';
  static const transferSuccess = '/wallet/send/success';
  static const topUpSuccess = '/wallet/topup/success';
  static const notification = '/notification';
  static const transactions = '/transactions';
  static String transactionDetail(String reference) => '/transactions/$reference';
  static const scanResultSuccess = '/scan/result/success';
  static const scanResultFailed = '/scan/result/failed';
  static const scanResultLowBalance = '/scan/result/low-balance';

  // Legacy — kept for deep links during transition
  static const welcome = '/welcome';
  static const loginPhone = '/login/phone';
  static const loginPin = '/login/pin';
  static const loginOtp = '/login/otp';
  static const setLoginPin = '/login/set-pin';
  static const signupPhone = '/signup/phone';
  static const signupOtp = '/signup/otp';
  static const signupCreateAccount = '/signup/create-account';
  static const signupBiometric = '/signup/biometric';
  static const otp = '/otp';
}
