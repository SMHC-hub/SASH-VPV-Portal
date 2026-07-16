import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';
import '../../../onboarding/presentation/providers/onboarding_provider.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';
import '../../../../shared/widgets/pp_login_pin_input.dart';

/// Post-KYC payment PIN (used when sending money). Required for Google signup.
class SetupSpendingPinScreen extends ConsumerStatefulWidget {
  const SetupSpendingPinScreen({super.key});

  @override
  ConsumerState<SetupSpendingPinScreen> createState() => _SetupSpendingPinScreenState();
}

class _SetupSpendingPinScreenState extends ConsumerState<SetupSpendingPinScreen> {
  final _pinController = TextEditingController();
  final _confirmController = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _pinController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final pin = _pinController.text;
    final confirm = _confirmController.text;
    if (pin.length != 4) {
      setState(() => _error = 'PIN must be 4 digits');
      return;
    }
    if (pin != confirm) {
      setState(() => _error = 'PINs do not match');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authControllerProvider.notifier).setSpendingPin(pin);
      await ref.read(onboardingControllerProvider.notifier).refresh();
      if (!mounted) return;
      context.go(AppRoutes.home);
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Payment PIN')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Create your payment PIN', style: AppTextStyles.title(context)),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'This 4-digit PIN confirms sending money to other VeinPay accounts. '
              'Keep it private — you will enter it every time you transfer funds.',
              style: AppTextStyles.body(context),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text('New PIN', style: AppTextStyles.label(context)),
            const SizedBox(height: AppSpacing.sm),
            PpLoginPinInput(controller: _pinController, length: 4),
            const SizedBox(height: AppSpacing.md),
            Text('Confirm PIN', style: AppTextStyles.label(context)),
            const SizedBox(height: AppSpacing.sm),
            PpLoginPinInput(
              controller: _confirmController,
              length: 4,
              onCompleted: (_) => _submit(),
            ),
            if (_error != null) PpInlineErrorState(message: _error!),
            const SizedBox(height: AppSpacing.xl),
            PpButton(
              label: _loading ? 'Saving…' : 'Continue',
              onPressed: _loading ? null : _submit,
            ),
          ],
        ),
      ),
    );
  }
}
