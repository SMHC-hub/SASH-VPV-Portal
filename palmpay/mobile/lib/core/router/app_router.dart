import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/analytics/presentation/screens/analytics_screen.dart';
import '../../features/auth/presentation/screens/forgot_password_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/reset_password_screen.dart';
import '../../features/auth/presentation/screens/signup_details_screen.dart';
import '../../features/auth/presentation/screens/signup_pin_screen.dart';
import '../../features/auth/presentation/screens/signup_verify_email_screen.dart';
import '../../features/auth/presentation/screens/signup_verify_phone_screen.dart';
import '../../features/onboarding/presentation/providers/auth_provider.dart';
import '../../features/onboarding/presentation/providers/onboarding_provider.dart';
import '../../features/onboarding/presentation/screens/enrollment_success_screen.dart';
import '../../features/onboarding/presentation/screens/kyc_screen.dart';
import '../../features/onboarding/presentation/screens/palm_enrollment_screen.dart';
import '../../features/onboarding/presentation/screens/setup_spending_pin_screen.dart';
import '../../features/onboarding/presentation/screens/splash_screen.dart';
import '../../features/scan/presentation/screens/scan_result_failed_screen.dart';
import '../../features/scan/presentation/screens/scan_result_low_balance_screen.dart';
import '../../features/scan/presentation/screens/scan_result_success_screen.dart';
import '../../features/scan/presentation/screens/scan_screen.dart';
import '../../features/scan/domain/scan_models.dart';
import '../../features/wallet/presentation/screens/add_money_screen.dart';
import '../../features/wallet/presentation/screens/home_screen.dart';
import '../../features/wallet/presentation/screens/transaction_detail_screen.dart';
import '../../features/wallet/presentation/screens/transaction_history_screen.dart';
import '../../features/wallet/presentation/screens/send_confirm_screen.dart';
import '../../features/wallet/presentation/screens/send_money_screen.dart';
import '../../features/wallet/presentation/screens/topup_success_screen.dart';
import '../../features/wallet/presentation/screens/transfer_success_screen.dart';
import '../../features/wallet/domain/wallet_models.dart';
import '../../features/profile/presentation/screens/profile_screen.dart';
import '../../shared/widgets/main_shell.dart';
import 'app_routes.dart';
import 'navigation_resolver.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>(debugLabel: 'root');
final _shellNavigatorHomeKey = GlobalKey<NavigatorState>(debugLabel: 'shellHome');
final _shellNavigatorScanKey = GlobalKey<NavigatorState>(debugLabel: 'shellScan');
final _shellNavigatorAnalyticsKey = GlobalKey<NavigatorState>(debugLabel: 'shellAnalytics');
final _shellNavigatorProfileKey = GlobalKey<NavigatorState>(debugLabel: 'shellProfile');

