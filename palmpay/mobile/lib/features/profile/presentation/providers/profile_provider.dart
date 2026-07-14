import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/network_exceptions.dart';
import '../../data/profile_repository.dart';
import '../../domain/profile_models.dart';

class ProfileSettingsState {
  const ProfileSettingsState({
    this.sessions = const [],
    this.notifications,
    this.loading = false,
    this.error,
  });

  final List<DeviceSession> sessions;
  final NotificationPreferences? notifications;
  final bool loading;
  final String? error;

  ProfileSettingsState copyWith({
    List<DeviceSession>? sessions,
    NotificationPreferences? notifications,
    bool? loading,
    String? error,
  }) {
    return ProfileSettingsState(
      sessions: sessions ?? this.sessions,
      notifications: notifications ?? this.notifications,
      loading: loading ?? this.loading,
      error: error,
    );
  }
}

class ProfileSettingsController extends StateNotifier<ProfileSettingsState> {
  ProfileSettingsController(this._repo) : super(const ProfileSettingsState());

  final ProfileRepository _repo;

  Future<void> refresh() async {
    state = state.copyWith(loading: true, error: null);
    try {
      final sessions = await _repo.fetchDeviceSessions();
      final notifications = await _repo.fetchNotificationPreferences();
      state = state.copyWith(
        sessions: sessions,
        notifications: notifications,
        loading: false,
        error: null,
      );
    } catch (e) {
      state = state.copyWith(loading: false, error: userFacingError(e));
    }
  }

  Future<void> revokeSession(int sessionId) async {
    await _repo.revokeDeviceSession(sessionId);
    await refresh();
  }

  Future<void> updateNotificationPreferences({
    bool? transactionNotifications,
    bool? securityNotifications,
    bool? promoNotifications,
  }) async {
    final prefs = await _repo.updateNotificationPreferences(
      transactionNotifications: transactionNotifications,
      securityNotifications: securityNotifications,
      promoNotifications: promoNotifications,
    );
    state = state.copyWith(notifications: prefs, error: null);
  }
}

final profileSettingsProvider =
    StateNotifierProvider<ProfileSettingsController, ProfileSettingsState>((ref) {
  return ProfileSettingsController(ref.watch(profileRepositoryProvider));
});
