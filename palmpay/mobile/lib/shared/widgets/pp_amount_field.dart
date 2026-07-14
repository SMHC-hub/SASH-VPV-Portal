import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/utils/pkr_format.dart';

/// Formats digits with comma grouping as the user types.
class PkrAmountInputFormatter extends TextInputFormatter {
  const PkrAmountInputFormatter();
  @override
  TextEditingValue formatEditUpdate(TextEditingValue oldValue, TextEditingValue newValue) {
    final digits = newValue.text.replaceAll(RegExp(r'[^0-9]'), '');
    if (digits.isEmpty) {
      return const TextEditingValue();
    }

    final normalized = digits.replaceFirst(RegExp(r'^0+(?=\d)'), '');
    if (normalized.isEmpty) {
      return const TextEditingValue(text: '0', selection: TextSelection.collapsed(offset: 1));
    }

    final value = double.parse(normalized);
    final formatted = PkrFormat.amount(value, showDecimals: false);
    return TextEditingValue(
      text: formatted,
      selection: TextSelection.collapsed(offset: formatted.length),
    );
  }
}

class PpAmountField extends StatelessWidget {
  const PpAmountField({
    super.key,
    required this.controller,
    this.focusNode,
    this.labelText = 'Amount (PKR)',
    this.hintText,
    this.textInputAction = TextInputAction.done,
    this.onSubmitted,
    this.enabled = true,
    this.autofocus = false,
  });

  final TextEditingController controller;
  final FocusNode? focusNode;
  final String labelText;
  final String? hintText;
  final TextInputAction textInputAction;
  final ValueChanged<String>? onSubmitted;
  final bool enabled;
  final bool autofocus;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      focusNode: focusNode,
      enabled: enabled,
      autofocus: autofocus,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      textInputAction: textInputAction,
      inputFormatters: const [PkrAmountInputFormatter()],
      decoration: InputDecoration(
        labelText: labelText,
        hintText: hintText,
        border: const OutlineInputBorder(),
        prefixText: 'PKR ',
      ),
      onSubmitted: onSubmitted,
    );
  }
}
