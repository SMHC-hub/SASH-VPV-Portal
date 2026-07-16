import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/security/secure_screen_service.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_form_scroll.dart';
import '../../../../shared/widgets/pp_pin_input.dart';
import '../../../../shared/widgets/pp_screen_header.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';
import '../../data/wallet_repository.dart';
import '../../domain/wallet_models.dart';
import '../../presentation/providers/wallet_provider.dart';

class SendConfirmScreen extends ConsumerStatefulWidget {
  const SendConfirmScreen({super.key, this.preview});

  final TransferPreview? preview;

  @override
  ConsumerState<SendConfirmScreen> createState() => _SendConfirmScreenState();
}

class _SendConfirmScreenState extends ConsumerState<SendConfirmScreen> {
  final _pinController = TextEditingController();
  bool _loading = false;
  String? _error;

  Future<void> _confirm([String? pin]) async {
    final preview = widget.preview;
    if (preview == null) return;
    final spendingPin = pin ?? _pinController.text;
    if (spendingPin.length < 4) return;

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final newBalance = await ref.read(walletRepositoryProvider).confirmTransfer(
            transferReference: preview.transferReference,
            spendingPin: spendingPin,
          );
      if (!mounted) return;
      ref.read(walletControllerProvider.notifier).setOptimisticBalance(newBalance);
      // Refresh off the critical path — setState after go() races Flutter element lifecycle.
      // ignore: unawaited_futures
      ref.read(walletControllerProvider.notifier).refresh();
      if (!mounted) return;
      context.go(AppRoutes.transferSuccess, extra: preview);
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() {
        _error = dioErrorMessage(e);
        _loading = false;
      });
    }
  }

  @override
  void dispose() {
    _pinController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final preview = widget.preview;
    final wallet = ref.watch(walletControllerProvider).wallet;

    if (preview == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Confirm transfer')),
        body: const Center(child: Text('Missing transfer preview')),
      );
    }

    return SecureScreen(
      child: Scaffold(
        appBar: AppBar(title: const Text('Confirm transfer')),
        body: PpFormScroll(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const PpScreenHeader(
                title: 'Review transfer',
                subtitle: 'Confirm recipient, amount, and PIN before sending.',
              ),
              _Row(label: 'To', value: preview.recipientName),
              _Row(label: 'Phone', value: preview.recipientPhoneMasked),
              _Row(label: 'Amount', value: 'PKR ${preview.amountPkr.toStringAsFixed(2)}'),
              _Row(label: 'Fee', value: 'PKR ${preview.feePkr.toStringAsFixed(2)}'),
              _Row(label: 'Total', value: 'PKR ${preview.totalDebitPkr.toStringAsFixed(2)}'),
              if (preview.note != null && preview.note!.isNotEmpty) _Row(label: 'Note', value: preview.note!),
              const SizedBox(height: AppSpacing.xl),
              Text('Enter spending PIN', style: AppTextStyles.title(context)),
              if (wallet?.devSpendingPinHint != null) ...[
                const SizedBox(height: AppSpacing.xs),
                Text('Dev PIN: ${wallet!.devSpendingPinHint}', style: AppTextStyles.label(context)),
              ],
              const SizedBox(height: AppSpacing.md),
              Center(
                child: PpPinInput(
                  controller: _pinController,
                  onCompleted: _confirm,
                ),
              ),
              if (_error != null) PpInlineErrorState(message: _error!),
              const SizedBox(height: AppSpacing.xl),
              PpButton(
                label: _loading ? 'Sending…' : 'Confirm send',
                onPressed: _loading ? null : () => _confirm(),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        children: [
          SizedBox(width: 80, child: Text(label, style: AppTextStyles.label(context))),
          Expanded(child: Text(value, style: AppTextStyles.body(context))),
        ],
      ),
    );
  }
}
