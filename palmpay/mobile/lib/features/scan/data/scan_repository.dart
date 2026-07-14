import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_config.dart';
import '../../../core/network/dio_client.dart';
import '../domain/scan_models.dart';

class ScanRepository {
  ScanRepository(this._dio);

  final Dio _dio;

  Future<List<PalmMerchant>> fetchMerchants() async {
    final res = await _dio.get<List<dynamic>>(ApiConfig.paymentMerchants);
    return (res.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(PalmMerchant.fromJson)
        .toList();
  }

  Future<List<PalmPayNotification>> fetchUnreadNotifications() async {
    final res = await _dio.get<List<dynamic>>(ApiConfig.notificationsUnread);
    return (res.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(PalmPayNotification.fromJson)
        .toList();
  }

  Future<void> markNotificationRead(int id) async {
    await _dio.post<void>(ApiConfig.notificationRead(id));
  }
}

final scanRepositoryProvider = Provider<ScanRepository>((ref) {
  return ScanRepository(ref.watch(dioProvider));
});
