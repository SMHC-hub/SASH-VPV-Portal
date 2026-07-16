import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/onboarding/presentation/providers/onboarding_provider.dart';

class MainShell extends ConsumerWidget {
  const MainShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final needsPalm = ref.watch(onboardingControllerProvider).needsPalm;
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      body: SafeArea(
        top: false,
        child: navigationShell,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: navigationShell.goBranch,
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Badge(
              isLabelVisible: needsPalm,
              smallSize: 8,
              backgroundColor: cs.error,
              child: const Icon(Icons.fingerprint_outlined),
            ),
            selectedIcon: Badge(
              isLabelVisible: needsPalm,
              smallSize: 8,
              backgroundColor: cs.error,
              child: const Icon(Icons.fingerprint),
            ),
            label: 'Scan',
          ),
          const NavigationDestination(
            icon: Icon(Icons.grid_view_outlined),
            selectedIcon: Icon(Icons.grid_view),
            label: 'Payments',
          ),
          const NavigationDestination(
            icon: Icon(Icons.menu_outlined),
            selectedIcon: Icon(Icons.menu),
            label: 'More',
          ),
        ],
      ),
    );
  }
}
