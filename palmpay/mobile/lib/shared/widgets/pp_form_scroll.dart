import 'package:flutter/material.dart';

import '../../core/constants/app_spacing.dart';
import 'pp_page_frame.dart';

/// Scrollable form body with keyboard dismiss-on-drag (Day 8).
class PpFormScroll extends StatelessWidget {
  const PpFormScroll({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(AppSpacing.lg),
  });

  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    final viewInsetsBottom = MediaQuery.viewInsetsOf(context).bottom;
    return SingleChildScrollView(
      padding: EdgeInsets.only(bottom: AppSpacing.lg + viewInsetsBottom),
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      child: PpPageFrame(
        maxWidth: 560,
        horizontalPadding: 0,
        child: Padding(
          padding: padding,
          child: child,
        ),
      ),
    );
  }
}
