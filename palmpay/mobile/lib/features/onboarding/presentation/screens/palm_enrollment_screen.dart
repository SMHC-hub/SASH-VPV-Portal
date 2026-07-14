import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_section_state.dart';
import '../../../../shared/widgets/pp_shimmer.dart';
import '../../data/auth_repository.dart';
import '../../domain/onboarding_models.dart';
import '../../presentation/providers/onboarding_provider.dart';

class PalmEnrollmentScreen extends ConsumerStatefulWidget {
  const PalmEnrollmentScreen({super.key});

  @override
  ConsumerState<PalmEnrollmentScreen> createState() => _PalmEnrollmentScreenState();
}

class _PalmEnrollmentScreenState extends ConsumerState<PalmEnrollmentScreen> {
  EnrollmentSession? _session;
  bool _loading = true;
  String? _error;
  Timer? _pollTimer;

  @override
  void initState() {
    super.initState();
    _start();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _start() async {
    setState(() {
      _loading = true;
      _error = null;
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

  Future<void> _simulateKiosk() async {
    final code = _session?.sessionCode;
    if (code == null) return;
    setState(() => _loading = true);
    try {
      await ref.read(authRepositoryProvider).devCompleteEnrollment(code);
      await ref.read(onboardingControllerProvider.notifier).refresh();
      if (!mounted) return;
      context.go(AppRoutes.enrollSuccess);
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Palm enrollment')),
      body: PpSectionState(
        loading: _loading && _session == null,
        errorMessage: _error,
        onRetry: _start,
        isEmpty: false,
        emptyChild: const SizedBox.shrink(),
        loadingChild: const Padding(
          padding: EdgeInsets.all(AppSpacing.lg),
          child: PpHomeSkeleton(),
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            children: [
              Text('Enroll at web kiosk', style: AppTextStyles.title(context)),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'On the PC kiosk open /kiosk/enroll and type this code '
                '(or scan the QR). Keep this screen open until enrollment finishes.',
                style: AppTextStyles.body(context),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: AppSpacing.lg),
              if (_session != null) ...[
                QrImageView(
                  data: _session!.qrPayload,
                  size: 200,
                  backgroundColor: Colors.white,
                ),
                const SizedBox(height: AppSpacing.md),
                Text('Code: ${_session!.sessionCode}', style: AppTextStyles.title(context)),
                const SizedBox(height: AppSpacing.lg),
                const LinearProgressIndicator(color: AppColors.primary),
                const SizedBox(height: AppSpacing.sm),
                Text('Waiting for kiosk…', style: AppTextStyles.label(context)),
              ],
              const SizedBox(height: AppSpacing.xl),
              PpButton(
                label: 'Simulate kiosk (dev)',
                onPressed: _loading ? null : _simulateKiosk,
              ),
              const SizedBox(height: AppSpacing.sm),
              TextButton(onPressed: _start, child: const Text('Refresh code')),
            ],
          ),
        ),
      ),
    );
  }
}
