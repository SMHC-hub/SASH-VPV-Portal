import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/auth_repository.dart';
import '../../domain/auth_session.dart';
import 'auth_provider.dart';

class OnboardingState {
  const OnboardingState({
    required this.loaded,
    this.profile,
    this.error,
  });

  final bool loaded;
  final WalletProfile? profile;
  final String? error;

  bool get needsKyc => profile != null && !profile!.kycApproved;

  bool get needsPalm =>
      profile != null && profile!.kycApproved && !profile!.palmEnrolled;

  bool get isFetchingProfile => !loaded;

  bool get isComplete => profile?.onboardingComplete ?? false;
}

class OnboardingController extends StateNotifier<OnboardingState> {
  OnboardingController(this._ref) : super(const OnboardingState(loaded: false));

  final Ref _ref;

  void _notifyRouter() {
    _ref.read(authRefreshListenableProvider).refresh();
    _ref.read(onboardingRefreshListenableProvider).refresh();
  }

  void markReadyWithoutProfile() {
    state = const OnboardingState(loaded: true);
    _notifyRouter();
  }

  void onAuthenticated() {
    state = OnboardingState(loaded: false, profile: state.profile);
    _notifyRouter();
  }

  Future<void> refresh() async {
    final auth = _ref.read(authControllerProvider);
    if (!auth.isAuthenticated) {
      markReadyWithoutProfile();
      return;
    }
    // Soft refresh when a profile is already known: keep loaded=true so the
    // router does not remount onboarding screens (KYC form, palm enroll, etc.).
    final existing = state.profile;
    if (existing == null) {
      state = const OnboardingState(loaded: false);
      _notifyRouter();
    }
    try {
      final profile = await _ref.read(authRepositoryProvider).fetchProfile();
      state = OnboardingState(loaded: true, profile: profile);
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        await _ref.read(authControllerProvider.notifier).logout();
        return;
      }
      state = OnboardingState(loaded: true, profile: existing, error: e.toString());
    } on Exception catch (e) {
      state = OnboardingState(loaded: true, profile: existing, error: e.toString());
    }
    _notifyRouter();
  }

  void reset() {
    state = const OnboardingState(loaded: false);
    _notifyRouter();
  }
}

final onboardingRefreshListenableProvider = Provider<OnboardingRefreshListenable>((ref) {
  return OnboardingRefreshListenable();
});

class OnboardingRefreshListenable extends ChangeNotifier {
  void refresh() => notifyListeners();
}

final onboardingControllerProvider =
    StateNotifierProvider<OnboardingController, OnboardingState>((ref) {
  final controller = OnboardingController(ref);
  ref.listen(authControllerProvider, (prev, next) {
    final authSettled = prev?.status == AuthStatus.unknown &&
        next.status != AuthStatus.unknown;

    if (authSettled && !next.isAuthenticated) {
      controller.markReadyWithoutProfile();
      return;
    }
    if (next.isAuthenticated && !(prev?.isAuthenticated ?? false)) {
      controller.onAuthenticated();
      controller.refresh();
    }
    if (!next.isAuthenticated && (prev?.isAuthenticated ?? false)) {
      controller.reset();
    }
  });
  final auth = ref.read(authControllerProvider);
  if (auth.status != AuthStatus.unknown) {
    if (auth.isAuthenticated) {
      Future.microtask(controller.refresh);
    } else {
      Future.microtask(controller.markReadyWithoutProfile);
    }
  }
  return controller;
});
