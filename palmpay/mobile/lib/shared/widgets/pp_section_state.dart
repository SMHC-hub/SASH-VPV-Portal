import 'package:flutter/material.dart';

import 'pp_error_state.dart';
import 'pp_inline_error_state.dart';

class PpSectionState extends StatelessWidget {
  const PpSectionState({
    super.key,
    required this.loading,
    required this.isEmpty,
    required this.child,
    required this.loadingChild,
    required this.emptyChild,
    this.errorMessage,
    this.onRetry,
    this.errorInCenter = true,
  });

  final bool loading;
  final String? errorMessage;
  final VoidCallback? onRetry;

  /// Used to decide whether to show [emptyChild].
  final bool isEmpty;

  final Widget child;
  final Widget loadingChild;
  final Widget emptyChild;

  /// When true, shows [PpErrorState] (centered). When false, shows [PpInlineErrorState].
  final bool errorInCenter;

  @override
  Widget build(BuildContext context) {
    if (loading) return loadingChild;
    if (errorMessage != null) {
      if (errorInCenter) {
        return PpErrorState(
          message: errorMessage!,
          onRetry: onRetry,
        );
      }
      return PpInlineErrorState(
        message: errorMessage!,
        onRetry: onRetry,
      );
    }
    if (isEmpty) return emptyChild;
    return child;
  }
}

