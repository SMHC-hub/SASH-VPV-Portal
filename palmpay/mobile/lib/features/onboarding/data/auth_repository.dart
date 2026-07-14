import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_config.dart';
import '../../../core/network/dio_client.dart';
import '../../auth/domain/auth_flow_models.dart';
import '../domain/auth_session.dart';
import '../domain/onboarding_models.dart';

class AuthRepository {
  AuthRepository(this._dio, this._publicDio);

  final Dio _dio;
  final Dio _publicDio;

  Future<String?> requestOtp(String phone) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authRegisterPhone,
      data: {'phone': phone},
    );
    return res.data?['dev_otp'] as String?;
  }

  Future<AuthSession> verifyOtp({
    required String phone,
    required String otp,
    String? fullName,
  }) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authVerifyOtp,
      data: {
        'phone': phone,
        'otp': otp,
        if (fullName != null && fullName.isNotEmpty) 'full_name': fullName,
      },
    );
    return AuthSession.fromJson(res.data!);
  }

  Future<AuthSession> refresh(String refreshToken) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authRefresh,
      data: {'refresh_token': refreshToken},
    );
    return AuthSession.fromJson(res.data!);
  }

  Future<AuthSession> loginWithEmail({
    required String email,
    required String password,
  }) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authLoginEmail,
      data: {'email': email.trim().toLowerCase(), 'password': password},
    );
    return AuthSession.fromJson(res.data!);
  }

  Future<PasswordResetStartResult> requestPasswordReset(String email) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authForgotPassword,
      data: {'email': email.trim().toLowerCase()},
    );
    return PasswordResetStartResult.fromJson(res.data!);
  }

  Future<void> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authResetPassword,
      data: {
        'email': email.trim().toLowerCase(),
        'otp': otp,
        'new_password': newPassword,
      },
    );
  }

  Future<SignupStartResult> signupStart({
    required String fullName,
    required String email,
    required String phone,
    required String password,
  }) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authSignupStart,
      data: {
        'full_name': fullName,
        'email': email.trim().toLowerCase(),
        'phone': phone,
        'password': password,
      },
    );
    return SignupStartResult.fromJson(res.data!);
  }

  Future<void> verifyPhoneSignup({required String phone, required String otp}) async {
    await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authSignupVerifyPhone,
      data: {'phone': phone, 'otp': otp},
    );
  }

  Future<void> verifyEmailSignup({required String email, required String otp}) async {
    await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authSignupVerifyEmail,
      data: {'email': email.trim().toLowerCase(), 'otp': otp},
    );
  }

  Future<void> finishSignup({
    required String phone,
    required String email,
    required String loginPin,
  }) async {
    await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authSignupFinish,
      data: {
        'phone': phone,
        'email': email.trim().toLowerCase(),
        'login_pin': loginPin,
      },
    );
  }

  Future<AccountCheckResult> checkAccount(String phone) async {
    final res = await _publicDio.get<Map<String, dynamic>>(
      ApiConfig.authAccountCheck,
      queryParameters: {'phone': phone},
    );
    return AccountCheckResult.fromJson(res.data!);
  }

  /// Returns null when the check endpoint is unavailable (e.g. stale backend).
  /// Callers should fall back to OTP rather than blocking the user.
  Future<AccountCheckResult?> tryCheckAccount(String phone) async {
    try {
      return await checkAccount(phone);
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 404 || status == 501 || status == 503) return null;
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout ||
          e.type == DioExceptionType.receiveTimeout) {
        return null;
      }
      rethrow;
    }
  }

  Future<void> confirmOtpSignup({required String phone, required String otp}) async {
    await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authConfirmOtpSignup,
      data: {'phone': phone, 'otp': otp},
    );
  }

  Future<AuthSession> completeSignup({
    required String phone,
    required String fullName,
    required String loginPin,
    bool useSamePinForSpending = false,
  }) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authCompleteSignup,
      data: {
        'phone': phone,
        'full_name': fullName,
        'login_pin': loginPin,
        'use_same_pin_for_spending': useSamePinForSpending,
      },
    );
    return AuthSession.fromJson(res.data!);
  }

  Future<AuthSession> loginWithPin({
    required String phone,
    required String loginPin,
  }) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authLoginPin,
      data: {'phone': phone, 'login_pin': loginPin},
    );
    return AuthSession.fromJson(res.data!);
  }

  Future<AuthSession> setLoginPin({
    required String loginPin,
    bool useSamePinForSpending = false,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConfig.authSetLoginPin,
      data: {
        'login_pin': loginPin,
        'use_same_pin_for_spending': useSamePinForSpending,
      },
    );
    return AuthSession.fromJson(res.data!);
  }

  Future<AuthSession> resetLoginPin({
    required String phone,
    required String otp,
    required String loginPin,
    bool useSamePinForSpending = false,
  }) async {
    final res = await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.authResetLoginPin,
      data: {
        'phone': phone,
        'otp': otp,
        'login_pin': loginPin,
        'use_same_pin_for_spending': useSamePinForSpending,
      },
    );
    return AuthSession.fromJson(res.data!);
  }

  Future<WalletProfile> fetchProfile() async {
    final res = await _dio.get<Map<String, dynamic>>(ApiConfig.palmpayProfile);
    return WalletProfile.fromJson(res.data!);
  }

  Future<KycStatus> fetchKycStatus() async {
    final res = await _dio.get<Map<String, dynamic>>(ApiConfig.kycStatus);
    return KycStatus.fromJson(res.data!);
  }

  Future<KycStatus> submitKyc({
    required String fullName,
    required String cnic,
    required String frontImagePath,
    String? backImagePath,
  }) async {
    final form = FormData.fromMap({
      'full_name': fullName,
      'cnic': cnic,
      'front_image': await MultipartFile.fromFile(frontImagePath, filename: 'front.jpg'),
      if (backImagePath != null)
        'back_image': await MultipartFile.fromFile(backImagePath, filename: 'back.jpg'),
    });
    final res = await _dio.post<Map<String, dynamic>>(ApiConfig.kycSubmit, data: form);
    return KycStatus(
      status: res.data?['status'] as String? ?? 'pending',
      cnicMasked: res.data?['cnic_masked'] as String?,
      fullName: fullName,
      message: res.data?['message'] as String? ?? '',
    );
  }

  Future<EnrollmentSession> initiateEnrollment() async {
    final res = await _dio.post<Map<String, dynamic>>(ApiConfig.palmEnrollInitiate);
    return EnrollmentSession.fromJson(res.data!);
  }

  Future<EnrollmentStatus> fetchEnrollmentStatus() async {
    final res = await _dio.get<Map<String, dynamic>>(ApiConfig.palmEnrollStatus);
    return EnrollmentStatus.fromJson(res.data!);
  }

  Future<void> devCompleteEnrollment(String sessionCode) async {
    await _publicDio.post<Map<String, dynamic>>(
      ApiConfig.kioskEnrollComplete,
      data: {'session_code': sessionCode},
    );
  }
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(dioProvider), ref.watch(baseDioProvider));
});
