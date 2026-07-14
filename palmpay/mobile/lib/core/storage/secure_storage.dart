import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

const _kAccess = 'palmpay_access_token';
const _kRefresh = 'palmpay_refresh_token';
const _kPhone = 'palmpay_phone';
const _kEmail = 'palmpay_email';
const _kBiometric = 'palmpay_biometric_enabled';

class SecureStorageService {
  SecureStorageService(this._storage);

  final FlutterSecureStorage _storage;

  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
    required String phone,
    String? email,
  }) async {
    await _storage.write(key: _kAccess, value: accessToken);
    await _storage.write(key: _kRefresh, value: refreshToken);
    await _storage.write(key: _kPhone, value: phone);
    if (email != null && email.isNotEmpty) {
      await _storage.write(key: _kEmail, value: email);
    }
  }

  Future<String?> readEmail() => _storage.read(key: _kEmail);

  Future<String?> readAccessToken() => _storage.read(key: _kAccess);

  Future<String?> readRefreshToken() => _storage.read(key: _kRefresh);

  Future<String?> readPhone() => _storage.read(key: _kPhone);

  Future<void> setBiometricEnabled(bool enabled) async {
    await _storage.write(key: _kBiometric, value: enabled ? '1' : '0');
  }

  Future<bool> isBiometricEnabled() async {
    final v = await _storage.read(key: _kBiometric);
    return v == '1';
  }

  /// Clears the active session. When [keepBiometricUnlock] is true, keeps refresh
  /// token, email, phone, and biometric flag so fingerprint login works after sign out.
  Future<void> clearSession({required bool keepBiometricUnlock}) async {
    await _storage.delete(key: _kAccess);
    if (!keepBiometricUnlock) {
      await _storage.delete(key: _kRefresh);
      await _storage.delete(key: _kPhone);
      await _storage.delete(key: _kEmail);
      await _storage.delete(key: _kBiometric);
    }
  }

  /// Removes stored refresh token and disables fingerprint unlock (e.g. expired session).
  Future<void> clearBiometricUnlock() async {
    await _storage.delete(key: _kRefresh);
    await _storage.delete(key: _kBiometric);
  }

  /// Clears active access and any stale refresh/biometric data; keeps email for login prefill.
  Future<void> invalidateExpiredSession() async {
    await _storage.delete(key: _kAccess);
    await clearBiometricUnlock();
  }

  Future<void> clear() async {
    await clearSession(keepBiometricUnlock: false);
  }
}

final secureStorageProvider = Provider<SecureStorageService>((ref) {
  return SecureStorageService(const FlutterSecureStorage());
});
