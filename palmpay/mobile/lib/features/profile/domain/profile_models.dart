class DeviceSession {
  const DeviceSession({
    required this.id,
    required this.deviceName,
    required this.createdAt,
    required this.expiresAt,
    required this.status,
  });

  final int id;
  final String deviceName;
  final String createdAt;
  final String expiresAt;
  final String status;

  bool get isActive => status == 'active';

  factory DeviceSession.fromJson(Map<String, dynamic> json) {
    return DeviceSession(
      id: json['id'] as int? ?? 0,
      deviceName: json['device_name'] as String? ?? 'VeinPay session',
      createdAt: json['created_at'] as String? ?? '',
      expiresAt: json['expires_at'] as String? ?? '',
      status: json['status'] as String? ?? 'expired',
    );
  }
}

class NotificationPreferences {
  const NotificationPreferences({
    required this.transactionNotifications,
    required this.securityNotifications,
    required this.promoNotifications,
  });

  final bool transactionNotifications;
  final bool securityNotifications;
  final bool promoNotifications;

  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    return NotificationPreferences(
      transactionNotifications: json['transaction_notifications'] as bool? ?? true,
      securityNotifications: json['security_notifications'] as bool? ?? true,
      promoNotifications: json['promo_notifications'] as bool? ?? false,
    );
  }
}
