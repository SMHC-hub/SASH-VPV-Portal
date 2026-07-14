import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/constants/veinpay_brand.dart';
import '../../../../core/services/biometric_service.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../auth/domain/auth_flow_models.dart';
import '../../../auth/presentation/providers/signup_draft_provider.dart';
import '../../data/auth_repository.dart';
import '../../domain/auth_session.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

enum BiometricLoginResult {
  success,
  cancelled,
  notConfigured,
  sessionExpired,
}

class AuthState {
  const AuthState({
    required this.status,
    this.session,
    this.error,
  });

  final AuthStatus status;
  final AuthSession? session;
  final String? error;

  bool get isAuthenticated => status == AuthStatus.authenticated && session != null;

  AuthState copyWith({
    AuthStatus? status,
    AuthSession? session,
    String? error,
  }) {
    return AuthState(
      status: status ?? this.status,
      session: session ?? this.session,
      error: error,
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._ref) : super(const AuthState(status: AuthStatus.unknown)) {
    _bootstrap();
  }

  final Ref _ref;

  AuthRepository get _repo => _ref.read(authRepositoryProvider);
  SecureStorageService get _storage => _ref.read(secureStorageProvider);

  Future<void> _bootstrap() async {
    // Always land on login — no auto-navigation to OTP or home.
    state = const AuthState(status: AuthStatus.unauthenticated);
    _ref.read(authRefreshListenableProvider).refresh();
  }

  Future<void> _persistSession(AuthSession session) async {
    await _storage.saveTokens(
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      phone: session.phone,
      email: session.email,
    );
    state = AuthState(status: AuthStatus.authenticated, session: session);
    _ref.read(authRefreshListenableProvider).refresh();
  }

  Future<void> loginWithEmail({
    required String email,
    required String password,
  }) async {
    final session = await _repo.loginWithEmail(email: email, password: password);
    await _persistSession(session);
  }

  Future<PasswordResetStartResult> requestPasswordReset(String email) async {
    return _repo.requestPasswordReset(email);
  }

  Future<void> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    await _repo.resetPassword(email: email, otp: otp, newPassword: newPassword);
    await _storage.invalidateExpiredSession();
    state = const AuthState(status: AuthStatus.unauthenticated);
    _ref.read(authRefreshListenableProvider).refresh();
  }

  Future<SignupStartResult> startSignup({
    required String fullName,
    required String email,
    required String phone,
    required String password,
  }) async {
    final result = await _repo.signupStart(
      fullName: fullName,
      email: email,
      phone: phone,
      password: password,
    );
    _ref.read(signupDraftProvider.notifier).setDraft(
          SignupDraft(
            fullName: fullName,
            email: result.email,
            phone: result.phone,
            devOtpPhone: result.devOtpPhone,
            devOtpEmail: result.devOtpEmail,
          ),
        );
    return result;
  }

  Future<void> verifyPhoneSignup({required String phone, required String otp}) async {
    await _repo.verifyPhoneSignup(phone: phone, otp: otp);
    _ref.read(signupDraftProvider.notifier).markPhoneVerified();
  }

  Future<void> verifyEmailSignup({required String email, required String otp}) async {
    await _repo.verifyEmailSignup(email: email, otp: otp);
    _ref.read(signupDraftProvider.notifier).markEmailVerified();
  }

  Future<void> finishSignup({required String loginPin}) async {
    final draft = _ref.read(signupDraftProvider);
    if (draft == null) throw StateError('Signup session missing');
    await _repo.finishSignup(
      phone: draft.phone,
      email: draft.email,
      loginPin: loginPin,
    );
    _ref.read(signupDraftProvider.notifier).clear();
  }

  Future<BiometricLoginResult> tryBiometricLogin() async {
    if (!await canUseBiometricLogin()) {
      return BiometricLoginResult.notConfigured;
    }

    final bio = _ref.read(biometricServiceProvider);
    final ok = await bio.authenticate(reason: 'Unlock ${VeinPayBrand.appName}');
    if (!ok) return BiometricLoginResult.cancelled;

    final refresh = await _storage.readRefreshToken();
    if (refresh == null) {
      await _storage.clearBiometricUnlock();
      return BiometricLoginResult.notConfigured;
    }

    try {
      final session = await _repo.refresh(refresh);
      await _persistSession(session);
      return BiometricLoginResult.success;
    } on DioException {
      await _storage.clearBiometricUnlock();
      return BiometricLoginResult.sessionExpired;
    } on Exception {
      await _storage.clearBiometricUnlock();
      return BiometricLoginResult.sessionExpired;
    }
  }

  /// True when fingerprint login is enabled and a refresh token is stored.
  Future<bool> canUseBiometricLogin() async {
    if (!await _storage.isBiometricEnabled()) return false;
    final refresh = await _storage.readRefreshToken();
    return refresh != null && refresh.isNotEmpty;
  }

  Future<bool> setBiometricEnabled(bool enabled) async {
    if (enabled) {
      final available = await isBiometricAvailable();
      if (!available) return false;

      final refresh = await _storage.readRefreshToken();
      if (refresh == null) return false;

      final bio = _ref.read(biometricServiceProvider);
      final ok = await bio.authenticate(reason: 'Enable fingerprint login for ${VeinPayBrand.appName}');
      if (!ok) return false;
    }

    await _storage.setBiometricEnabled(enabled);
    return true;
  }

  Future<bool> isBiometricAvailable() async {
    return _ref.read(biometricServiceProvider).isAvailable();
  }

  Future<bool> isBiometricEnabled() async {
    return _storage.isBiometricEnabled();
  }

  Future<bool> refreshSession() async {
    final refresh = await _storage.readRefreshToken();
    if (refresh == null) {
      await _invalidateSession();
      return false;
    }
    try {
      final session = await _repo.refresh(refresh);
      await _persistSession(session);
      return true;
    } on Exception {
      await _invalidateSession();
      return false;
    }
  }

  /// Drops stale tokens without keeping biometric unlock (refresh may already be revoked).
  Future<void> _invalidateSession() async {
    await _storage.invalidateExpiredSession();
    state = const AuthState(status: AuthStatus.unauthenticated);
    _ref.read(authRefreshListenableProvider).refresh();
  }

  /// Called by the Dio interceptor when refresh fails (avoids keeping a revoked token).
  Future<void> invalidateSessionFromInterceptor() async {
    if (state.status == AuthStatus.unauthenticated) return;
    await _invalidateSession();
  }

  Future<void> logout() async {
    final keepBio = await _storage.isBiometricEnabled();
    await _storage.clearSession(keepBiometricUnlock: keepBio);
    state = const AuthState(status: AuthStatus.unauthenticated);
    _ref.read(authRefreshListenableProvider).refresh();
  }
}

final authRefreshListenableProvider = Provider<AuthRefreshListenable>((ref) {
  return AuthRefreshListenable();
});

class AuthRefreshListenable extends ChangeNotifier {
  void refresh() => notifyListeners();
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(ref);
});
