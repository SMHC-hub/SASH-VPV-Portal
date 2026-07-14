import 'package:flutter/material.dart';
import 'package:pinput/pinput.dart';

import '../../core/theme/palmpay_palette.dart';

class PpLoginPinInput extends StatelessWidget {
  const PpLoginPinInput({
    super.key,
    required this.controller,
    this.length = 4,
    this.onCompleted,
  });

  final TextEditingController controller;
  final int length;
  final ValueChanged<String>? onCompleted;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = Theme.of(context).colorScheme;

    final theme = PinTheme(
      width: 44,
      height: 52,
      textStyle: TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: cs.onSurface),
      decoration: BoxDecoration(
        color: pp.surfaceElevated,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: pp.border),
      ),
    );

    return Pinput(
      controller: controller,
      length: length,
      obscureText: true,
      keyboardType: TextInputType.number,
      defaultPinTheme: theme,
      focusedPinTheme: theme.copyWith(
        decoration: theme.decoration?.copyWith(border: Border.all(color: pp.primary, width: 2)),
      ),
      onCompleted: onCompleted,
    );
  }
}
