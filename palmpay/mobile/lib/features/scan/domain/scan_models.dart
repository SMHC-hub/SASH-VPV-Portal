class PalmMerchant {
  const PalmMerchant({
    required this.code,
    required this.name,
    required this.category,
  });

  final String code;
  final String name;
  final String category;

  factory PalmMerchant.fromJson(Map<String, dynamic> json) {
    return PalmMerchant(
      code: json['code'] as String? ?? '',
      name: json['name'] as String? ?? '',
      category: json['category'] as String? ?? 'retail',
    );
  }
}

class PalmPayNotification {
  const PalmPayNotification({
    required this.id,
    required this.kind,
    required this.title,
    required this.body,
    required this.payload,
    required this.createdAt,
  });

  final int id;
  final String kind;
  final String title;
  final String body;
  final Map<String, dynamic> payload;
  final String createdAt;

  bool get isSuccess => kind == 'palm_pay_success';
  bool get isLowBalance => kind == 'palm_pay_low_balance';

  double get amountPkr => (payload['amount_pkr'] as num?)?.toDouble() ?? 0;
  double get shortfallPkr => (payload['shortfall_pkr'] as num?)?.toDouble() ?? 0;
  String get merchantName => payload['merchant_name'] as String? ?? 'Merchant';
  String? get transactionReference => payload['transaction_reference'] as String?;

  factory PalmPayNotification.fromJson(Map<String, dynamic> json) {
    return PalmPayNotification(
      id: json['id'] as int? ?? 0,
      kind: json['kind'] as String? ?? '',
      title: json['title'] as String? ?? '',
      body: json['body'] as String? ?? '',
      payload: (json['payload'] as Map<String, dynamic>?) ?? {},
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}
