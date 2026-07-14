import 'package:flutter/material.dart';

import '../constants/app_colors.dart';

/// Theme-aware VeinPay palette. Access via `context.pp`.
@immutable
class PalmPayPalette extends ThemeExtension<PalmPayPalette> {
  const PalmPayPalette({
    required this.primary,
    required this.primaryDark,
    required this.accent,
    required this.onBalanceCard,
    required this.balanceGradient,
    required this.surfaceElevated,
    required this.textSecondary,
    required this.textMuted,
    required this.border,
    required this.shadow,
    required this.discoverTint,
  });

  final Color primary;
  final Color primaryDark;
  final Color accent;
  final Color onBalanceCard;
  final List<Color> balanceGradient;
  final Color surfaceElevated;
  final Color textSecondary;
  final Color textMuted;
  final Color border;
  final Color shadow;
  final Color discoverTint;

  // Legacy aliases used in widgets
  Color get mint => primary;
  Color get mintDark => primaryDark;
  Color get actionBlue => accent;
  Color get actionCoral => primary;

  static const light = PalmPayPalette(
    primary: AppColors.primary,
    primaryDark: AppColors.primaryDark,
    accent: AppColors.accent,
    onBalanceCard: AppColors.onBalanceCard,
    balanceGradient: AppColors.balanceCardGradient,
    surfaceElevated: AppColors.lightSurfaceElevated,
    textSecondary: AppColors.lightTextSecondary,
    textMuted: AppColors.textMuted,
    border: AppColors.lightBorder,
    shadow: AppColors.lightShadow,
    discoverTint: Color(0xFFE8F8F3),
  );

  static const dark = PalmPayPalette(
    primary: AppColors.primary,
    primaryDark: AppColors.primaryDark,
    accent: AppColors.accent,
    onBalanceCard: AppColors.onBalanceCard,
    balanceGradient: AppColors.balanceCardGradient,
    surfaceElevated: AppColors.surfaceElevated,
    textSecondary: AppColors.textSecondary,
    textMuted: AppColors.textSecondary,
    border: AppColors.border,
    shadow: AppColors.shadow,
    discoverTint: AppColors.surfaceElevated,
  );

  @override
  PalmPayPalette copyWith({
    Color? primary,
    Color? primaryDark,
    Color? accent,
    Color? onBalanceCard,
    List<Color>? balanceGradient,
    Color? surfaceElevated,
    Color? textSecondary,
    Color? textMuted,
    Color? border,
    Color? shadow,
    Color? discoverTint,
  }) {
    return PalmPayPalette(
      primary: primary ?? this.primary,
      primaryDark: primaryDark ?? this.primaryDark,
      accent: accent ?? this.accent,
      onBalanceCard: onBalanceCard ?? this.onBalanceCard,
      balanceGradient: balanceGradient ?? this.balanceGradient,
      surfaceElevated: surfaceElevated ?? this.surfaceElevated,
      textSecondary: textSecondary ?? this.textSecondary,
      textMuted: textMuted ?? this.textMuted,
      border: border ?? this.border,
      shadow: shadow ?? this.shadow,
      discoverTint: discoverTint ?? this.discoverTint,
    );
  }

  @override
  PalmPayPalette lerp(ThemeExtension<PalmPayPalette>? other, double t) {
    if (other is! PalmPayPalette) return this;
    return PalmPayPalette(
      primary: Color.lerp(primary, other.primary, t)!,
      primaryDark: Color.lerp(primaryDark, other.primaryDark, t)!,
      accent: Color.lerp(accent, other.accent, t)!,
      onBalanceCard: Color.lerp(onBalanceCard, other.onBalanceCard, t)!,
      balanceGradient: [
        Color.lerp(balanceGradient[0], other.balanceGradient[0], t)!,
        Color.lerp(balanceGradient[1], other.balanceGradient[1], t)!,
      ],
      surfaceElevated: Color.lerp(surfaceElevated, other.surfaceElevated, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      textMuted: Color.lerp(textMuted, other.textMuted, t)!,
      border: Color.lerp(border, other.border, t)!,
      shadow: Color.lerp(shadow, other.shadow, t)!,
      discoverTint: Color.lerp(discoverTint, other.discoverTint, t)!,
    );
  }
}

extension PalmPayThemeContext on BuildContext {
  PalmPayPalette get pp => Theme.of(this).extension<PalmPayPalette>() ?? PalmPayPalette.light;
  ColorScheme get cs => Theme.of(this).colorScheme;
}