final appRouterProvider = Provider<GoRouter>((ref) {
  final authRefresh = ref.watch(authRefreshListenableProvider);
  final onboardingRefresh = ref.watch(onboardingRefreshListenableProvider);
  final refresh = Listenable.merge([authRefresh, onboardingRefresh]);

  final router = GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: AppRoutes.splash,
    refreshListenable: refresh,
    redirect: (context, state) {
      final auth = ref.read(authControllerProvider);
      final onboarding = ref.read(onboardingControllerProvider);
      final loc = state.matchedLocation;

      if (auth.status == AuthStatus.unknown) {
        return isAuthRoute(loc) ? null : AppRoutes.login;
      }

      if (!auth.isAuthenticated) {
        return isAuthRoute(loc) ? null : AppRoutes.login;
      }

      // Profile reload (e.g. after image picker resume) must not bounce to login —
      // that remounts KYC and wipes in-progress form state.
      if (!onboarding.loaded) {
        return null;
      }

      if (onboarding.needsKyc) {
        return loc == AppRoutes.kyc ? null : AppRoutes.kyc;
      }

      if (onboarding.needsSpendingPin) {
        return loc == AppRoutes.setupSpendingPin ? null : AppRoutes.setupSpendingPin;
      }

      // KYC + payment PIN done → main app. Palm enrollment is optional in Scan tab.
      if (onboarding.isComplete) {
        if (isAuthRoute(loc) ||
            loc == AppRoutes.kyc ||
            loc == AppRoutes.setupSpendingPin) {
          return AppRoutes.home;
        }
        return null;
      }

      return resolveNextRoute(auth: auth, onboarding: onboarding);
    },
    routes: [
      GoRoute(
        path: AppRoutes.splash,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: AppRoutes.login,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: AppRoutes.forgotPassword,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: AppRoutes.resetPassword,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const ResetPasswordScreen(),
      ),
      GoRoute(
        path: AppRoutes.signupDetails,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SignupDetailsScreen(),
      ),
      GoRoute(
        path: AppRoutes.signupVerifyPhone,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final extra = state.extra as Map<String, dynamic>? ?? {};
          return SignupVerifyPhoneScreen(devOtp: extra['devOtpPhone'] as String?);
        },
      ),
      GoRoute(
        path: AppRoutes.signupVerifyEmail,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SignupVerifyEmailScreen(),
      ),
      GoRoute(
        path: AppRoutes.signupPin,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SignupPinScreen(),
      ),
      GoRoute(
        path: AppRoutes.kyc,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const KycScreen(),
      ),
      GoRoute(
        path: AppRoutes.setupSpendingPin,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SetupSpendingPinScreen(),
      ),
      GoRoute(
        path: AppRoutes.palmEnroll,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const PalmEnrollmentScreen(),
      ),
      GoRoute(
        path: AppRoutes.enrollSuccess,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const EnrollmentSuccessScreen(),
      ),
      GoRoute(
        path: AppRoutes.addMoney,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const AddMoneyScreen(),
      ),
      GoRoute(
        path: AppRoutes.sendMoney,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const SendMoneyScreen(),
      ),
      GoRoute(
        path: AppRoutes.transactions,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const TransactionHistoryScreen(),
      ),
      GoRoute(
        path: '/transactions/:reference',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => TransactionDetailScreen(
          reference: state.pathParameters['reference']!,
        ),
      ),
      GoRoute(
        path: AppRoutes.sendConfirm,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final extra = state.extra as Map<String, dynamic>? ?? {};
          return SendConfirmScreen(preview: extra['preview'] as TransferPreview?);
        },
      ),
      GoRoute(
        path: AppRoutes.transferSuccess,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => TransferSuccessScreen(
          preview: state.extra as TransferPreview,
        ),
      ),
      GoRoute(
        path: AppRoutes.topUpSuccess,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => TopUpSuccessScreen(
          amountPkr: state.extra as double,
        ),
      ),
      GoRoute(
        path: AppRoutes.notification,
        redirect: (context, state) {
          final type = state.uri.queryParameters['type'];
          final ref = state.uri.queryParameters['ref'];
          if (type == 'transaction' && ref != null && ref.isNotEmpty) {
            return AppRoutes.transactionDetail(ref);
          }
          if (type == 'payment_success' || type == 'payment_failed') {
            return AppRoutes.home;
          }
          return AppRoutes.home;
        },
      ),
      GoRoute(
        path: AppRoutes.scanResultSuccess,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ScanResultSuccessScreen(
          notification: state.extra as PalmPayNotification,
        ),
      ),
      GoRoute(
        path: AppRoutes.scanResultFailed,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ScanResultFailedScreen(
          notification: state.extra as PalmPayNotification,
        ),
      ),
      GoRoute(
        path: AppRoutes.scanResultLowBalance,
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => ScanResultLowBalanceScreen(
          notification: state.extra as PalmPayNotification,
        ),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return MainShell(navigationShell: navigationShell);
        },
        branches: [
          StatefulShellBranch(
            navigatorKey: _shellNavigatorHomeKey,
            routes: [
              GoRoute(path: AppRoutes.home, builder: (context, state) => const HomeScreen()),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _shellNavigatorScanKey,
            routes: [
              GoRoute(path: AppRoutes.scan, builder: (context, state) => const ScanScreen()),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _shellNavigatorAnalyticsKey,
            routes: [
              GoRoute(path: AppRoutes.analytics, builder: (context, state) => const AnalyticsScreen()),
            ],
          ),
          StatefulShellBranch(
            navigatorKey: _shellNavigatorProfileKey,
            routes: [
              GoRoute(path: AppRoutes.profile, builder: (context, state) => const ProfileScreen()),
            ],
          ),
        ],
      ),
    ],
  );

  ref.onDispose(router.dispose);
  return router;
});
