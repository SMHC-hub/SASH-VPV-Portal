import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/security/secure_screen_service.dart';
import '../../../../core/utils/pkr_format.dart';
import '../../../../shared/widgets/pp_amount_field.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_form_scroll.dart';
import '../../../../shared/widgets/pp_inline_error_state.dart';
import '../../../../shared/widgets/pp_screen_header.dart';
import '../../data/wallet_repository.dart';
import '../../domain/wallet_models.dart';
import '../../presentation/providers/wallet_provider.dart';

class SendMoneyScreen extends ConsumerStatefulWidget {
  const SendMoneyScreen({super.key});

  @override
  ConsumerState<SendMoneyScreen> createState() => _SendMoneyScreenState();
}

class _SendMoneyScreenState extends ConsumerState<SendMoneyScreen> {
  final _phoneController = TextEditingController();
  final _amountController = TextEditingController(text: '500');
  final _noteController = TextEditingController();
  final _phoneFocus = FocusNode();
  final _amountFocus = FocusNode();
  final _noteFocus = FocusNode();
  Timer? _debounce;
  bool _loading = false;
  String? _error;
  List<TransferLookupResult> _results = [];

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
    _debounce?.cancel();
    _phoneController.dispose();
    _amountController.dispose();
    _noteController.dispose();
    _phoneFocus.dispose();
    _amountFocus.dispose();
    _noteFocus.dispose();
    super.dispose();
  }

  void _onPhoneChanged(String value) {
    _debounce?.cancel();
    if (value.trim().length < 3) {
      setState(() => _results = []);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 400), () async {
      try {
        final items = await ref.read(walletRepositoryProvider).lookupRecipient(value.trim());
        if (mounted) setState(() => _results = items);
      } catch (_) {}
    });
  }

  void _selectContact(RecentContact contact) {
    _phoneController.text = contact.phone;
    setState(() => _results = []);
    _amountFocus.requestFocus();
  }

  Future<void> _continue() async {
    final phone = _phoneController.text.trim();
    final amount = PkrFormat.parseAmount(_amountController.text);
    if (phone.length < 10) {
      setState(() => _error = 'Enter a valid phone number');
      return;
    }
    if (amount == null || amount <= 0) {
      setState(() => _error = 'Enter a valid amount');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final preview = await ref.read(walletRepositoryProvider).initiateTransfer(
            recipientPhone: phone,
            amountPkr: amount,
            note: _noteController.text.trim(),
          );
      final name = preview.recipientName;
      ref.read(walletControllerProvider.notifier).addRecentContact(
            RecentContact(fullName: name, phone: phone),
          );
      if (!mounted) return;
      context.push(AppRoutes.sendConfirm, extra: {
        'preview': preview,
        'recipientPhone': phone,
      });
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final recent = ref.watch(walletControllerProvider).recentContacts;

    return SecureScreen(
      child: Scaffold(
        appBar: AppBar(title: const Text('Send money')),
        body: PpFormScroll(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const PpScreenHeader(
                title: 'Send money',
                subtitle: 'Transfer securely to any registered VeinPay recipient.',
              ),
              TextField(
                controller: _phoneController,
                focusNode: _phoneFocus,
                keyboardType: TextInputType.phone,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: 'Recipient phone',
                  hintText: '03XX XXXXXXX',
                  border: OutlineInputBorder(),
                ),
                onChanged: _onPhoneChanged,
                onSubmitted: (_) => _amountFocus.requestFocus(),
              ),
              if (_results.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.sm),
                ..._results.map(
                  (r) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(r.fullName),
                    subtitle: Text(r.phoneMasked),
                    onTap: () => setState(() => _results = []),
                  ),
                ),
              ],
              if (recent.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.lg),
                Text('Recent', style: AppTextStyles.title(context)),
                ...recent.map(
                  (c) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const CircleAvatar(child: Icon(Icons.person, size: 20)),
                    title: Text(c.fullName),
                    subtitle: Text(c.phone),
                    onTap: () => _selectContact(c),
                  ),
                ),
              ] else ...[
                const SizedBox(height: AppSpacing.lg),
                Text('Recent', style: AppTextStyles.title(context)),
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
                  child: Text(
                    'No recent contacts yet. People you send money to will appear here.',
                    style: AppTextStyles.label(context),
                  ),
                ),
              ],
              const SizedBox(height: AppSpacing.lg),
              PpAmountField(
                controller: _amountController,
                focusNode: _amountFocus,
                textInputAction: TextInputAction.next,
                onSubmitted: (_) => _noteFocus.requestFocus(),
              ),
              const SizedBox(height: AppSpacing.md),
              TextField(
                controller: _noteController,
                focusNode: _noteFocus,
                textInputAction: TextInputAction.done,
                decoration: const InputDecoration(
                  labelText: 'Note (optional)',
                  border: OutlineInputBorder(),
                ),
                onSubmitted: (_) => _continue(),
              ),
            if (_error != null) PpInlineErrorState(message: _error!),
              const SizedBox(height: AppSpacing.xl),
              PpButton(label: 'Continue', onPressed: _loading ? null : _continue),
            ],
          ),
        ),
      ),
    );
  }
}
