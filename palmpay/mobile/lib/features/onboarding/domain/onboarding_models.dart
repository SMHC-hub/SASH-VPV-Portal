class EnrollmentSession {
  const EnrollmentSession({
    required this.sessionCode,
    required this.qrPayload,
    required this.expiresAt,
    required this.message,
  });

  final String sessionCode;
  final String qrPayload;
  final String expiresAt;
  final String message;

  factory EnrollmentSession.fromJson(Map<String, dynamic> json) {
    return EnrollmentSession(
      sessionCode: json['session_code'] as String,
      qrPayload: json['qr_payload'] as String,
      expiresAt: json['expires_at'] as String? ?? '',
      message: json['message'] as String? ?? '',
    );
  }
}

class EnrollmentStatus {
  const EnrollmentStatus({
    required this.status,
    required this.palmEnrolled,
    this.sessionCode,
    required this.message,
  });

  final String status;
  final bool palmEnrolled;
  final String? sessionCode;
  final String message;

  factory EnrollmentStatus.fromJson(Map<String, dynamic> json) {
    return EnrollmentStatus(
      status: json['status'] as String? ?? 'not_started',
      palmEnrolled: json['palm_enrolled'] as bool? ?? false,
      sessionCode: json['session_code'] as String?,
      message: json['message'] as String? ?? '',
    );
  }
}

class KycStatus {
  const KycStatus({
    required this.status,
    this.cnicMasked,
    required this.fullName,
    required this.message,
  });

  final String status;
  final String? cnicMasked;
  final String fullName;
  final String message;

  factory KycStatus.fromJson(Map<String, dynamic> json) {
    return KycStatus(
      status: json['status'] as String? ?? 'pending',
      cnicMasked: json['cnic_masked'] as String?,
      fullName: json['full_name'] as String? ?? '',
      message: json['message'] as String? ?? '',
    );
  }
}
