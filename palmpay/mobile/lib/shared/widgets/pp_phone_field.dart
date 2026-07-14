import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme/palmpay_palette.dart';

/// Theme-aware Pakistani mobile number field (+92 prefix).
class PpPhoneField extends StatelessWidget {
  const PpPhoneField({
    super.key,
    required this.controller,
    this.focusNode,
    this.hintText = '3XX XXXXXXX',
    this.autofocus = false,
    this.textInputAction = TextInputAction.done,
    this.onSubmitted,
  });

  final TextEditingController controller;
  final FocusNode? focusNode;
  final String hintText;
  final bool autofocus;
  final TextInputAction textInputAction;
  final ValueChanged<String>? onSubmitted;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = Theme.of(context).colorScheme;
    final scale = MediaQuery.textScalerOf(context).clamp(maxScaleFactor: 1.3);
    final fontSize = scale.scale(18.0);

    final fieldStyle = TextStyle(
      color: cs.onSurface,
      fontSize: fontSize,
      fontWeight: FontWeight.w600,
      letterSpacing: 0.5,
      height: 1.2,
    );

    return TextField(
      controller: controller,
      focusNode: focusNode,
      autofocus: autofocus,
      keyboardType: TextInputType.phone,
      textInputAction: textInputAction,
      inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[\d\s\-+]'))],
      style: fieldStyle,
      cursorColor: pp.primary,
      onSubmitted: onSubmitted,
      decoration: InputDecoration(
        labelText: 'Mobile number',
        hintText: hintText,
        hintStyle: TextStyle(
          color: pp.textMuted,
          fontSize: fontSize,
          fontWeight: FontWeight.w400,
        ),
        prefixIcon: Padding(
          padding: const EdgeInsets.only(left: 16, right: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.phone_android_rounded, size: 20, color: pp.primary),
              const SizedBox(width: 6),
              Text(
                '+92',
                style: fieldStyle.copyWith(
                  color: pp.textSecondary,
                  fontWeight: FontWeight.w700,
                ),
              ),
              Container(
                width: 1,
                height: 22,
                margin: const EdgeInsets.only(left: 10),
                color: pp.border,
              ),
            ],
          ),
        ),
        prefixIconConstraints: const BoxConstraints(minWidth: 0, minHeight: 0),
        filled: true,
        fillColor: pp.surfaceElevated,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: pp.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: pp.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: pp.primary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: cs.error),
        ),
      ),
    );
  }
}
