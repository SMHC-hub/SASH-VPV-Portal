import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../shared/widgets/pp_animated_result_icon.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../core/theme/palmpay_palette.dart';

class EnrollmentSuccessScreen extends StatelessWidget {
  const EnrollmentSuccessScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              PpAnimatedResultIcon(
                icon: Icons.fingerprint,
                color: pp.primary,
                iconSize: 56,
              ),
              const SizedBox(height: AppSpacing.lg),
              Text('You\'re enrolled!', style: AppTextStyles.display(context).copyWith(fontSize: 24)),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Palm vein registered. You can pay at merchant kiosks.',
                style: AppTextStyles.body(context),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.xxl),
              PpButton(
                label: 'Go to wallet',
                onPressed: () => context.go(AppRoutes.home),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
