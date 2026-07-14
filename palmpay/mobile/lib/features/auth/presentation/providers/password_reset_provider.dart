import 'package:flutter_riverpod/flutter_riverpod.dart';

class PasswordResetDraft {
  const PasswordResetDraft({
    required this.email,
    this.devOtp,
  });

  final String email;
  final String? devOtp;
}

class PasswordResetController extends StateNotifier<PasswordResetDraft?> {
  PasswordResetController() : super(null);

  void setDraft(PasswordResetDraft draft) => state = draft;

  void clear() => state = null;
}

final passwordResetProvider =
    StateNotifierProvider<PasswordResetController, PasswordResetDraft?>((ref) {
  return PasswordResetController();
});
