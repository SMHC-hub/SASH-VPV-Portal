import '../../features/onboarding/presentation/providers/auth_provider.dart';
import '../../features/onboarding/presentation/providers/onboarding_provider.dart';
import 'app_routes.dart';

bool isAuthRoute(String loc) {
  return loc == AppRoutes.splash ||
      loc == AppRoutes.login ||
      loc == AppRoutes.forgotPassword ||
      loc == AppRoutes.resetPassword ||
      loc == AppRoutes.signupDetails ||
      loc == AppRoutes.signupVerifyPhone ||
      loc == AppRoutes.signupVerifyEmail ||
      loc == AppRoutes.signupPin ||
      loc.startsWith('/signup') ||
      loc.startsWith('/login');
}

bool isOnboardingRoute(String loc) {
  return loc == AppRoutes.kyc ||
      loc == AppRoutes.palmEnroll ||
      loc == AppRoutes.enrollSuccess;
}

String? resolveNextRoute({
  required AuthState auth,
  required OnboardingState onboarding,
}) {
  if (auth.status == AuthStatus.unknown || !onboarding.loaded) return null;
  if (!auth.isAuthenticated) return AppRoutes.login;
  if (onboarding.isComplete) return AppRoutes.home;
  if (onboarding.needsKyc) return AppRoutes.kyc;
  if (onboarding.needsPalm) return AppRoutes.palmEnroll;
  return AppRoutes.home;
}
