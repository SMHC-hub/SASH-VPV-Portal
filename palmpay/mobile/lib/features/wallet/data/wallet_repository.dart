import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/api_config.dart';
import '../../../core/network/dio_client.dart';
import '../domain/wallet_models.dart';

class WalletRepository {
  WalletRepository(this._dio);

  final Dio _dio;

  Future<WalletInfo> fetchWallet() async {
    final res = await _dio.get<Map<String, dynamic>>(ApiConfig.wallet);
    return WalletInfo.fromJson(res.data!);
  }

  Future<WalletInfo> updateWalletLimit(double perTxnLimitPkr) async {
    final res = await _dio.put<Map<String, dynamic>>(
      ApiConfig.walletLimits,
      data: {'per_txn_limit_pkr': perTxnLimitPkr},
    );
    return WalletInfo.fromJson(res.data!);
  }

  Future<WalletInfo> updateWalletSettings({
    bool? isFrozen,
    bool? palmPayEnabled,
  }) async {
    final res = await _dio.put<Map<String, dynamic>>(
      ApiConfig.walletSettings,
      data: {
        if (isFrozen != null) 'is_frozen': isFrozen,
        if (palmPayEnabled != null) 'palm_pay_enabled': palmPayEnabled,
      },
    );
    return WalletInfo.fromJson(res.data!);
  }

  Future<List<WalletTransaction>> fetchRecentTransactions({int limit = 5}) async {
    final res = await _dio.get<List<dynamic>>(
      ApiConfig.walletTransactions,
      queryParameters: {'limit': limit},
    );
    return (res.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(WalletTransaction.fromJson)
        .toList();
  }

  Future<TransactionListResult> fetchTransactions({
    int offset = 0,
    int limit = 20,
    String? txType,
    String? direction,
    String? search,
  }) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConfig.transactions,
      queryParameters: {
        'offset': offset,
        'limit': limit,
        if (txType != null && txType.isNotEmpty) 'tx_type': txType,
        if (direction != null && direction.isNotEmpty) 'direction': direction,
        if (search != null && search.isNotEmpty) 'search': search,
      },
    );
    return TransactionListResult.fromJson(res.data!);
  }

  Future<WalletTransactionDetail> fetchTransactionDetail(String reference) async {
    final res = await _dio.get<Map<String, dynamic>>(ApiConfig.transactionDetail(reference));
    return WalletTransactionDetail.fromJson(res.data!);
  }

  Future<AnalyticsSummary> fetchAnalyticsSummary({String period = 'week'}) async {
    final res = await _dio.get<Map<String, dynamic>>(
      ApiConfig.analyticsSummary,
      queryParameters: {'period': period},
    );
    return AnalyticsSummary.fromJson(res.data!);
  }

  Future<TopUpInitResult> initiateTopUp(double amountPkr) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConfig.topupInitiate,
      data: {'amount_pkr': amountPkr},
    );
    return TopUpInitResult.fromJson(res.data!);
  }

  Future<double> simulateTopUpExisting(String orderReference) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConfig.topupSimulateExisting,
      data: {'order_reference': orderReference},
    );
    return (res.data?['new_balance_pkr'] as num?)?.toDouble() ?? 0;
  }

  Future<List<TransferLookupResult>> lookupRecipient(String query) async {
    final res = await _dio.get<List<dynamic>>(
      ApiConfig.transferLookup,
      queryParameters: {'q': query},
    );
    return (res.data ?? [])
        .whereType<Map<String, dynamic>>()
        .map(TransferLookupResult.fromJson)
        .toList();
  }

  Future<TransferPreview> initiateTransfer({
    required String recipientPhone,
    required double amountPkr,
    String? note,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConfig.transferInitiate,
      data: {
        'recipient_phone': recipientPhone,
        'amount_pkr': amountPkr,
        if (note != null && note.isNotEmpty) 'note': note,
      },
    );
    return TransferPreview.fromJson(res.data!);
  }

  Future<double> confirmTransfer({
    required String transferReference,
    required String spendingPin,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      ApiConfig.transferConfirm,
      data: {
        'transfer_reference': transferReference,
        'spending_pin': spendingPin,
      },
    );
    return (res.data?['new_balance_pkr'] as num?)?.toDouble() ?? 0;
  }
}

final walletRepositoryProvider = Provider<WalletRepository>((ref) {
  return WalletRepository(ref.watch(dioProvider));
});
