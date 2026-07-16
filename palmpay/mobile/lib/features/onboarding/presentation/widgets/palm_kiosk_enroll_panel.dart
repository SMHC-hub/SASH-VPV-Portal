import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../data/auth_repository.dart';
import '../../domain/onboarding_models.dart';
import '../providers/onboarding_provider.dart';

/// Shows kiosk enrollment code + QR until palm is registered on the web kiosk.
class PalmKioskEnrollPanel extends ConsumerStatefulWidget {
  const PalmKioskEnrollPanel({super.key, this.compact = false});

  final bool compact;

  @override
  ConsumerState<PalmKioskEnrollPanel> createState() => _PalmKioskEnrollPanelState();
}

class _PalmKioskEnrollPanelState extends ConsumerState<PalmKioskEnrollPanel> {
  EnrollmentSession? _session;
  bool _loading = false;
  bool _codeVisible = false;
  String? _error;
  Timer? _pollTimer;

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _showCode() async {
    setState(() {
      _loading = true;
      _error = null;
      _codeVisible = true;
    });
    try {
      final session = await ref.read(authRepositoryProvider).initiateEnrollment();
      if (!mounted) return;
      setState(() => _session = session);
      _pollTimer?.cancel();
      _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _poll());
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _poll() async {
    try {
      final status = await ref.read(authRepositoryProvider).fetchEnrollmentStatus();
      if (!mounted) return;
      if (status.palmEnrolled || status.status == 'complete') {
        _pollTimer?.cancel();
        await ref.read(onboardingControllerProvider.notifier).refresh();
        if (!mounted) return;
        context.go(AppRoutes.enrollSuccess);
      }
    } catch (_) {}
  }

  Future<void> _copyCode() async {
    final code = _session?.sessionCode;
    if (code == null) return;
    await Clipboard.setData(ClipboardData(text: code));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Enrollment code copied')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = context.cs;

    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: pp.primary.withValues(alpha: 0.45)),
        boxShadow: [
          BoxShadow(
            color: pp.primary.withValues(alpha: 0.08),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: pp.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(Icons.fingerprint, color: pp.primary, size: 28),
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Enroll your palm', style: AppTextStyles.title(context)),
                    const SizedBox(height: 2),
                    Text(
                      'Complete palm vein registration at a web kiosk whenever you are ready.',
                      style: AppTextStyles.label(context).copyWith(height: 1.35),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          Text(
            'On the PC open Web Kiosk (or /kiosk/enroll), enter the code below, then scan both palms.',
            style: AppTextStyles.body(context).copyWith(fontSize: 13, height: 1.4),
          ),
          if (_error != null) ...[
            const SizedBox(height: AppSpacing.sm),
            Text(_error!, style: TextStyle(color: cs.error, fontSize: 13)),
          ],
          const SizedBox(height: AppSpacing.md),
          if (!_codeVisible)
            PpButton(
              label: 'Get enrollment code',
              onPressed: _loading ? null : _showCode,
            )
          else if (_loading && _session == null)
            const Center(child: Padding(
              padding: EdgeInsets.all(AppSpacing.md),
              child: CircularProgressIndicator(),
            ))
          else if (_session != null) ...[
            if (!widget.compact)
              Center(
                child: QrImageView(
                  data: _session!.qrPayload,
                  size: 168,
                  backgroundColor: Colors.white,
                ),
              ),
            const SizedBox(height: AppSpacing.md),
            Container(
              padding: const EdgeInsets.symmetric(vertical: AppSpacing.md, horizontal: AppSpacing.lg),
              decoration: BoxDecoration(
                color: pp.discoverTint.withValues(alpha: cs.brightness == Brightness.dark ? 0.35 : 1),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: pp.border),
              ),
              child: Column(
                children: [
                  Text('Enrollment code', style: AppTextStyles.label(context)),
                  const SizedBox(height: 4),
                  Text(
                    _session!.sessionCode,
                    style: AppTextStyles.title(context).copyWith(
                      fontSize: 28,
                      letterSpacing: 3,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            const LinearProgressIndicator(),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Waiting for kiosk… keep this screen open',
              style: AppTextStyles.label(context),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _copyCode,
                    child: const Text('Copy code'),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: OutlinedButton(
                    onPressed: _loading ? null : _showCode,
                    child: const Text('Refresh'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
