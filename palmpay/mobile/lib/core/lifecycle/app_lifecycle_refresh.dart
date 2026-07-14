import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/onboarding/presentation/providers/auth_provider.dart';
import '../../features/onboarding/presentation/providers/onboarding_provider.dart';
import '../../features/profile/presentation/providers/profile_provider.dart';
import '../../features/wallet/presentation/providers/wallet_provider.dart';

/// Refreshes wallet data when the app returns to foreground.
class AppLifecycleRefresh extends ConsumerStatefulWidget {
  const AppLifecycleRefresh({super.key, required this.child});

  final Widget child;

  @override
  ConsumerState<AppLifecycleRefresh> createState() => _AppLifecycleRefreshState();
}

class _AppLifecycleRefreshState extends ConsumerState<AppLifecycleRefresh>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state != AppLifecycleState.resumed) return;
    final auth = ref.read(authControllerProvider);
    if (!auth.isAuthenticated) return;

    ref.read(walletControllerProvider.notifier).refresh();
    ref.read(onboardingControllerProvider.notifier).refresh();
    ref.read(profileSettingsProvider.notifier).refresh();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
