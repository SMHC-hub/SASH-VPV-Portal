import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../constants/api_config.dart';
import '../storage/secure_storage.dart';
import '../../features/onboarding/presentation/providers/auth_provider.dart';
import 'network_exceptions.dart';
import 'network_status_provider.dart';

final baseDioProvider = Provider<Dio>((ref) {
  return Dio(
    BaseOptions(
      baseUrl: ApiConfig.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      sendTimeout: const Duration(seconds: 15),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ),
  );
});

class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._ref);

  final Ref _ref;
  Future<void>? _refreshInFlight;

  Future<void> _invalidateSession() async {
    await _ref.read(secureStorageProvider).invalidateExpiredSession();
    final auth = _ref.read(authControllerProvider.notifier);
    await auth.invalidateSessionFromInterceptor();
  }

  Future<bool> _rotateRefreshToken() async {
    final refresh = await _ref.read(secureStorageProvider).readRefreshToken();
    if (refresh == null) return false;

    try {
      final res = await _ref.read(baseDioProvider).post<Map<String, dynamic>>(
        ApiConfig.authRefresh,
        data: {'refresh_token': refresh},
      );
      final data = res.data;
      final accessToken = data?['access_token'] as String?;
      final refreshToken = data?['refresh_token'] as String?;
      final phone = data?['phone'] as String?;
      if (accessToken == null || refreshToken == null || phone == null) {
        return false;
      }

      await _ref.read(secureStorageProvider).saveTokens(
            accessToken: accessToken,
            refreshToken: refreshToken,
            phone: phone,
            email: data?['email'] as String?,
          );
      return true;
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        await _invalidateSession();
      }
      return false;
    }
  }

  Future<bool> _ensureFreshAccessToken() async {
    if (_refreshInFlight != null) {
      await _refreshInFlight;
      final token = await _ref.read(secureStorageProvider).readAccessToken();
      return token != null && token.isNotEmpty;
    }

    final future = _rotateRefreshToken();
    _refreshInFlight = future;
    try {
      return await future;
    } finally {
      _refreshInFlight = null;
    }
  }

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _ref.read(secureStorageProvider).readAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401) {
      handler.next(err);
      return;
    }

    final path = err.requestOptions.path;
    if (path.contains('/auth/token/refresh')) {
      await _invalidateSession();
      handler.next(err);
      return;
    }
    if (path.contains('/auth/register/') ||
        path.contains('/auth/login/') ||
        path.contains('/auth/password/')) {
      handler.next(err);
      return;
    }

    final refreshed = await _ensureFreshAccessToken();
    if (!refreshed) {
      handler.next(err);
      return;
    }

    final accessToken = await _ref.read(secureStorageProvider).readAccessToken();
    if (accessToken == null || accessToken.isEmpty) {
      handler.next(err);
      return;
    }

    try {
      final opts = err.requestOptions;
      opts.headers['Authorization'] = 'Bearer $accessToken';
      final response = await _ref.read(baseDioProvider).fetch(opts);
      handler.resolve(response);
    } on DioException catch (e) {
      handler.next(e);
    }
  }
}

class _NetworkStatusInterceptor extends Interceptor {
  _NetworkStatusInterceptor(this._ref);

  final Ref _ref;

  NetworkStatusNotifier get _status => _ref.read(networkOnlineProvider.notifier);

  @override
  void onResponse(Response<dynamic> response, ResponseInterceptorHandler handler) {
    _status.markOnline();
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (isConnectionError(err)) {
      _status.markOffline();
    }
    handler.next(err);
  }
}

final dioProvider = Provider<Dio>((ref) {
  final dio = ref.watch(baseDioProvider);
  if (!dio.interceptors.any((i) => i is _NetworkStatusInterceptor)) {
    dio.interceptors.insert(0, _NetworkStatusInterceptor(ref));
  }
  if (!dio.interceptors.any((i) => i is _AuthInterceptor)) {
    dio.interceptors.add(_AuthInterceptor(ref));
  }
  return dio;
});
