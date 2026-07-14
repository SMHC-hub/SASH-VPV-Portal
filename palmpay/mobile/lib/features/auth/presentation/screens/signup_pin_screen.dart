import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../auth/presentation/providers/signup_draft_provider.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_login_pin_input.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';

class SignupPinScreen extends ConsumerStatefulWidget {
  const SignupPinScreen({super.key});

  @override
  ConsumerState<SignupPinScreen> createState() => _SignupPinScreenState();
}

class _SignupPinScreenState extends ConsumerState<SignupPinScreen> {
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

    final draft = ref.read(signupDraftProvider);
    if (draft == null || !draft.phoneVerified || !draft.emailVerified) {
      setState(() => _error = 'Complete phone and email verification first');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authControllerProvider.notifier).finishSignup(loginPin: pin);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Account created! Log in with your email.')),
      );
      context.go(AppRoutes.login);
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create PIN')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Set your 4-digit PIN', style: AppTextStyles.title(context)),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'You will use email and password to log in. This PIN secures payments.',
              style: AppTextStyles.body(context),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text('New PIN', style: AppTextStyles.label(context)),
            const SizedBox(height: AppSpacing.sm),
            PpLoginPinInput(controller: _pinController, length: 4),
            const SizedBox(height: AppSpacing.md),
            Text('Confirm PIN', style: AppTextStyles.label(context)),
            const SizedBox(height: AppSpacing.sm),
            PpLoginPinInput(controller: _confirmController, length: 4, onCompleted: (_) => _submit()),
            if (_error != null) PpInlineErrorState(message: _error!),
            const SizedBox(height: AppSpacing.xl),
            PpButton(label: _loading ? 'Saving...' : 'Finish signup', onPressed: _loading ? null : _submit),
          ],
        ),
      ),
    );
  }
}
