import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../providers/onboarding_provider.dart';
import '../widgets/palm_kiosk_enroll_panel.dart';

/// Full-screen enrollment (optional deep link). Prefer Scan tab for day-to-day use.
class PalmEnrollmentScreen extends ConsumerWidget {
  const PalmEnrollmentScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final needsPalm = ref.watch(onboardingControllerProvider).needsPalm;

    return Scaffold(
      appBar: AppBar(title: const Text('Palm enrollment')),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          if (!needsPalm) ...[
            Text('Already enrolled', style: AppTextStyles.title(context)),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Your palm is registered. You can pay at merchant kiosks.',
              style: AppTextStyles.body(context),
            ),
            const SizedBox(height: AppSpacing.xl),
            PpButton(
              label: 'Back to wallet',
              onPressed: () => context.go(AppRoutes.home),
            ),
          ] else
            const PalmKioskEnrollPanel(),
        ],
      ),
    );
  }
}
