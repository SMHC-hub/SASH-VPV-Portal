import 'package:flutter/material.dart';

import '../../core/constants/app_spacing.dart';
import '../../core/constants/app_text_styles.dart';

class PpInlineErrorState extends StatelessWidget {
  const PpInlineErrorState({
    super.key,
    required this.message,
    this.onRetry,
    this.retryLabel = 'Retry',
    this.leftIcon = Icons.error_outline,
  });

  final String message;
  final VoidCallback? onRetry;
  final String retryLabel;
  final IconData leftIcon;

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Material(
        color: cs.errorContainer,
        borderRadius: BorderRadius.circular(12),
        child: ListTile(
          dense: true,
          leading: Icon(leftIcon, color: cs.error),
          title: Text(
            message,
            style: AppTextStyles.body(context).copyWith(
                  color: cs.error,
                  fontSize: 13,
                ),
          ),
          trailing: onRetry != null
              ? TextButton(
                  onPressed: onRetry,
                  child: Text(retryLabel),
                )
              : null,
        ),
      ),
    );
  }
}

