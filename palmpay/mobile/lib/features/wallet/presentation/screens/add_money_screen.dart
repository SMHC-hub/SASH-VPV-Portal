import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/security/secure_screen_service.dart';
import '../../../../core/utils/pkr_format.dart';
import '../../../../shared/widgets/pp_amount_field.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_form_scroll.dart';
import '../../../../shared/widgets/pp_screen_header.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';
import '../../data/wallet_repository.dart';
import '../../presentation/providers/wallet_provider.dart';

class AddMoneyScreen extends ConsumerStatefulWidget {
  const AddMoneyScreen({super.key});

  @override
  ConsumerState<AddMoneyScreen> createState() => _AddMoneyScreenState();
}

class _AddMoneyScreenState extends ConsumerState<AddMoneyScreen> {
  final _amountController = TextEditingController(text: '1000');
  bool _loading = false;
  String? _error;
  String? _orderReference;
  String? _checkoutUrl;

  @override
  void initState() {
    super.initState();
    final initial = PkrFormat.parseAmount(_amountController.text);
    if (initial != null) {
      _amountController.text = PkrFormat.amount(initial, showDecimals: false);
    }
  }

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  double? _parseAmount() {
    final v = PkrFormat.parseAmount(_amountController.text);
    if (v == null || v < 100) return null;
    return v;
  }

  Future<void> _initiateCheckout() async {
    final amount = _parseAmount();
    if (amount == null) {
      setState(() => _error = 'Enter at least PKR 100');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref.read(walletRepositoryProvider).initiateTopUp(amount);
      if (!mounted) return;
      setState(() {
        _orderReference = result.orderReference;
        _checkoutUrl = result.checkoutUrl;
      });
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => _JazzCashWebView(
            checkoutUrl: result.checkoutUrl,
            onClosed: () => _completeIfPaid(result.orderReference),
          ),
        ),
      );
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _simulatePayment() async {
    final amount = _parseAmount();
    if (amount == null) {
      setState(() => _error = 'Enter at least PKR 100');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final init = await ref.read(walletRepositoryProvider).initiateTopUp(amount);
      final balance = await ref.read(walletRepositoryProvider).simulateTopUpExisting(init.orderReference);
      ref.read(walletControllerProvider.notifier).setOptimisticBalance(balance);
      await ref.read(walletControllerProvider.notifier).refresh();
      if (!mounted) return;
      context.go(AppRoutes.topUpSuccess, extra: amount);
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _completeIfPaid(String orderReference) async {
    try {
      final balance = await ref.read(walletRepositoryProvider).simulateTopUpExisting(orderReference);
      ref.read(walletControllerProvider.notifier).setOptimisticBalance(balance);
      await ref.read(walletControllerProvider.notifier).refresh();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Wallet updated')),
      );
      context.pop();
    } catch (_) {
      await ref.read(walletControllerProvider.notifier).refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    return SecureScreen(
      child: Scaffold(
        appBar: AppBar(title: const Text('Add money')),
        body: PpFormScroll(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const PpScreenHeader(
                title: 'Top up via JazzCash',
                subtitle: 'Dev: use Simulate payment for instant credit, or open JazzCash checkout in WebView.',
              ),
              PpAmountField(
                controller: _amountController,
                autofocus: true,
              ),
              if (_error != null) PpInlineErrorState(message: _error!),
              const SizedBox(height: AppSpacing.xl),
              PpButton(
                label: 'Open JazzCash checkout',
                onPressed: _loading ? null : _initiateCheckout,
              ),
              const SizedBox(height: AppSpacing.sm),
              PpButton(
                label: 'Simulate payment (dev)',
                onPressed: _loading ? null : _simulatePayment,
              ),
              if (_checkoutUrl != null) ...[
                const SizedBox(height: AppSpacing.md),
                Text('Order: $_orderReference', style: AppTextStyles.label(context)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _JazzCashWebView extends StatefulWidget {
  const _JazzCashWebView({
    required this.checkoutUrl,
    required this.onClosed,
  });

  final String checkoutUrl;
  final VoidCallback onClosed;

  @override
  State<_JazzCashWebView> createState() => _JazzCashWebViewState();
}

class _JazzCashWebViewState extends State<_JazzCashWebView> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(Uri.parse(widget.checkoutUrl));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('JazzCash'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () {
            Navigator.of(context).pop();
            widget.onClosed();
          },
        ),
      ),
      body: WebViewWidget(controller: _controller),
    );
  }
}
