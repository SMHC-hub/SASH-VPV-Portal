import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../shared/widgets/pp_empty_state.dart';
import '../../../../shared/widgets/pp_screen_header.dart';
import '../../../../shared/widgets/pp_section_state.dart';
import '../../../../shared/widgets/pp_shimmer.dart';
import '../../domain/scan_models.dart';
import '../providers/scan_provider.dart';
import '../../../wallet/presentation/providers/wallet_provider.dart';

class ScanScreen extends ConsumerStatefulWidget {
  const ScanScreen({super.key});

  @override
  ConsumerState<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends ConsumerState<ScanScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(scanControllerProvider.notifier).startPolling(_onPaymentNotification);
    });
  }

  @override
  void dispose() {
    ref.read(scanControllerProvider.notifier).stopPolling();
    super.dispose();
  }

  void _onPaymentNotification(PalmPayNotification note) {
    if (!mounted) return;
    ref.read(walletControllerProvider.notifier).refresh();
    if (note.isSuccess) {
      context.push(AppRoutes.scanResultSuccess, extra: note);
    } else if (note.isLowBalance) {
      context.push(AppRoutes.scanResultLowBalance, extra: note);
    } else {
      context.push(AppRoutes.scanResultFailed, extra: note);
    }
  }

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = context.cs;
    final scanState = ref.watch(scanControllerProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Vein Pay')),
      body: RefreshIndicator(
        onRefresh: () => ref.read(scanControllerProvider.notifier).loadMerchants(),
        child: ListView(
            padding: const EdgeInsets.all(AppSpacing.lg),
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
          const PpScreenHeader(
            title: 'Pay with your palm',
            subtitle: 'Keep this tab open while paying at supported merchant kiosks.',
          ),
          Container(
            padding: const EdgeInsets.all(AppSpacing.lg),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: pp.balanceGradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.fingerprint, color: pp.onBalanceCard, size: 40),
                const SizedBox(height: AppSpacing.md),
                Text(
                  'Palm scan ready',
                  style: TextStyle(
                    color: pp.onBalanceCard,
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'At checkout, place your enrolled palm on the merchant kiosk scanner. '
                  'No phone, QR, or PIN needed.',
                  style: TextStyle(
                    color: pp.onBalanceCard.withValues(alpha: 0.85),
                    height: 1.45,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.xl),
          Row(
            children: [
              Text('Nearby merchants', style: AppTextStyles.title(context)),
              const Spacer(),
              if (scanState.polling)
                Row(
                  children: [
                    SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(strokeWidth: 2, color: pp.primary),
                    ),
                    const SizedBox(width: 6),
                    Text('Listening', style: AppTextStyles.label(context)),
                  ],
                ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          PpSectionState(
            loading: scanState.loadingMerchants,
            errorMessage: scanState.errorMessage,
            onRetry: () => ref.read(scanControllerProvider.notifier).loadMerchants(),
            isEmpty: scanState.merchants.isEmpty,
            loadingChild: const Column(
              children: [
                Padding(
                  padding: EdgeInsets.only(bottom: AppSpacing.sm),
                  child: PpShimmerBox(width: double.infinity, height: 72, borderRadius: 16),
                ),
                Padding(
                  padding: EdgeInsets.only(bottom: AppSpacing.sm),
                  child: PpShimmerBox(width: double.infinity, height: 72, borderRadius: 16),
                ),
                Padding(
                  padding: EdgeInsets.only(bottom: AppSpacing.sm),
                  child: PpShimmerBox(width: double.infinity, height: 72, borderRadius: 16),
                ),
              ],
            ),
            emptyChild: PpEmptyState(
              icon: Icons.store_outlined,
              title: 'No merchants nearby',
              message: 'Merchant kiosks will appear here when they are online.',
            ),
            child: Column(
              children: [
                ...scanState.merchants.map(
                  (m) => _MerchantTile(merchant: m),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: pp.discoverTint.withValues(alpha: cs.brightness == Brightness.dark ? 0.3 : 1),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: pp.border),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline, color: pp.primary, size: 20),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: Text(
                    'Keep this tab open while paying — you\'ll see the result here when the kiosk scan completes.',
                    style: AppTextStyles.label(context).copyWith(height: 1.4),
                  ),
                ),
              ],
            ),
          ),
        ],
        ),
      ),
    );
  }
}

class _MerchantTile extends StatelessWidget {
  const _MerchantTile({required this.merchant});

  final PalmMerchant merchant;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = context.cs;

    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: pp.border),
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: pp.primary.withValues(alpha: 0.15),
            child: Icon(Icons.storefront_outlined, color: pp.primary),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(merchant.name, style: AppTextStyles.title(context).copyWith(fontSize: 15)),
                Text(merchant.category, style: AppTextStyles.label(context)),
              ],
            ),
          ),
          Icon(Icons.near_me_outlined, size: 18, color: pp.textSecondary),
        ],
      ),
    );
  }
}
