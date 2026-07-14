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

class ScanResultSuccessScreen extends StatelessWidget {
  const ScanResultSuccessScreen({super.key, required this.notification});

  final PalmPayNotification notification;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = context.cs;

    return Scaffold(
      appBar: AppBar(title: const Text('Payment complete')),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
            children: [
              const Spacer(),
              const PpAnimatedResultIcon(
                icon: Icons.check_rounded,
                color: AppColors.success,
              ),
              const SizedBox(height: AppSpacing.lg),
              Text('Payment successful', style: AppTextStyles.display(context).copyWith(fontSize: 24)),
              const SizedBox(height: AppSpacing.sm),
              Text(
                notification.merchantName,
                style: AppTextStyles.title(context),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                'Rs. ${notification.amountPkr.toStringAsFixed(2)}',
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.w700,
                  color: pp.primary,
                  letterSpacing: -0.5,
                ),
              ),
              if (notification.transactionReference != null) ...[
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Ref ${notification.transactionReference}',
                  style: AppTextStyles.label(context),
                ),
              ],
              const Spacer(flex: 2),
              PpButton(
                label: 'Done',
                onPressed: () => context.go(AppRoutes.home),
              ),
              const SizedBox(height: AppSpacing.sm),
              TextButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Receipt PDF — Day 6')),
                  );
                },
                child: Text('View receipt', style: TextStyle(color: cs.onSurface)),
              ),
          ],
        ),
      ),
    );
  }
}