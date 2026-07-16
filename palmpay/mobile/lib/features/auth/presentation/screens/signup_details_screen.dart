import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/utils/pk_phone.dart';
import '../../../../core/constants/veinpay_brand.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_form_scroll.dart';
import '../../../../shared/widgets/pp_phone_field.dart';
import '../../../../shared/widgets/veinpay_logo.dart';
import '../widgets/google_auth_button.dart';

class SignupDetailsScreen extends ConsumerStatefulWidget {
  const SignupDetailsScreen({super.key});

  @override
  ConsumerState<SignupDetailsScreen> createState() => _SignupDetailsScreenState();
}

class _SignupDetailsScreenState extends ConsumerState<SignupDetailsScreen> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  final _nameFocus = FocusNode();
  final _emailFocus = FocusNode();
  final _phoneFocus = FocusNode();
  final _passwordFocus = FocusNode();
  final _confirmFocus = FocusNode();
  bool _loading = false;
  bool _obscure = true;
  String? _error;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    _nameFocus.dispose();
    _emailFocus.dispose();
    _phoneFocus.dispose();
    _passwordFocus.dispose();
    _confirmFocus.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final name = _nameController.text.trim();
    final email = _emailController.text.trim();
    final phoneMsg = PkPhone.validationMessage(_phoneController.text);
    final password = _passwordController.text;
    final confirm = _confirmController.text;

    if (name.length < 2) {
      setState(() => _error = 'Enter your full name');
      return;
    }
    if (!email.contains('@')) {
      setState(() => _error = 'Enter a valid email');
      return;
    }
    if (phoneMsg != null) {
      setState(() => _error = phoneMsg);
      return;
    }
    if (password.length < 8) {
      setState(() => _error = 'Password must be at least 8 characters');
      return;
    }
    if (password != confirm) {
      setState(() => _error = 'Passwords do not match');
      return;
    }

    final phone = PkPhone.normalize(_phoneController.text)!;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref.read(authControllerProvider.notifier).startSignup(
            fullName: name,
            email: email,
            phone: phone,
            password: password,
          );
      if (!mounted) return;
      context.go(AppRoutes.signupVerifyPhone, extra: {
        'devOtpPhone': result.devOtpPhone,
        'devOtpEmail': result.devOtpEmail,
      });
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create account')),
      body: PpFormScroll(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const VeinPayLogo(size: VeinPayBrand.logoMd),
            const SizedBox(height: AppSpacing.md),
            Text('Sign up for ${VeinPayBrand.appName}', style: AppTextStyles.title(context)),
            const SizedBox(height: AppSpacing.lg),
            GoogleAuthButton(
              intent: 'signup',
              disabled: _loading,
              onSuccess: () {
                if (!mounted) return;
                // Router redirect sends KYC/home after session is stored.
              },
              onError: (msg) {
                if (!mounted) return;
                setState(() => _error = msg);
              },
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                const Expanded(child: Divider()),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm),
                  child: Text('or email', style: AppTextStyles.label(context)),
                ),
                const Expanded(child: Divider()),
              ],
            ),
            const SizedBox(height: AppSpacing.lg),
            TextField(
              controller: _nameController,
              focusNode: _nameFocus,
              textCapitalization: TextCapitalization.words,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Full name'),
              onSubmitted: (_) => _emailFocus.requestFocus(),
            ),
            const SizedBox(height: AppSpacing.md),
            TextField(
              controller: _emailController,
              focusNode: _emailFocus,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(labelText: 'Email'),
              onSubmitted: (_) => _phoneFocus.requestFocus(),
            ),
            const SizedBox(height: AppSpacing.md),
            PpPhoneField(
              controller: _phoneController,
              focusNode: _phoneFocus,
              textInputAction: TextInputAction.next,
              onSubmitted: (_) => _passwordFocus.requestFocus(),
            ),
            const SizedBox(height: AppSpacing.md),
            TextField(
              controller: _passwordController,
              focusNode: _passwordFocus,
              obscureText: _obscure,
              textInputAction: TextInputAction.next,
              decoration: InputDecoration(
                labelText: 'Password',
                suffixIcon: IconButton(
                  icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility),
                  onPressed: () => setState(() => _obscure = !_obscure),
                ),
              ),
              onSubmitted: (_) => _confirmFocus.requestFocus(),
            ),
            const SizedBox(height: AppSpacing.md),
            TextField(
              controller: _confirmController,
              focusNode: _confirmFocus,
              obscureText: _obscure,
              textInputAction: TextInputAction.done,
              decoration: const InputDecoration(labelText: 'Confirm password'),
              onSubmitted: (_) => _submit(),
            ),
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: AppSpacing.xl),
            PpButton(label: _loading ? 'Continuing...' : 'Continue', onPressed: _loading ? null : _submit),
            TextButton(onPressed: () => context.go(AppRoutes.login), child: const Text('Already have an account? Log in')),
          ],
        ),
      ),
    );
  }
}
