import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../shared/widgets/pp_animated_result_icon.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../domain/scan_models.dart';

class ScanResultFailedScreen extends StatelessWidget {
  const ScanResultFailedScreen({super.key, required this.notification});

  final PalmPayNotification notification;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;

    return Scaffold(
      appBar: AppBar(title: const Text('Payment failed')),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
            children: [
              const Spacer(),
              const PpAnimatedResultIcon(
                icon: Icons.close_rounded,
                color: AppColors.error,
              ),
              const SizedBox(height: AppSpacing.lg),
              Text('Payment failed', style: AppTextStyles.display(context).copyWith(fontSize: 24)),
              const SizedBox(height: AppSpacing.sm),
              Text(
                notification.merchantName,
                style: AppTextStyles.title(context),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                notification.body,
                style: AppTextStyles.body(context),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                'Rs. ${notification.amountPkr.toStringAsFixed(2)}',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w600,
                  color: pp.textSecondary,
                ),
              ),
              const Spacer(flex: 2),
              PpButton(
                label: 'Back to home',
                onPressed: () => context.go(AppRoutes.home),
              ),
              const SizedBox(height: AppSpacing.sm),
              TextButton(
                onPressed: () => context.go(AppRoutes.scan),
                child: const Text('Try again at kiosk'),
              ),
          ],
        ),
      ),
    );
  }
}