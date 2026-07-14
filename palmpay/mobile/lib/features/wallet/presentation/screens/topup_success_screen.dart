import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/security/secure_screen_service.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../core/utils/pkr_format.dart';
import '../../../../shared/widgets/pp_animated_result_icon.dart';
import '../../../../shared/widgets/pp_button.dart';
class TopUpSuccessScreen extends StatelessWidget {
  const TopUpSuccessScreen({super.key, required this.amountPkr});

  final double amountPkr;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;

    return SecureScreen(
      child: Scaffold(
        appBar: AppBar(title: const Text('Top-up complete')),
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
                Text('Money added', style: AppTextStyles.display(context).copyWith(fontSize: 24)),
                const SizedBox(height: AppSpacing.md),
                Text(
                  'PKR ${PkrFormat.amount(amountPkr)}',
                  style: TextStyle(
                    fontSize: 36,
                    fontWeight: FontWeight.w700,
                    color: pp.primary,
                    letterSpacing: -0.5,
                  ),
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