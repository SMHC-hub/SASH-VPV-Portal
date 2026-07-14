import 'package:flutter/material.dart';

import '../../core/constants/app_spacing.dart';
import '../../core/constants/app_text_styles.dart';

class PpScreenHeader extends StatelessWidget {
  const PpScreenHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.centered = false,
    this.bottomSpacing = AppSpacing.lg,
  });

  final String title;
  final String? subtitle;
  final bool centered;
  final double bottomSpacing;

  @override
  Widget build(BuildContext context) {
    final textAlign = centered ? TextAlign.center : TextAlign.start;

    return Padding(
      padding: EdgeInsets.only(bottom: bottomSpacing),
      child: Column(
        crossAxisAlignment: centered ? CrossAxisAlignment.center : CrossAxisAlignment.start,
        children: [
          Text(title, style: AppTextStyles.title(context), textAlign: textAlign),
          if (subtitle != null && subtitle!.trim().isNotEmpty) ...[
            const SizedBox(height: AppSpacing.sm),
            Text(subtitle!, style: AppTextStyles.body(context), textAlign: textAlign),
          ],
        ],
      ),
    );
  }
}
