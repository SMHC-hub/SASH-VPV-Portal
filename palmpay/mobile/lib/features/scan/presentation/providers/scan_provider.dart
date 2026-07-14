import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/scan_repository.dart';
import '../../domain/scan_models.dart';
import '../../../../core/network/network_exceptions.dart';

class ScanState {
  const ScanState({
    this.merchants = const [],
    this.loadingMerchants = false,
    this.polling = false,
    this.errorMessage,
  });

  final List<PalmMerchant> merchants;
  final bool loadingMerchants;
  final bool polling;
  final String? errorMessage;

  ScanState copyWith({
    List<PalmMerchant>? merchants,
    bool? loadingMerchants,
    bool? polling,
    String? errorMessage,
  }) {
    return ScanState(
      merchants: merchants ?? this.merchants,
      loadingMerchants: loadingMerchants ?? this.loadingMerchants,
      polling: polling ?? this.polling,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

class ScanController extends Notifier<ScanState> {
  Timer? _pollTimer;

  @override
  ScanState build() {
    ref.onDispose(_stopPolling);
    Future.microtask(loadMerchants);
    return const ScanState();
  }

  ScanRepository get _repo => ref.read(scanRepositoryProvider);

  Future<void> loadMerchants() async {
    state = state.copyWith(
      loadingMerchants: true,
      errorMessage: null,
    );
    try {
      final merchants = await _repo.fetchMerchants();
      state = state.copyWith(merchants: merchants, loadingMerchants: false);
    } catch (e) {
      state = state.copyWith(
        loadingMerchants: false,
        errorMessage: userFacingError(e),
      );
    }
  }

  void startPolling(void Function(PalmPayNotification note) onNotification) {
    _stopPolling();
    state = state.copyWith(polling: true);
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) async {
      try {
        final notes = await _repo.fetchUnreadNotifications();
        for (final note in notes) {
          if (note.kind.startsWith('palm_pay')) {
            await _repo.markNotificationRead(note.id);
            onNotification(note);
          }
        }
      } catch (_) {}
    });
  }

  void stopPolling() => _stopPolling();

  void _stopPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
    if (state.polling) {
      state = state.copyWith(polling: false);
    }
  }
}

final scanControllerProvider = NotifierProvider<ScanController, ScanState>(ScanController.new);
