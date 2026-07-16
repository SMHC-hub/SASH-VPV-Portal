import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../onboarding/data/auth_repository.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';

/// Shared Google button for login / signup. Hidden when server has no client id.
class GoogleAuthButton extends ConsumerStatefulWidget {
  const GoogleAuthButton({
    super.key,
    required this.intent,
    this.onSuccess,
    this.onError,
    this.disabled = false,
  });

  final String intent; // login | signup
  final VoidCallback? onSuccess;
  final ValueChanged<String>? onError;
  final bool disabled;

  @override
  ConsumerState<GoogleAuthButton> createState() => _GoogleAuthButtonState();
}

class _GoogleAuthButtonState extends ConsumerState<GoogleAuthButton> {
  bool _loading = false;
  bool? _enabled;
  String? _clientId;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadConfig());
  }

  Future<void> _loadConfig() async {
    try {
      final cfg = await ref.read(authRepositoryProvider).fetchGoogleConfig();
      if (!mounted) return;
      setState(() {
        _enabled = cfg.enabled && (cfg.clientId?.isNotEmpty ?? false);
        _clientId = cfg.clientId;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _enabled = false);
    }
  }

  Future<void> _tap() async {
    if (widget.disabled || _loading || _clientId == null) return;
    setState(() => _loading = true);
    try {
      final googleSignIn = GoogleSignIn(
        scopes: const ['email', 'profile'],
        serverClientId: _clientId,
      );
      await googleSignIn.signOut();
      final account = await googleSignIn.signIn();
      if (account == null) {
        if (mounted) setState(() => _loading = false);
        return;
      }
      final auth = await account.authentication;
      final idToken = auth.idToken;
      if (idToken == null || idToken.isEmpty) {
        throw StateError(
          'Google did not return an ID token. Add this Android app in Google Cloud Console '
          '(package pk.palmpay.palmpay + SHA-1) and use the Web client ID as serverClientId.',
        );
      }
      await ref.read(authControllerProvider.notifier).loginWithGoogle(
            credential: idToken,
            intent: widget.intent,
          );
      if (!mounted) return;
      widget.onSuccess?.call();
    } on DioException catch (e) {
      widget.onError?.call(dioErrorMessage(e));
    } catch (e) {
      widget.onError?.call(e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_enabled == false) return const SizedBox.shrink();
    if (_enabled == null) {
      return const SizedBox(height: 48);
    }

    final label = widget.intent == 'signup'
        ? (_loading ? 'Creating account…' : 'Continue with Google')
        : (_loading ? 'Signing in…' : 'Continue with Google');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        OutlinedButton(
          onPressed: (widget.disabled || _loading) ? null : _tap,
          style: OutlinedButton.styleFrom(
            minimumSize: const Size.fromHeight(52),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (_loading)
                const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              else
                const Icon(Icons.g_mobiledata, size: 28),
              const SizedBox(width: AppSpacing.sm),
              Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
            ],
          ),
        ),
      ],
    );
  }
}
