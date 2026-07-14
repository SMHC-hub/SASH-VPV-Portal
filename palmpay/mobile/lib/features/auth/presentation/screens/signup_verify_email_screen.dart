import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:pinput/pinput.dart';

import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../auth/presentation/providers/signup_draft_provider.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_form_scroll.dart';
import '../../../../shared/widgets/pp_screen_header.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';

class SignupVerifyEmailScreen extends ConsumerStatefulWidget {
  const SignupVerifyEmailScreen({super.key});

  @override
  ConsumerState<SignupVerifyEmailScreen> createState() => _SignupVerifyEmailScreenState();
}

class _SignupVerifyEmailScreenState extends ConsumerState<SignupVerifyEmailScreen> {
  final _controller = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final draft = ref.read(signupDraftProvider);
    if (draft?.devOtpEmail != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Dev email OTP: ${draft!.devOtpEmail}')),
        );
      });
    }
  }

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
      await ref.read(authControllerProvider.notifier).verifyEmailSignup(
            email: draft.email,
            otp: otp,
          );
      if (!mounted) return;
      context.go(AppRoutes.signupPin);
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

    return Scaffold(
      appBar: AppBar(title: const Text('Verify email')),
      body: PpFormScroll(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            PpScreenHeader(
              title: 'Verify email',
              subtitle: 'Enter the 6-digit code sent to ${draft?.email ?? ''}',
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
            if (_error != null) PpInlineErrorState(message: _error!),
            const Spacer(),
            PpButton(label: _loading ? 'Verifying...' : 'Verify email', onPressed: _loading ? null : () => _verify()),
          ],
        ),
      ),
    );
  }
}
