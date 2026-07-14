import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/constants/app_colors.dart';
import '../../core/constants/app_spacing.dart';

class PpButton extends StatelessWidget {
  const PpButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = PpButtonVariant.primary,
  });

  final String label;
  final VoidCallback? onPressed;
  final PpButtonVariant variant;

  @override
  Widget build(BuildContext context) {
    if (variant == PpButtonVariant.peach) {
      return FilledButton(
        onPressed: onPressed == null
            ? null
            : () {
                HapticFeedback.lightImpact();
                onPressed!();
              },
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.accent,
          foregroundColor: AppColors.onPrimary,
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
          child: Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16)),
        ),
      );
    }

    return FilledButton(
      onPressed: onPressed == null
          ? null
          : () {
              HapticFeedback.lightImpact();
              onPressed!();
            },
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
        child: Text(label),
      ),
    );
  }
}

enum PpButtonVariant { primary, peach }
