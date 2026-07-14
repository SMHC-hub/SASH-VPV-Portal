import 'package:flutter_riverpod/flutter_riverpod.dart';

/// `true` when the app can reach the API; `false` after connection failures.
class NetworkStatusNotifier extends StateNotifier<bool> {
  NetworkStatusNotifier() : super(true);

  void markOffline() {
    if (state) state = false;
  }

  void markOnline() {
    if (!state) state = true;
  }
}

final networkOnlineProvider =
    StateNotifierProvider<NetworkStatusNotifier, bool>((ref) => NetworkStatusNotifier());
