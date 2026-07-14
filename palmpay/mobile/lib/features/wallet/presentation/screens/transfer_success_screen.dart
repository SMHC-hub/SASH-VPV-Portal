import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../core/security/secure_screen_service.dart';
import '../../../../core/utils/pkr_format.dart';
import '../../../../shared/widgets/pp_animated_result_icon.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../domain/wallet_models.dart';
class TransferSuccessScreen extends StatelessWidget {
  const TransferSuccessScreen({super.key, required this.preview});

  final TransferPreview preview;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;

    return SecureScreen(
      child: Scaffold(
      appBar: AppBar(title: const Text('Transfer sent')),
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
              Text('Money sent', style: AppTextStyles.display(context).copyWith(fontSize: 24)),
              const SizedBox(height: AppSpacing.sm),
              Text(
                preview.recipientName,
                style: AppTextStyles.title(context),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                'PKR ${PkrFormat.amount(preview.amountPkr)}',
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.w700,
                  color: pp.primary,
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Ref ${preview.transferReference}',
                style: AppTextStyles.label(context),
              ),
              const Spacer(flex: 2),
              PpButton(
                label: 'Done',
                onPressed: () => context.go(AppRoutes.home),
              ),
            ],
          ),
        ),
      ),
    );
  }
}