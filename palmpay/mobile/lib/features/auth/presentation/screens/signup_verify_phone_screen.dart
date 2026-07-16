import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:pinput/pinput.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../auth/presentation/providers/signup_draft_provider.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_screen_header.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';

class SignupVerifyPhoneScreen extends ConsumerStatefulWidget {
  const SignupVerifyPhoneScreen({super.key, this.devOtp});

  /// Only present when server is in PALMPAY_DEV_OTP mode.
  final String? devOtp;

  @override
  ConsumerState<SignupVerifyPhoneScreen> createState() => _SignupVerifyPhoneScreenState();
}

class _SignupVerifyPhoneScreenState extends ConsumerState<SignupVerifyPhoneScreen> {
  final _controller = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _verify([String? code]) async {
    final draft = ref.read(signupDraftProvider);
    if (draft == null) {
      context.go(AppRoutes.signupDetails);
      return;
    }
    final otp = code ?? _controller.text;
    if (otp.length != 6) return;

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authControllerProvider.notifier).verifyPhoneSignup(
            phone: draft.phone,
            otp: otp,
          );
      if (!mounted) return;
      context.go(AppRoutes.signupVerifyEmail);
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final draft = ref.watch(signupDraftProvider);
    final pp = context.pp;
    final emailHint = draft?.email.isNotEmpty == true ? draft!.email : 'your email';

    return Scaffold(
      appBar: AppBar(title: const Text('Verify phone')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                child: SingleChildScrollView(
                  keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      PpScreenHeader(
                        title: 'Verify phone',
                        subtitle:
                            'Enter the 6-digit phone verification code we emailed to $emailHint',
                      ),
                      Pinput(
                        length: 6,
                        controller: _controller,
                        keyboardType: TextInputType.number,
                        defaultPinTheme: PinTheme(
                          width: 44,
                          height: 52,
                          decoration: BoxDecoration(
                            color: pp.surfaceElevated,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: pp.border),
                          ),
                        ),
                        onCompleted: _verify,
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: AppSpacing.md),
                        PpInlineErrorState(message: _error!),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.md),
              PpButton(
                label: _loading ? 'Verifying...' : 'Verify phone',
                onPressed: _loading ? null : () => _verify(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
