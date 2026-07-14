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

class ScanResultLowBalanceScreen extends StatelessWidget {
  const ScanResultLowBalanceScreen({super.key, required this.notification});

  final PalmPayNotification notification;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;

    return Scaffold(
      appBar: AppBar(title: const Text('Low balance')),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
            children: [
              const Spacer(),
              const PpAnimatedResultIcon(
                icon: Icons.account_balance_wallet_outlined,
                color: AppColors.accent,
                iconSize: 44,
              ),
              const SizedBox(height: AppSpacing.lg),
              Text('Insufficient balance', style: AppTextStyles.display(context).copyWith(fontSize: 24)),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Could not pay ${notification.merchantName}',
                style: AppTextStyles.title(context),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                'You need Rs. ${notification.shortfallPkr.toStringAsFixed(0)} more',
                style: AppTextStyles.body(context),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                'Amount due: Rs. ${notification.amountPkr.toStringAsFixed(2)}',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: pp.primary,
                ),
              ),
              const Spacer(flex: 2),
              PpButton(
                label: 'Load money',
                onPressed: () => context.push(AppRoutes.addMoney),
              ),
              const SizedBox(height: AppSpacing.sm),
              TextButton(
                onPressed: () => context.go(AppRoutes.home),
                child: const Text('Back to home'),
              ),
          ],
        ),
      ),
    );
  }
}