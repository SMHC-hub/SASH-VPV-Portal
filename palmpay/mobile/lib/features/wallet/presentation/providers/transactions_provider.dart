import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/network_exceptions.dart';
import '../../data/wallet_repository.dart';
import '../../domain/wallet_models.dart';

class TransactionsFilter {
  const TransactionsFilter({
    this.direction,
    this.txType,
    this.search,
  });

  final String? direction;
  final String? txType;
  final String? search;

  TransactionsFilter copyWith({
    String? direction,
    String? txType,
    String? search,
    bool clearDirection = false,
    bool clearTxType = false,
    bool clearSearch = false,
  }) {
    return TransactionsFilter(
      direction: clearDirection ? null : (direction ?? this.direction),
      txType: clearTxType ? null : (txType ?? this.txType),
      search: clearSearch ? null : (search ?? this.search),
    );
  }
}

class TransactionsState {
  const TransactionsState({
    this.items = const [],
    this.loading = false,
    this.loadingMore = false,
    this.error,
    this.hasMore = true,
    this.total = 0,
    this.filter = const TransactionsFilter(),
  });

  final List<WalletTransaction> items;
  final bool loading;
  final bool loadingMore;
  final String? error;
  final bool hasMore;
  final int total;
  final TransactionsFilter filter;

  TransactionsState copyWith({
    List<WalletTransaction>? items,
    bool? loading,
    bool? loadingMore,
    String? error,
    bool? hasMore,
    int? total,
    TransactionsFilter? filter,
  }) {
    return TransactionsState(
      items: items ?? this.items,
      loading: loading ?? this.loading,
      loadingMore: loadingMore ?? this.loadingMore,
      error: error,
      hasMore: hasMore ?? this.hasMore,
      total: total ?? this.total,
      filter: filter ?? this.filter,
    );
  }
}

class TransactionsController extends StateNotifier<TransactionsState> {
  TransactionsController(this._repo) : super(const TransactionsState());

  final WalletRepository _repo;
  static const _pageSize = 20;

  Future<void> refresh({TransactionsFilter? filter}) async {
    final nextFilter = filter ?? state.filter;
    state = state.copyWith(loading: true, error: null, filter: nextFilter, items: []);
    try {
      final page = await _repo.fetchTransactions(
        limit: _pageSize,
        direction: nextFilter.direction,
        txType: nextFilter.txType,
        search: nextFilter.search,
      );
      state = state.copyWith(
        loading: false,
        items: page.items,
        hasMore: page.hasMore,
        total: page.total,
      );
    } catch (e) {
      state = state.copyWith(loading: false, error: userFacingError(e));
    }
  }

  Future<void> loadMore() async {
    if (state.loading || state.loadingMore || !state.hasMore) return;
    state = state.copyWith(loadingMore: true, error: null);
    try {
      final page = await _repo.fetchTransactions(
        offset: state.items.length,
        limit: _pageSize,
        direction: state.filter.direction,
        txType: state.filter.txType,
        search: state.filter.search,
      );
      state = state.copyWith(
        loadingMore: false,
        items: [...state.items, ...page.items],
        hasMore: page.hasMore,
        total: page.total,
      );
    } catch (e) {
      state = state.copyWith(loadingMore: false, error: userFacingError(e));
    }
  }
}

final transactionsControllerProvider =
    StateNotifierProvider<TransactionsController, TransactionsState>((ref) {
  return TransactionsController(ref.watch(walletRepositoryProvider));
});

final analyticsSummaryProvider = FutureProvider.family<AnalyticsSummary, String>((ref, period) {
  return ref.watch(walletRepositoryProvider).fetchAnalyticsSummary(period: period);
});

final transactionDetailProvider = FutureProvider.family<WalletTransactionDetail, String>((ref, reference) {
  return ref.watch(walletRepositoryProvider).fetchTransactionDetail(reference);
});
