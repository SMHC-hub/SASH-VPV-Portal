/// Pakistani mobile number helpers (03XX XXXXXXX).
abstract final class PkPhone {
  /// Returns normalized `03XXXXXXXXX` or null if invalid.
  static String? normalize(String raw) {
    var digits = raw.replaceAll(RegExp(r'\D'), '');
    if (digits.isEmpty) return null;

    if (digits.startsWith('92') && digits.length >= 12) {
      digits = '0${digits.substring(2)}';
    } else if (!digits.startsWith('0') && digits.length == 10 && digits.startsWith('3')) {
      digits = '0$digits';
    }

    if (!RegExp(r'^03\d{9}$').hasMatch(digits)) return null;
    return digits;
  }

  static String? validationMessage(String raw) {
    final trimmed = raw.trim();
    if (trimmed.isEmpty) return 'Enter your mobile number';
    if (normalize(trimmed) == null) {
      return 'Use a valid Pakistani number (03XX XXXXXXX)';
    }
    return null;
  }
}
