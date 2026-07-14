import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_config.dart';
import '../../../core/network/dio_client.dart';
import '../domain/profile_models.dart';

class ProfileRepository {
  ProfileRepository(this._dio);

  final Dio _dio;

  Future<List<DeviceSession>> fetchDeviceSessions() async {
    final res = await _dio.get<List<dynamic>>(ApiConfig.authDevices);
    return (res.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(DeviceSession.fromJson)
        .toList();
  }

  Future<void> revokeDeviceSession(int sessionId) async {
    await _dio.delete<Map<String, dynamic>>('${ApiConfig.authDevices}/$sessionId');
  }

  Future<NotificationPreferences> fetchNotificationPreferences() async {
    final res = await _dio.get<Map<String, dynamic>>(ApiConfig.authNotificationPreferences);
    return NotificationPreferences.fromJson(res.data!);
  }

  Future<NotificationPreferences> updateNotificationPreferences({
    bool? transactionNotifications,
    bool? securityNotifications,
    bool? promoNotifications,
  }) async {
    final res = await _dio.put<Map<String, dynamic>>(
      ApiConfig.authNotificationPreferences,
      data: {
        if (transactionNotifications != null) 'transaction_notifications': transactionNotifications,
        if (securityNotifications != null) 'security_notifications': securityNotifications,
        if (promoNotifications != null) 'promo_notifications': promoNotifications,
      },
    );
    return NotificationPreferences.fromJson(res.data!);
  }
}

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository(ref.watch(dioProvider));
});
