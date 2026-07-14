import 'package:flutter_riverpod/flutter_riverpod.dart';

class SignupDraft {
  const SignupDraft({
    required this.fullName,
    required this.email,
    required this.phone,
    this.devOtpPhone,
    this.devOtpEmail,
    this.phoneVerified = false,
    this.emailVerified = false,
  });

  final String fullName;
  final String email;
  final String phone;
  final String? devOtpPhone;
  final String? devOtpEmail;
  final bool phoneVerified;
  final bool emailVerified;

  SignupDraft copyWith({
    bool? phoneVerified,
    bool? emailVerified,
  }) {
    return SignupDraft(
      fullName: fullName,
      email: email,
      phone: phone,
      devOtpPhone: devOtpPhone,
      devOtpEmail: devOtpEmail,
      phoneVerified: phoneVerified ?? this.phoneVerified,
      emailVerified: emailVerified ?? this.emailVerified,
    );
  }
}

class SignupDraftController extends StateNotifier<SignupDraft?> {
  SignupDraftController() : super(null);

  void setDraft(SignupDraft draft) => state = draft;

  void markPhoneVerified() {
    if (state != null) state = state!.copyWith(phoneVerified: true);
  }

  void markEmailVerified() {
    if (state != null) state = state!.copyWith(emailVerified: true);
  }

  void clear() => state = null;
}

final signupDraftProvider =
    StateNotifierProvider<SignupDraftController, SignupDraft?>((ref) {
  return SignupDraftController();
});
