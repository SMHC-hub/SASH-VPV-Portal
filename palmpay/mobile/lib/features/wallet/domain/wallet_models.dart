class WalletInfo {
  const WalletInfo({
    required this.accountNumber,
    required this.balancePkr,
    required this.isFrozen,
    required this.perTxnLimitPkr,
    required this.dailyTransferLimitPkr,
    required this.palmPayEnabled,
    required this.spendingPinSet,
    this.devSpendingPinHint,
  });

  final String accountNumber;
  final double balancePkr;
  final bool isFrozen;
  final double perTxnLimitPkr;
  final double dailyTransferLimitPkr;
  final bool palmPayEnabled;
  final bool spendingPinSet;
  final String? devSpendingPinHint;

  factory WalletInfo.fromJson(Map<String, dynamic> json) {
    return WalletInfo(
      accountNumber: json['account_number'] as String? ?? '',
      balancePkr: (json['balance_pkr'] as num?)?.toDouble() ?? 0,
      isFrozen: json['is_frozen'] as bool? ?? false,
      perTxnLimitPkr: (json['per_txn_limit_pkr'] as num?)?.toDouble() ?? 500000,
      dailyTransferLimitPkr: (json['daily_transfer_limit_pkr'] as num?)?.toDouble() ?? 500000,
      palmPayEnabled: json['palm_pay_enabled'] as bool? ?? true,
      spendingPinSet: json['spending_pin_set'] as bool? ?? false,
      devSpendingPinHint: json['dev_spending_pin_hint'] as String?,
    );
  }
}

class WalletTransaction {
  const WalletTransaction({
    required this.reference,
    required this.txType,
    required this.direction,
    required this.amountPkr,
    required this.counterpartyName,
    required this.description,
    required this.createdAt,
  });

  final String reference;
  final String txType;
  final String direction;
  final double amountPkr;
  final String counterpartyName;
  final String description;
  final String createdAt;

