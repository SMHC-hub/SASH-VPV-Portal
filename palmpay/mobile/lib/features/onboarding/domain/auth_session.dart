class AuthSession {
  const AuthSession({
    required this.accessToken,
    required this.refreshToken,
    required this.accountId,
    required this.phone,
    required this.email,
    required this.fullName,
    required this.walletAccountNumber,
    required this.balancePkr,
    this.needsLoginPinSetup = false,
  });

  final String accessToken;
  final String refreshToken;
  final int accountId;
  final String phone;
  final String email;
  final String fullName;
  final String walletAccountNumber;
  final double balancePkr;
  final bool needsLoginPinSetup;

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      accountId: json['account_id'] as int,
      phone: json['phone'] as String,
      email: json['email'] as String? ?? '',
      fullName: json['full_name'] as String? ?? '',
      walletAccountNumber: json['wallet_account_number'] as String? ?? '',
      balancePkr: (json['balance_pkr'] as num?)?.toDouble() ?? 0,
      needsLoginPinSetup: json['needs_login_pin_setup'] as bool? ?? false,
    );
  }
}

class WalletProfile {
  const WalletProfile({
    required this.walletId,
    required this.balancePkr,
    required this.kycStatus,
    required this.palmEnrolled,
    required this.fullName,
    required this.phone,
  });

  final String? walletId;
  final double balancePkr;
  final String kycStatus;
  final bool palmEnrolled;
  final String fullName;
  final String phone;

  factory WalletProfile.fromJson(Map<String, dynamic> json) {
    return WalletProfile(
      walletId: json['wallet_id'] as String?,
      balancePkr: (json['balance_pkr'] as num?)?.toDouble() ?? 0,
      kycStatus: json['kyc_status'] as String? ?? 'pending',
      palmEnrolled: json['palm_enrolled'] as bool? ?? false,
      fullName: json['full_name'] as String? ?? '',
      phone: json['phone'] as String? ?? '',
    );
  }

  bool get kycApproved => kycStatus == 'approved';
  bool get onboardingComplete => kycApproved && palmEnrolled;
}
