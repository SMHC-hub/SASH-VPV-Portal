import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../shared/widgets/pp_empty_state.dart';
import '../../../../shared/widgets/pp_error_state.dart';
import '../../../../shared/widgets/pp_shimmer.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';
import '../../domain/wallet_models.dart';
import '../providers/transactions_provider.dart';

String _formatWhen(String iso) {
  try {
    final d = DateTime.parse(iso);
    return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year} '
        '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
  } catch (_) {
    return iso;
  }
}

String _typeLabel(String txType) {
  return switch (txType) {
    'topup' => 'Top-up',
    'transfer' => 'Transfer',
    'palm_pay' => 'Vein Pay',
    _ => txType.replaceAll('_', ' '),
  };
}

class TransactionHistoryScreen extends ConsumerStatefulWidget {
  const TransactionHistoryScreen({super.key});

  @override
  ConsumerState<TransactionHistoryScreen> createState() => _TransactionHistoryScreenState();
}

class _TransactionHistoryScreenState extends ConsumerState<TransactionHistoryScreen> {
  final _scrollController = ScrollController();
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(transactionsControllerProvider.notifier).refresh();
    });
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 200) {
      ref.read(transactionsControllerProvider.notifier).loadMore();
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _openFilters() async {
    final current = ref.read(transactionsControllerProvider).filter;
    final direction = await showModalBottomSheet<String?>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                title: const Text('All directions'),
                trailing: current.direction == null ? const Icon(Icons.check) : null,
                onTap: () => Navigator.pop(context, null),
              ),
              ListTile(
                title: const Text('Money in'),
                trailing: current.direction == 'in' ? const Icon(Icons.check) : null,
                onTap: () => Navigator.pop(context, 'in'),
              ),
              ListTile(
                title: const Text('Money out'),
                trailing: current.direction == 'out' ? const Icon(Icons.check) : null,
                onTap: () => Navigator.pop(context, 'out'),
              ),
            ],
          ),
        );
      },
    );
    if (!mounted || direction == current.direction) return;
    await ref.read(transactionsControllerProvider.notifier).refresh(
          filter: current.copyWith(direction: direction, clearDirection: direction == null),
        );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(transactionsControllerProvider);
    final pp = context.pp;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Transactions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _openFilters,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, 0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search reference or description',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _searchController.clear();
                    ref.read(transactionsControllerProvider.notifier).refresh(
                          filter: state.filter.copyWith(clearSearch: true),
                        );
                  },
                ),
              ),
              onSubmitted: (value) {
                ref.read(transactionsControllerProvider.notifier).refresh(
                      filter: state.filter.copyWith(search: value.trim()),
                    );
              },
            ),
          ),
          if (state.total > 0)
            Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text('${state.total} transactions', style: AppTextStyles.label(context)),
              ),
            ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: () => ref.read(transactionsControllerProvider.notifier).refresh(),
              child: _buildBody(context, state, pp),
            ),
          ),
          ],
        ),
    );
  }

  Widget _buildBody(BuildContext context, TransactionsState state, PalmPayPalette pp) {
    if (state.loading && state.items.isEmpty) {
      return const PpTransactionListSkeleton();
    }
    if (state.error != null && state.items.isEmpty) {
      return ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          PpErrorState(
            message: state.error!,
            onRetry: () => ref.read(transactionsControllerProvider.notifier).refresh(),
          ),
        ],
      );
    }
    if (state.items.isEmpty) {
      return ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: [
          PpEmptyState(
            icon: Icons.receipt_long_outlined,
            title: 'No transactions yet',
            message: 'Load money or pay with your palm to see activity here.',
          ),
        ],
      );
    }

    return ListView.builder(
      controller: _scrollController,
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
      itemCount: state.items.length + (state.loadingMore ? 1 : 0) + (state.error != null ? 1 : 0),
      itemBuilder: (context, index) {
        if (state.error != null && index == 0) {
          return PpInlineErrorState(
            message: state.error!,
            onRetry: () => ref.read(transactionsControllerProvider.notifier).refresh(),
          );
        }
        final itemIndex = state.error != null ? index - 1 : index;
        if (itemIndex >= state.items.length) {
          return const Padding(
            padding: EdgeInsets.all(AppSpacing.lg),
            child: PpShimmerBox(width: double.infinity, height: 72, borderRadius: 16),
          );
        }
        final tx = state.items[itemIndex];
        return _TransactionTile(
          transaction: tx,
          onTap: () => context.push(AppRoutes.transactionDetail(tx.reference)),
        );
      },
    );
  }
}

class _TransactionTile extends StatelessWidget {
  const _TransactionTile({required this.transaction, required this.onTap});

  final WalletTransaction transaction;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = context.cs;
    final sign = transaction.isIncoming ? '+' : '-';
    final amountColor = transaction.isIncoming ? pp.primary : cs.onSurface;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
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
                transaction.isIncoming ? Icons.arrow_downward : Icons.arrow_upward,
                size: 18,
                color: transaction.isIncoming ? pp.primary : pp.accent,
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    transaction.counterpartyName,
                    style: AppTextStyles.title(context).copyWith(fontSize: 15),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    '${_typeLabel(transaction.txType)} · ${_formatWhen(transaction.createdAt)}',
                    style: AppTextStyles.label(context),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            Text(
              '$sign Rs. ${transaction.amountPkr.toStringAsFixed(0)}',
              style: AppTextStyles.title(context).copyWith(fontSize: 14, color: amountColor),
            ),
          ],
        ),
      ),
    );
  }
}