  factory WalletTransaction.fromJson(Map<String, dynamic> json) {
    return WalletTransaction(
      reference: json['reference'] as String? ?? '',
      txType: json['tx_type'] as String? ?? '',
      direction: json['direction'] as String? ?? '',
      amountPkr: (json['amount_pkr'] as num?)?.toDouble() ?? 0,
      counterpartyName: json['counterparty_name'] as String? ?? '',
      description: json['description'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  bool get isIncoming => direction == 'in';
}

class WalletTransactionDetail extends WalletTransaction {
  const WalletTransactionDetail({
    required super.reference,
    required super.txType,
    required super.direction,
    required super.amountPkr,
    required super.counterpartyName,
    required super.description,
    required super.createdAt,
    required this.status,
    this.topupMethod,
    this.completedAt,
  });

  final String status;
  final String? topupMethod;
  final String? completedAt;

  factory WalletTransactionDetail.fromJson(Map<String, dynamic> json) {
    return WalletTransactionDetail(
      reference: json['reference'] as String? ?? '',
      txType: json['tx_type'] as String? ?? '',
      direction: json['direction'] as String? ?? '',
      amountPkr: (json['amount_pkr'] as num?)?.toDouble() ?? 0,
      counterpartyName: json['counterparty_name'] as String? ?? '',
      description: json['description'] as String? ?? '',
      createdAt: json['created_at'] as String? ?? '',
      status: json['status'] as String? ?? 'complete',
      topupMethod: json['topup_method'] as String?,
      completedAt: json['completed_at'] as String?,
    );
  }
}

class TransactionListResult {
  const TransactionListResult({
    required this.items,
    required this.total,
    required this.offset,
    required this.limit,
    required this.hasMore,
  });

  final List<WalletTransaction> items;
  final int total;
  final int offset;
  final int limit;
  final bool hasMore;

  factory TransactionListResult.fromJson(Map<String, dynamic> json) {
    final raw = json['items'] as List<dynamic>? ?? [];
    return TransactionListResult(
      items: raw.whereType<Map<String, dynamic>>().map(WalletTransaction.fromJson).toList(),
      total: json['total'] as int? ?? 0,
      offset: json['offset'] as int? ?? 0,
      limit: json['limit'] as int? ?? 20,
      hasMore: json['has_more'] as bool? ?? false,
    );
  }
}

class AnalyticsTypeBreakdown {
  const AnalyticsTypeBreakdown({
    required this.txType,
    required this.count,
    required this.amountPkr,
  });

  final String txType;
  final int count;
  final double amountPkr;

  factory AnalyticsTypeBreakdown.fromJson(Map<String, dynamic> json) {
    return AnalyticsTypeBreakdown(
      txType: json['tx_type'] as String? ?? '',
      count: json['count'] as int? ?? 0,
      amountPkr: (json['amount_pkr'] as num?)?.toDouble() ?? 0,
    );
  }
}

class AnalyticsDailyBreakdown {
  const AnalyticsDailyBreakdown({
    required this.date,
    required this.inPkr,
    required this.outPkr,
  });

  final String date;
  final double inPkr;
  final double outPkr;

  factory AnalyticsDailyBreakdown.fromJson(Map<String, dynamic> json) {
    return AnalyticsDailyBreakdown(
      date: json['date'] as String? ?? '',
      inPkr: (json['in_pkr'] as num?)?.toDouble() ?? 0,
      outPkr: (json['out_pkr'] as num?)?.toDouble() ?? 0,
    );
  }
}

class AnalyticsSummary {
  const AnalyticsSummary({
    required this.period,
    required this.totalInPkr,
    required this.totalOutPkr,
    required this.netPkr,
    required this.txCount,
    required this.byType,
    required this.daily,
  });

  final String period;
  final double totalInPkr;
  final double totalOutPkr;
  final double netPkr;
  final int txCount;
  final List<AnalyticsTypeBreakdown> byType;
  final List<AnalyticsDailyBreakdown> daily;

  factory AnalyticsSummary.fromJson(Map<String, dynamic> json) {
    return AnalyticsSummary(
      period: json['period'] as String? ?? 'week',
      totalInPkr: (json['total_in_pkr'] as num?)?.toDouble() ?? 0,
      totalOutPkr: (json['total_out_pkr'] as num?)?.toDouble() ?? 0,
      netPkr: (json['net_pkr'] as num?)?.toDouble() ?? 0,
      txCount: json['tx_count'] as int? ?? 0,
      byType: (json['by_type'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(AnalyticsTypeBreakdown.fromJson)
          .toList(),
      daily: (json['daily'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(AnalyticsDailyBreakdown.fromJson)
          .toList(),
    );
  }
}

class TransferLookupResult {
  const TransferLookupResult({
    required this.accountId,
    required this.fullName,
    required this.phoneMasked,
  });

  final int accountId;
  final String fullName;
  final String phoneMasked;

  factory TransferLookupResult.fromJson(Map<String, dynamic> json) {
    return TransferLookupResult(
      accountId: json['account_id'] as int? ?? 0,
      fullName: json['full_name'] as String? ?? '',
      phoneMasked: json['phone_masked'] as String? ?? '',
    );
  }
}

class TransferPreview {
  const TransferPreview({
    required this.transferReference,
    required this.amountPkr,
    required this.feePkr,
    required this.totalDebitPkr,
    required this.recipientName,
    required this.recipientPhoneMasked,
    this.note,
    required this.expiresInSeconds,
    required this.message,
  });

  final String transferReference;
  final double amountPkr;
  final double feePkr;
  final double totalDebitPkr;
  final String recipientName;
  final String recipientPhoneMasked;
  final String? note;
  final int expiresInSeconds;
  final String message;

  factory TransferPreview.fromJson(Map<String, dynamic> json) {
    return TransferPreview(
      transferReference: json['transfer_reference'] as String? ?? '',
      amountPkr: (json['amount_pkr'] as num?)?.toDouble() ?? 0,
      feePkr: (json['fee_pkr'] as num?)?.toDouble() ?? 0,
      totalDebitPkr: (json['total_debit_pkr'] as num?)?.toDouble() ?? 0,
      recipientName: json['recipient_name'] as String? ?? '',
      recipientPhoneMasked: json['recipient_phone_masked'] as String? ?? '',
      note: json['note'] as String?,
      expiresInSeconds: json['expires_in_seconds'] as int? ?? 300,
      message: json['message'] as String? ?? '',
    );
  }
}

class TopUpInitResult {
  const TopUpInitResult({
    required this.orderReference,
    required this.amountPkr,
    required this.checkoutUrl,
    required this.message,
  });

  final String orderReference;
  final double amountPkr;
  final String checkoutUrl;
  final String message;

  factory TopUpInitResult.fromJson(Map<String, dynamic> json) {
    return TopUpInitResult(
      orderReference: json['order_reference'] as String? ?? '',
      amountPkr: (json['amount_pkr'] as num?)?.toDouble() ?? 0,
      checkoutUrl: json['checkout_url'] as String? ?? '',
      message: json['message'] as String? ?? '',
    );
  }
}
