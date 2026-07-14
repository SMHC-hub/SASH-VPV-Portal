import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/constants/veinpay_brand.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';
import '../../../onboarding/data/auth_repository.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_form_scroll.dart';
import '../../../../shared/widgets/pp_screen_header.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';
import '../../../../shared/widgets/veinpay_logo.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailFocus = FocusNode();
  final _passwordFocus = FocusNode();
  bool _loading = false;
  bool _obscure = true;
  bool _biometricReady = false;
  bool _prepared = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _prepareLogin());
  }

  /// Router redirect handles navigation after auth — do not call context.go here.
  void _onAuthSuccess() {
    if (!mounted) return;
    setState(() {
      _loading = true;
      _error = null;
    });
  }

  Future<void> _prepareLogin() async {
    if (_prepared) return;
    _prepared = true;

    final email = await ref.read(secureStorageProvider).readEmail();
    if (!mounted) return;
    if (email != null) _emailController.text = email;

    final canBio = await ref.read(authControllerProvider.notifier).canUseBiometricLogin();
    if (!mounted) return;
    setState(() => _biometricReady = canBio);

    if (!canBio) return;

    final result = await ref.read(authControllerProvider.notifier).tryBiometricLogin();
    if (!mounted) return;

    if (result == BiometricLoginResult.success) {
      _onAuthSuccess();
      return;
    }

    final stillCanBio = await ref.read(authControllerProvider.notifier).canUseBiometricLogin();
    if (!mounted) return;
    setState(() {
      _biometricReady = stillCanBio;
      if (result == BiometricLoginResult.sessionExpired) {
        _error = 'Session expired. Log in with your email and password.';
      }
    });
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _emailFocus.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    if (email.isEmpty || password.isEmpty) {
      setState(() => _error = 'Enter your email and password');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      await ref.read(authControllerProvider.notifier).loginWithEmail(
            email: email,
            password: password,
          );
      if (!mounted) return;
      final canBio = await ref.read(authControllerProvider.notifier).canUseBiometricLogin();
      if (!mounted) return;
      setState(() => _biometricReady = canBio);
      _onAuthSuccess();
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = dioErrorMessage(e);
        _loading = false;
      });
    }
  }

  String _biometricErrorMessage(BiometricLoginResult result) {
    return switch (result) {
      BiometricLoginResult.cancelled => 'Fingerprint not recognized. Use email and password.',
      BiometricLoginResult.sessionExpired =>
        'Session expired. Log in with your email and password.',
      BiometricLoginResult.notConfigured =>
        'Fingerprint login is not set up. Log in with password first.',
      BiometricLoginResult.success => '',
    };
  }

  Future<void> _biometric() async {
    if (!_biometricReady || _loading) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    final result = await ref.read(authControllerProvider.notifier).tryBiometricLogin();
    if (!mounted) return;

    if (result == BiometricLoginResult.success) {
      _onAuthSuccess();
      return;
    }

    final canBio = await ref.read(authControllerProvider.notifier).canUseBiometricLogin();
    if (!mounted) return;
    setState(() {
      _biometricReady = canBio;
      _error = _biometricErrorMessage(result);
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: PpFormScroll(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: AppSpacing.xl),
              const VeinPayLogo(size: VeinPayBrand.logoLg),
              const SizedBox(height: AppSpacing.md),
              Text('Welcome back', style: AppTextStyles.display(context), textAlign: TextAlign.center),
              const SizedBox(height: AppSpacing.md),
              PpScreenHeader(
                title: 'Sign in',
                subtitle: 'Log in to ${VeinPayBrand.appName}',
                centered: true,
              ),
              TextField(
                controller: _emailController,
                focusNode: _emailFocus,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
                autocorrect: false,
                enabled: !_loading,
                decoration: const InputDecoration(labelText: 'Email'),
                onSubmitted: (_) => _passwordFocus.requestFocus(),
              ),
              const SizedBox(height: AppSpacing.md),
              TextField(
                controller: _passwordController,
                focusNode: _passwordFocus,
                obscureText: _obscure,
                textInputAction: TextInputAction.done,
                enabled: !_loading,
                decoration: InputDecoration(
                  labelText: 'Password',
                  suffixIcon: IconButton(
                    icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
                onSubmitted: (_) => _submit(),
              ),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: _loading ? null : () => context.push(AppRoutes.forgotPassword),
                  child: const Text('Forgot password?'),
                ),
              ),
              if (_error != null) PpInlineErrorState(message: _error!),
              const SizedBox(height: AppSpacing.xl),
              PpButton(
                label: _loading ? 'Signing in...' : 'Log in',
                onPressed: _loading ? null : _submit,
              ),
              if (_biometricReady) ...[
                const SizedBox(height: AppSpacing.md),
                OutlinedButton.icon(
                  onPressed: _loading ? null : _biometric,
                  icon: const Icon(Icons.fingerprint),
                  label: const Text('Use fingerprint'),
                ),
              ],
              const SizedBox(height: AppSpacing.lg),
              TextButton(
                onPressed: _loading ? null : () => context.push(AppRoutes.signupDetails),
                child: Text('New to ${VeinPayBrand.appName}? Create account'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
