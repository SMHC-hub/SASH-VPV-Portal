import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/veinpay_brand.dart';
import '../../../../core/security/secure_screen_service.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';
import '../../../onboarding/presentation/providers/onboarding_provider.dart';
import '../../domain/wallet_models.dart';
import '../../presentation/providers/wallet_provider.dart';
import '../../../../shared/widgets/animated_balance_text.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';
import '../../../../shared/widgets/pp_empty_state.dart';
import '../../../../shared/widgets/pp_shimmer.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  bool _hideBalance = false;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final walletState = ref.watch(walletControllerProvider);
    final auth = ref.watch(authControllerProvider);
    final onboarding = ref.watch(onboardingControllerProvider);
    final wallet = walletState.wallet;
    final balance = wallet?.balancePkr ?? auth.session?.balancePkr ?? 0;
    final sessionName = auth.session?.fullName ?? '';
    final profileName = onboarding.profile?.fullName ?? '';
    final name = sessionName.isNotEmpty
        ? sessionName
        : (profileName.isNotEmpty ? profileName : 'there');

    return SecureScreen(
      child: Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () => ref.read(walletControllerProvider.notifier).refresh(),
          child: ListView(
              padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.md, AppSpacing.lg, AppSpacing.lg),
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
              Text('Hello, $name', style: AppTextStyles.title(context)),
              if (walletState.error != null) ...[
                const SizedBox(height: AppSpacing.sm),
                PpInlineErrorState(
                  message: walletState.error!,
                  onRetry: () => ref.read(walletControllerProvider.notifier).refresh(),
                ),
              ],
              const SizedBox(height: AppSpacing.lg),
              LayoutBuilder(
                builder: (context, constraints) {
                  final compact = constraints.maxWidth < 340;
                  // "lac" subtitle appears from 100,000 — need a taller hero card.
                  final largeBalance = balance >= 100000;
                  final heroHeight = largeBalance
                      ? (compact ? 184.0 : 196.0)
                      : (compact ? 156.0 : 172.0);
                  return SizedBox(
                    height: heroHeight,
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Expanded(
                          flex: 3,
                          child: LayoutBuilder(
                            builder: (context, cardConstraints) {
                              return _BalanceCard(
                                balance: balance,
                                hidden: _hideBalance,
                                accountNumber: wallet?.accountNumber,
                                devPinHint: wallet?.devSpendingPinHint,
                                onToggleHide: () => setState(() => _hideBalance = !_hideBalance),
                                compact: compact,
                                maxTextWidth: cardConstraints.maxWidth - (AppSpacing.md * 2),
                              );
                            },
                          ),
                        ),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(
                          flex: 2,
                          child: Column(
                            children: [
                              Expanded(
                                child: _ActionTile(
                                  labelLines: const ['Load Money'],
                                  icon: Icons.arrow_downward_rounded,
                                  color: pp.accent,
                                  onTap: () => context.push(AppRoutes.addMoney),
                                ),
                              ),
                              const SizedBox(height: AppSpacing.sm),
                              Expanded(
                                child: _ActionTile(
                                  labelLines: const ['Send'],
                                  icon: Icons.arrow_outward_rounded,
                                  color: pp.primary,
                                  onTap: () => context.push(AppRoutes.sendMoney),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
              const SizedBox(height: AppSpacing.xl),
              Row(
                children: [
                  Text('Transactions', style: AppTextStyles.title(context)),
                  const Spacer(),
                  TextButton(
                    onPressed: () => context.push(AppRoutes.transactions),
                    child: Text('See all', style: TextStyle(color: pp.primary)),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.xs),
              if (walletState.loading && walletState.transactions.isEmpty)
                const Column(
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
                )
              else if (walletState.transactions.isEmpty)
                PpEmptyState(
                  icon: Icons.receipt_long_outlined,
                  title: 'No transactions yet',
                  message: 'Load money or pay with your palm to see activity here.',
                  actionLabel: 'Load money',
                  onAction: () => context.push(AppRoutes.addMoney),
                )
              else
                ...walletState.transactions.map((tx) => _TxCard(transaction: tx)),
              const SizedBox(height: AppSpacing.xl),
              Row(
                children: [
                  Text('Discover', style: AppTextStyles.title(context)),
                  const SizedBox(width: 6),
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(color: pp.primary, shape: BoxShape.circle),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
              SizedBox(
                height: 120,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    _DiscoverCard(
                      title: 'Welcome to ${VeinPayBrand.appName}',
                      subtitle: 'Palm vein payments made simple',
                      tint: pp.discoverTint,
                    ),
                    _DiscoverCard(
                      title: 'Load money',
                      subtitle: 'Top up via JazzCash',
                      tint: pp.discoverTint,
                      onTap: () => context.push(AppRoutes.addMoney),
                    ),
                    _DiscoverCard(
                      title: 'Enroll palm',
                      subtitle: 'Pay at merchant kiosks',
                      tint: pp.discoverTint,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
      ),
    );
  }
}

class _BalanceCard extends StatelessWidget {
  const _BalanceCard({
    required this.balance,
    required this.hidden,
    required this.onToggleHide,
    required this.maxTextWidth,
    this.accountNumber,
    this.devPinHint,
    this.compact = false,
  });

  final double balance;
  final bool hidden;
  final VoidCallback onToggleHide;
  final double maxTextWidth;
  final String? accountNumber;
  final String? devPinHint;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;

    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: pp.balanceGradient,
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(color: pp.shadow, blurRadius: 20, offset: const Offset(0, 8)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.credit_card, color: pp.onBalanceCard.withValues(alpha: 0.9), size: 18),
              const Spacer(),
              IconButton(
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
                onPressed: onToggleHide,
                icon: Icon(
                  hidden ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                  color: pp.onBalanceCard.withValues(alpha: 0.9),
                  size: 20,
                ),
              ),
            ],
          ),
          const Spacer(),
          AnimatedBalanceText(
            amount: balance,
            hidden: hidden,
            prefix: 'Rs. ',
            maxWidth: maxTextWidth,
            animate: true,
            style: TextStyle(
              fontSize: compact ? 22 : 26,
              fontWeight: FontWeight.w700,
              color: pp.onBalanceCard,
              letterSpacing: -0.5,
            ),
          ),
          if (accountNumber != null) ...[
            const SizedBox(height: 4),
            Text(
              accountNumber!,
              style: TextStyle(fontSize: 10, color: pp.onBalanceCard.withValues(alpha: 0.7)),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ],
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.labelLines,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  final List<String> labelLines;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  static const _labelStyle = TextStyle(
    color: Colors.white,
    fontWeight: FontWeight.w600,
    fontSize: 12.5,
    height: 1.22,
    letterSpacing: -0.2,
  );

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(20),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: SizedBox.expand(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 10, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Icon(icon, color: Colors.white, size: 22),
                Text(
                  labelLines.join(' '),
                  style: _labelStyle,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TxCard extends StatelessWidget {
  const _TxCard({required this.transaction});

  final WalletTransaction transaction;

  @override
  Widget build(BuildContext context) {
    final tx = transaction;
    final pp = context.pp;
    final cs = context.cs;
    final sign = tx.isIncoming ? '+' : '-';
    final amountColor = tx.isIncoming ? pp.primary : cs.onSurface;

    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.sm),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: pp.border),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 20,
            backgroundColor: pp.surfaceElevated,
            child: Icon(
              tx.isIncoming ? Icons.arrow_downward : Icons.arrow_upward,
              size: 18,
              color: tx.isIncoming ? pp.primary : pp.accent,
            ),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tx.counterpartyName,
                  style: AppTextStyles.title(context).copyWith(fontSize: 15),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  tx.description,
                  style: AppTextStyles.label(context),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Text(
            '$sign Rs. ${tx.amountPkr.toStringAsFixed(0)}',
            style: AppTextStyles.title(context).copyWith(fontSize: 14, color: amountColor),
          ),
        ],
      ),
    );
  }
}

class _DiscoverCard extends StatelessWidget {
  const _DiscoverCard({
    required this.title,
    required this.subtitle,
    required this.tint,
    this.onTap,
  });

  final String title;
  final String subtitle;
  final Color tint;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = context.cs;

    return Padding(
      padding: const EdgeInsets.only(right: AppSpacing.sm),
      child: Material(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Container(
            width: 200,
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              border: Border.all(color: pp.border),
              borderRadius: BorderRadius.circular(16),
              gradient: LinearGradient(
                colors: [tint, cs.surface],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: AppTextStyles.title(context).copyWith(fontSize: 15)),
                const SizedBox(height: 4),
                Expanded(
                  child: Text(subtitle, style: AppTextStyles.label(context), maxLines: 2),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
