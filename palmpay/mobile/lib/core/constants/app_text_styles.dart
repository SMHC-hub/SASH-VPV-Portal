import 'package:flutter/material.dart';

import '../theme/palmpay_palette.dart';

abstract final class AppTextStyles {
  static TextStyle display(BuildContext context) => TextStyle(
        fontSize: 28,
        fontWeight: FontWeight.w700,
        color: Theme.of(context).colorScheme.onSurface,
        letterSpacing: -0.5,
      );

  static TextStyle title(BuildContext context) => TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: Theme.of(context).colorScheme.onSurface,
      );

  static TextStyle body(BuildContext context) => TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w400,
        color: Theme.of(context).extension<PalmPayPalette>()?.textSecondary ??
            Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.7),
        height: 1.4,
      );

  static TextStyle label(BuildContext context) => TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w500,
        color: Theme.of(context).extension<PalmPayPalette>()?.textSecondary ??
            Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.6),
        letterSpacing: 0.2,
      );

  static TextStyle amount(BuildContext context) => TextStyle(
        fontSize: 32,
        fontWeight: FontWeight.w700,
        color: Theme.of(context).colorScheme.onSurface,
        letterSpacing: -0.5,
      );
}
