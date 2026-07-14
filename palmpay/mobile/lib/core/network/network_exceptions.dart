import 'package:dio/dio.dart';

const _fieldLabels = <String, String>{
  'email': 'Email',
  'password': 'Password',
  'full_name': 'Full name',
  'phone': 'Phone number',
  'otp': 'Verification code',
  'login_pin': 'PIN',
  'refresh_token': 'Session',
};

String _validationItemMessage(Map<dynamic, dynamic> item) {
  final msg = item['msg']?.toString() ?? 'Invalid value';
  final loc = item['loc'];
  if (loc is List && loc.isNotEmpty) {
    final field = loc.last.toString();
    if (field == 'body') {
      return 'Invalid request. Check your details and try again.';
    }
    final label = _fieldLabels[field] ?? field.replaceAll('_', ' ');
    if (msg.toLowerCase().contains('field required') || msg.toLowerCase().contains('missing')) {
      return '$label is required';
    }
    if (msg.toLowerCase().contains('at least')) {
      return '$label: $msg';
    }
    return '$label: $msg';
  }
  return msg;
}

/// User-facing message from a failed API call (never raw Dio stack text).
String dioErrorMessage(DioException e) {
  final status = e.response?.statusCode;
  final data = e.response?.data;

  if (data is Map) {
    final detail = data['detail'];
    if (detail is String && detail.isNotEmpty) {
      final lower = detail.toLowerCase();
      if (lower.contains('refresh token')) {
        return 'Session expired. Log in with your email and password.';
      }
      return detail;
    }
    if (detail is List && detail.isNotEmpty) {
      return detail
          .whereType<Map>()
          .map(_validationItemMessage)
          .join(' ')
          .trim();
    }
  }

  if (data is String && data.isNotEmpty) return data;

  if (status == 422) {
    return 'Please check your details and try again.';
  }
  if (status == 429) {
    return 'Too many attempts. Please wait and try again.';
  }
  if (status == 400) {
    return 'Invalid request. Check your details and try again.';
  }
  if (status == 401) {
    return 'Wrong email or password. Please try again.';
  }
  if (status == 404) {
    return 'Account not found. Sign up first or check your email.';
  }
  if (status == 409) {
    return 'This email or phone is already registered. Try logging in.';
  }
  if (e.type == DioExceptionType.connectionTimeout ||
      e.type == DioExceptionType.receiveTimeout ||
      e.type == DioExceptionType.sendTimeout) {
    return 'Connection timed out. Check your network and try again.';
  }
  if (e.type == DioExceptionType.connectionError) {
    return 'Cannot reach the server. Check your Wi‑Fi and try again.';
  }

  return 'Something went wrong. Please try again.';
}

/// Friendly message for any caught error (Dio or otherwise).
String userFacingError(Object error) {
  if (error is DioException) return dioErrorMessage(error);
  final text = error.toString();
  if (text.contains('SocketException') || text.contains('Failed host lookup')) {
    return 'Cannot reach the server. Check your Wi‑Fi and try again.';
  }
  return 'Something went wrong. Please try again.';
}

bool isConnectionError(DioException e) {
  return e.type == DioExceptionType.connectionError ||
      e.type == DioExceptionType.connectionTimeout ||
      e.type == DioExceptionType.receiveTimeout ||
      e.type == DioExceptionType.sendTimeout;
}
