import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../core/security/secure_screen_service.dart';
import '../../../../shared/widgets/pp_error_state.dart';
import '../../../../shared/widgets/pp_shimmer.dart';
import '../../domain/wallet_models.dart';
import '../providers/transactions_provider.dart';
class TransactionDetailScreen extends ConsumerWidget {
  const TransactionDetailScreen({super.key, required this.reference});

  final String reference;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(transactionDetailProvider(reference));
    final pp = context.pp;

    return SecureScreen(
      child: Scaffold(
        appBar: AppBar(title: const Text('Receipt')),
        body: async.when(
            loading: () => const PpReceiptSkeleton(),
            error: (e, _) => PpErrorState(
              message: userFacingError(e),
              onRetry: () => ref.invalidate(transactionDetailProvider(reference)),
            ),
            data: (WalletTransactionDetail detail) {
              final sign = detail.isIncoming ? '+' : '-';
              return ListView(
                padding: const EdgeInsets.all(AppSpacing.lg),
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(AppSpacing.lg),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(colors: pp.balanceGradient),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Amount', style: AppTextStyles.label(context).copyWith(color: pp.onBalanceCard)),
                        const SizedBox(height: AppSpacing.xs),
                        Text(
                          '$sign Rs. ${detail.amountPkr.toStringAsFixed(2)}',
                          style: AppTextStyles.display(context).copyWith(color: pp.onBalanceCard, fontSize: 32),
                        ),
                        const SizedBox(height: AppSpacing.sm),
                        Text(
                          detail.description,
                          style: AppTextStyles.body(context).copyWith(color: pp.onBalanceCard),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  _DetailRow(label: 'Reference', value: detail.reference),
                  _DetailRow(label: 'Type', value: detail.txType.replaceAll('_', ' ')),
                  _DetailRow(label: 'Counterparty', value: detail.counterpartyName),
                  _DetailRow(label: 'Direction', value: detail.isIncoming ? 'Received' : 'Sent'),
                  _DetailRow(label: 'Status', value: detail.status),
                  if (detail.topupMethod != null) _DetailRow(label: 'Method', value: detail.topupMethod!),
                  _DetailRow(label: 'Created', value: detail.createdAt),
                  if (detail.completedAt != null) _DetailRow(label: 'Completed', value: detail.completedAt!),
                ],
              );
            },
          ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 110, child: Text(label, style: AppTextStyles.label(context))),
          Expanded(child: Text(value, style: AppTextStyles.body(context))),
        ],
      ),
    );
  }
}
