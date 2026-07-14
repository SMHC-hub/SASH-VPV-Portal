import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/constants/app_spacing.dart';
import '../../core/constants/app_text_styles.dart';
import '../../core/theme/palmpay_palette.dart';

class PpErrorState extends StatelessWidget {
  const PpErrorState({
    super.key,
    required this.message,
    this.onRetry,
    this.retryLabel = 'Try again',
  });

  final String message;
  final VoidCallback? onRetry;
  final String retryLabel;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = Theme.of(context).colorScheme;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.cloud_off_outlined, size: 56, color: cs.error),
            const SizedBox(height: AppSpacing.md),
            Text('Could not load', style: AppTextStyles.title(context), textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.sm),
            Text(
              message,
              style: AppTextStyles.body(context).copyWith(color: cs.error),
              textAlign: TextAlign.center,
            ),
            if (onRetry != null) ...[
              const SizedBox(height: AppSpacing.lg),
              FilledButton(
                onPressed: () {
                  HapticFeedback.lightImpact();
                  onRetry!();
                },
                style: FilledButton.styleFrom(backgroundColor: pp.primary),
                child: Text(retryLabel),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
