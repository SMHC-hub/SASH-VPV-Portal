import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/lifecycle/app_lifecycle_refresh.dart';
import 'core/constants/app_theme.dart';
import 'core/constants/veinpay_brand.dart';
import 'core/router/app_router.dart';
import 'core/theme/theme_mode_provider.dart';
import 'shared/widgets/offline_banner.dart';

class VeinPayApp extends ConsumerWidget {
  const VeinPayApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);
    final themeMode = ref.watch(themeModeProvider);

    return MaterialApp.router(
      title: VeinPayBrand.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: themeMode,
      routerConfig: router,
      builder: (context, child) => AppLifecycleRefresh(
        child: OfflineAwareShell(
          child: child ?? const SizedBox.shrink(),
        ),
      ),
    );
  }
}
