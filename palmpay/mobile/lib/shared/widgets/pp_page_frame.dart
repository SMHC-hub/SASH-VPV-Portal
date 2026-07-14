import 'package:flutter/material.dart';

import '../../core/constants/app_spacing.dart';

/// Full-width on phones; centers and constrains width on tablets only.
class PpPageFrame extends StatelessWidget {
  const PpPageFrame({
    super.key,
    required this.child,
    this.maxWidth = 920,
    this.horizontalPadding = AppSpacing.lg,
    this.tabletBreakpoint = 720,
  });

  final Widget child;
  final double maxWidth;
  final double horizontalPadding;
  final double tabletBreakpoint;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isTablet = constraints.maxWidth >= tabletBreakpoint;
        if (!isTablet) {
          return SizedBox(
            width: double.infinity,
            child: child,
          );
        }

        return Align(
          alignment: Alignment.topCenter,
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: maxWidth),
              child: SizedBox(
                width: double.infinity,
                child: child,
              ),
            ),
          ),
        );
      },
    );
  }
}
