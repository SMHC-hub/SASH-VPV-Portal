import 'package:flutter_test/flutter_test.dart';
import 'package:palmpay/core/network/network_exceptions.dart';
import 'package:palmpay/core/utils/pk_phone.dart';
import 'package:palmpay/core/utils/pkr_format.dart';
import 'package:dio/dio.dart';

void main() {
  group('PkrFormat', () {
    test('groups thousands with commas', () {
      expect(PkrFormat.amount(1000, showDecimals: false), '1,000');
      expect(PkrFormat.amount(1234567.89), '1,234,567.89');
    });

    test('parseAmount strips commas', () {
      expect(PkrFormat.parseAmount('2,500'), 2500);
      expect(PkrFormat.parseAmount(''), isNull);
    });

    test('compactLabel for lac and cr', () {
      expect(PkrFormat.compactLabel(150000), '1.50 lac');
      expect(PkrFormat.compactLabel(25000000), '2.50 cr');
    });
  });

  group('PkPhone', () {
    test('normalizes local and international formats', () {
      expect(PkPhone.normalize('03001234567'), '03001234567');
      expect(PkPhone.normalize('923001234567'), '03001234567');
      expect(PkPhone.normalize('3001234567'), '03001234567');
    });

    test('rejects invalid numbers', () {
      expect(PkPhone.normalize('12345'), isNull);
      expect(PkPhone.validationMessage(''), isNotNull);
    });
  });

  group('dioErrorMessage', () {
    test('maps connection errors', () {
      final err = DioException(
        requestOptions: RequestOptions(path: '/'),
        type: DioExceptionType.connectionError,
      );
      expect(
        dioErrorMessage(err),
        contains('Cannot reach the server'),
      );
    });

    test('maps refresh token expiry', () {
      final err = DioException(
        requestOptions: RequestOptions(path: '/'),
        response: Response(
          requestOptions: RequestOptions(path: '/'),
          statusCode: 401,
          data: {'detail': 'Invalid refresh token'},
        ),
        type: DioExceptionType.badResponse,
      );
      expect(dioErrorMessage(err), contains('Session expired'));
    });
  });
}
