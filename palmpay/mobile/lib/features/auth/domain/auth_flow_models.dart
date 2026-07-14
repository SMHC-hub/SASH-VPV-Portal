class AccountCheckResult {
  const AccountCheckResult({
    required this.exists,
    required this.hasLoginPin,
    required this.onboardingComplete,
    required this.phoneMasked,
  });

  final bool exists;
  final bool hasLoginPin;
  final bool onboardingComplete;
  final String phoneMasked;

  factory AccountCheckResult.fromJson(Map<String, dynamic> json) {
    return AccountCheckResult(
      exists: json['exists'] as bool? ?? false,
      hasLoginPin: json['has_login_pin'] as bool? ?? false,
      onboardingComplete: json['onboarding_complete'] as bool? ?? false,
      phoneMasked: json['phone_masked'] as String? ?? '',
    );
  }
}

class SignupStartResult {
  const SignupStartResult({
    required this.phone,
    required this.email,
    this.devOtpPhone,
    this.devOtpEmail,
  });

  final String phone;
  final String email;
  final String? devOtpPhone;
  final String? devOtpEmail;

  factory SignupStartResult.fromJson(Map<String, dynamic> json) {
    return SignupStartResult(
      phone: json['phone'] as String? ?? '',
      email: json['email'] as String? ?? '',
      devOtpPhone: json['dev_otp_phone'] as String?,
      devOtpEmail: json['dev_otp_email'] as String?,
    );
  }
}

class PasswordResetStartResult {
  const PasswordResetStartResult({
    required this.email,
    this.devOtp,
  });

  final String email;
  final String? devOtp;

  factory PasswordResetStartResult.fromJson(Map<String, dynamic> json) {
    return PasswordResetStartResult(
      email: json['email'] as String? ?? '',
      devOtp: json['dev_otp'] as String?,
    );
  }
}
