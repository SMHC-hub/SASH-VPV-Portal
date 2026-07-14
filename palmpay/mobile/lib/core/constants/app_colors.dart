import 'package:flutter/material.dart';

/// VeinPay brand tokens (original dark-fintech palette).
abstract final class AppColors {
  static const background = Color(0xFF0B0F14);
  static const surface = Color(0xFF151B24);
  static const surfaceElevated = Color(0xFF1E2733);
  static const primary = Color(0xFF00C896);
  static const primaryDark = Color(0xFF00A67E);
  static const accent = Color(0xFF3D8BFF);
  static const error = Color(0xFFFF5C5C);
  static const success = Color(0xFF2ECC71);
  static const textPrimary = Color(0xFFF4F7FB);
  static const textSecondary = Color(0xFF9AA7B8);
  static const textMuted = Color(0xFF6B7280);
  static const border = Color(0xFF2A3444);
  static const divider = Color(0xFF1E2733);
  static const shadow = Color(0x40000000);
  static const onPrimary = Color(0xFF0B0F14);
  static const onBalanceCard = Color(0xFFFFFFFF);
  static const onMintCard = primary;

  static const balanceCardGradient = [Color(0xFF12352C), Color(0xFF151B24)];

  // Light-mode surfaces (when theme is light)
  static const lightBackground = Color(0xFFFAFBFC);
  static const lightSurface = Color(0xFFFFFFFF);
  static const lightSurfaceElevated = Color(0xFFF3F5F7);
  static const lightTextPrimary = Color(0xFF111827);
  static const lightTextSecondary = Color(0xFF6B7280);
  static const lightBorder = Color(0xFFE5E7EB);
  static const lightShadow = Color(0x14111827);
}
