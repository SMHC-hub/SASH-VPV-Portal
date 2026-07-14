import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/network/network_exceptions.dart';
import '../../data/wallet_repository.dart';
import '../../domain/wallet_models.dart';

class WalletState {
  const WalletState({
    required this.loading,
    this.wallet,
    this.transactions = const [],
    this.recentContacts = const [],
    this.error,
  });

  final bool loading;
  final WalletInfo? wallet;
  final List<WalletTransaction> transactions;
  final List<RecentContact> recentContacts;
  final String? error;

  WalletState copyWith({
    bool? loading,
    WalletInfo? wallet,
    List<WalletTransaction>? transactions,
    List<RecentContact>? recentContacts,
    String? error,
  }) {
    return WalletState(
      loading: loading ?? this.loading,
      wallet: wallet ?? this.wallet,
      transactions: transactions ?? this.transactions,
      recentContacts: recentContacts ?? this.recentContacts,
      error: error,
    );
  }
}

class RecentContact {
  const RecentContact({
    required this.fullName,
    required this.phone,
  });

  final String fullName;
  final String phone;
}

class WalletController extends StateNotifier<WalletState> {
  WalletController(this._repo) : super(const WalletState(loading: true)) {
    refresh();
  }

  final WalletRepository _repo;

  Future<void> refresh() async {
    state = state.copyWith(loading: true, error: null);
    try {
      final wallet = await _repo.fetchWallet();
      final txs = await _repo.fetchRecentTransactions();
      state = state.copyWith(loading: false, wallet: wallet, transactions: txs);
    } catch (e) {
      state = state.copyWith(loading: false, error: userFacingError(e));
    }
  }

  Future<void> updatePerTxnLimit(double perTxnLimitPkr) async {
    final updated = await _repo.updateWalletLimit(perTxnLimitPkr);
    state = state.copyWith(wallet: updated, error: null);
  }

  Future<void> updateWalletSettings({bool? isFrozen, bool? palmPayEnabled}) async {
    final updated = await _repo.updateWalletSettings(
      isFrozen: isFrozen,
      palmPayEnabled: palmPayEnabled,
    );
    state = state.copyWith(wallet: updated, error: null);
  }

  void setOptimisticBalance(double balance) {
    final w = state.wallet;
    if (w == null) return;
    state = state.copyWith(
      wallet: WalletInfo(
        accountNumber: w.accountNumber,
        balancePkr: balance,
        isFrozen: w.isFrozen,
        perTxnLimitPkr: w.perTxnLimitPkr,
        dailyTransferLimitPkr: w.dailyTransferLimitPkr,
        palmPayEnabled: w.palmPayEnabled,
        spendingPinSet: w.spendingPinSet,
        devSpendingPinHint: w.devSpendingPinHint,
      ),
    );
  }

  void addRecentContact(RecentContact contact) {
    final existing = state.recentContacts.where((c) => c.phone != contact.phone).toList();
    state = state.copyWith(recentContacts: [contact, ...existing].take(5).toList());
  }
}

final walletControllerProvider =
    StateNotifierProvider<WalletController, WalletState>((ref) {
  return WalletController(ref.watch(walletRepositoryProvider));
});
