import 'package:flutter/material.dart';

import '../../core/constants/veinpay_brand.dart';

/// Theme-aware VeinPay logo. Light theme uses [VeinPayBrand.logoLight] (default).
class VeinPayLogo extends StatelessWidget {
  const VeinPayLogo({
    super.key,
    this.size = VeinPayBrand.logoMd,
    this.fit = BoxFit.contain,
    this.forceLight = false,
    this.forceDark = false,
  });

  final double size;
  final BoxFit fit;

  /// Always show the light logo asset (e.g. on a dark gradient card).
  final bool forceLight;

  /// Always show the dark logo asset.
  final bool forceDark;

  static double scaledSize(BuildContext context, double baseSize) {
    final textScaler = MediaQuery.textScalerOf(context);
    final accessibilityScale = textScaler.scale(1).clamp(0.85, 1.35);
    return baseSize * accessibilityScale;
  }

  static String assetFor(BuildContext context, {bool forceLight = false, bool forceDark = false}) {
    if (forceLight) return VeinPayBrand.logoLight;
    if (forceDark) return VeinPayBrand.logoDark;
    final brightness = Theme.of(context).brightness;
    return brightness == Brightness.dark ? VeinPayBrand.logoDark : VeinPayBrand.logoLight;
  }

  @override
  Widget build(BuildContext context) {
    final scaled = scaledSize(context, size);
    final asset = assetFor(context, forceLight: forceLight, forceDark: forceDark);
    final dpr = MediaQuery.devicePixelRatioOf(context);
    final cachePx = (scaled * dpr).round().clamp(1, 2048);

    return Image.asset(
      asset,
      width: scaled,
      height: scaled,
      fit: fit,
      filterQuality: FilterQuality.high,
      cacheWidth: cachePx,
      cacheHeight: cachePx,
      semanticLabel: VeinPayBrand.appName,
    );
  }
}

/// Logo with optional tagline for splash / auth headers.
class VeinPayBrandMark extends StatelessWidget {
  const VeinPayBrandMark({
    super.key,
    this.logoSize = VeinPayBrand.logoXl,
    this.tagline,
    this.alignment = CrossAxisAlignment.start,
  });

  final double logoSize;
  final String? tagline;
  final CrossAxisAlignment alignment;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: alignment,
      mainAxisSize: MainAxisSize.min,
      children: [
        VeinPayLogo(size: logoSize),
        if (tagline != null) ...[
          SizedBox(height: VeinPayLogo.scaledSize(context, 12)),
          Text(
            tagline!,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ],
    );
  }
}
