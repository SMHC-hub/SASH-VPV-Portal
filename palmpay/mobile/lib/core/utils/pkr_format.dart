/// PKR amount formatting for wallet UI.
abstract final class PkrFormat {
  static String amount(double value, {bool showDecimals = true}) {
    final fixed = showDecimals ? value.toStringAsFixed(2) : value.round().toString();
    final parts = fixed.split('.');
    final grouped = _groupDigits(parts[0]);
    if (showDecimals && parts.length > 1) {
      return '$grouped.${parts[1]}';
    }
    return grouped;
  }

  /// Parse user-entered PKR text (commas and spaces allowed).
  static double? parseAmount(String input) {
    final cleaned = input.replaceAll(',', '').replaceAll(' ', '').trim();
    if (cleaned.isEmpty) return null;
    return double.tryParse(cleaned);
  }

  /// Compact label for very large balances (e.g. 25.00 lac).
  static String? compactLabel(double value) {
    if (value >= 10000000) {
      return '${(value / 10000000).toStringAsFixed(2)} cr';
    }
    if (value >= 100000) {
      return '${(value / 100000).toStringAsFixed(2)} lac';
    }
    return null;
  }

  static String _groupDigits(String digits) {
    if (digits.length <= 3) return digits;
    final buf = StringBuffer();
    final rem = digits.length % 3;
    if (rem > 0) {
      buf.write(digits.substring(0, rem));
      if (digits.length > rem) buf.write(',');
    }
    for (var i = rem; i < digits.length; i += 3) {
      if (i > rem) buf.write(',');
      buf.write(digits.substring(i, i + 3));
    }
    return buf.toString();
  }
}
