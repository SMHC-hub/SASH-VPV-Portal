import 'dart:async';



import 'package:flutter/material.dart';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:go_router/go_router.dart';



import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/veinpay_brand.dart';

import '../../../../core/router/app_routes.dart';

import '../../../../core/router/navigation_resolver.dart';

import '../../../../core/theme/palmpay_palette.dart';

import '../../../../shared/widgets/veinpay_logo.dart';

import '../../presentation/providers/auth_provider.dart';

import '../../presentation/providers/onboarding_provider.dart';



class SplashScreen extends ConsumerStatefulWidget {

  const SplashScreen({super.key});



  @override

  ConsumerState<SplashScreen> createState() => _SplashScreenState();

}



class _SplashScreenState extends ConsumerState<SplashScreen> {

  bool _navigating = false;

  Timer? _autoNavTimer;

  ProviderSubscription<AuthState>? _authSub;

  ProviderSubscription<OnboardingState>? _onboardingSub;



  @override

  void initState() {

    super.initState();

    _authSub = ref.listenManual<AuthState>(

      authControllerProvider,

      (_, __) => _tryNavigate(),

    );

    _onboardingSub = ref.listenManual<OnboardingState>(

      onboardingControllerProvider,

      (_, __) => _tryNavigate(),

    );

    WidgetsBinding.instance.addPostFrameCallback((_) {

      _tryNavigate();

      _autoNavTimer = Timer(const Duration(milliseconds: 450), _tryNavigate);

    });

  }



  @override

  void dispose() {

    _autoNavTimer?.cancel();

    _authSub?.close();

    _onboardingSub?.close();

    super.dispose();

  }



  void _tryNavigate() {

    if (!mounted || _navigating) return;

    final auth = ref.read(authControllerProvider);

    final onboarding = ref.read(onboardingControllerProvider);

    final route = resolveNextRoute(auth: auth, onboarding: onboarding);

    if (route != null && route != AppRoutes.splash) {

      _navigating = true;

      context.go(route);

    }

  }



  String _continueLabel(AuthState auth, OnboardingState onboarding) {

    if (!auth.isAuthenticated) return 'Continue to ${VeinPayBrand.appName}';

    if (onboarding.isComplete) return 'Open wallet';

    if (onboarding.needsKyc) return 'Continue to verification';

    return 'Continue';

  }



  @override

  Widget build(BuildContext context) {

    final auth = ref.watch(authControllerProvider);

    final onboarding = ref.watch(onboardingControllerProvider);

    final nextRoute = resolveNextRoute(auth: auth, onboarding: onboarding);

    final ready = nextRoute != null;



    final pp = context.pp;



    return Scaffold(

      body: SafeArea(

        child: Padding(

          padding: const EdgeInsets.all(AppSpacing.lg),

          child: Column(

            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              const Spacer(),

              VeinPayBrandMark(

                logoSize: VeinPayBrand.logoHero,

                tagline: 'Palm vein wallet',

              ),

              const SizedBox(height: AppSpacing.xl),

              if (auth.status == AuthStatus.unknown || !onboarding.loaded)

                LinearProgressIndicator(color: pp.mint),

              if (ready) ...[

                const SizedBox(height: AppSpacing.lg),

                SizedBox(

                  width: double.infinity,

                  child: FilledButton(

                    onPressed: _tryNavigate,

                    child: Text(_continueLabel(auth, onboarding)),

                  ),

                ),

              ],

              const Spacer(),

            ],

          ),

        ),

      ),

    );

  }

}


