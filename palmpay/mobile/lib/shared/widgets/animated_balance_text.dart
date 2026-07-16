import 'package:flutter/material.dart';

import '../../core/constants/app_text_styles.dart';
import '../../core/utils/pkr_format.dart';

class AnimatedBalanceText extends StatefulWidget {
  const AnimatedBalanceText({
    super.key,
    required this.amount,
    this.hidden = false,
    this.style,
    this.prefix = 'PKR ',
    this.maxWidth,
    this.animate = true,
  });

  final double amount;
  final bool hidden;
  final TextStyle? style;
  final String prefix;
  final double? maxWidth;
  final bool animate;

  @override
  State<AnimatedBalanceText> createState() => _AnimatedBalanceTextState();
}

class _AnimatedBalanceTextState extends State<AnimatedBalanceText>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  Animation<double> _buildAnimation({required double begin, required double end}) {
    return Tween<double>(begin: begin, end: end).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic),
    );
  }

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: widget.animate ? 900 : 0),
    );
    final begin = widget.animate ? 0.0 : widget.amount;
    _animation = _buildAnimation(begin: begin, end: widget.amount);
    if (widget.animate) {
      _controller.forward();
    } else {
      _controller.value = 1;
    }
  }

  @override
  void didUpdateWidget(AnimatedBalanceText oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.amount != widget.amount) {
      final from = _animation.value;
      _animation = _buildAnimation(begin: from, end: widget.amount);
      _controller
        ..duration = Duration(milliseconds: widget.animate ? 900 : 0)
        ..reset();
      if (widget.animate) {
        _controller.forward();
      } else {
        _controller.value = 1;
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  TextStyle _resolvedStyle(BuildContext context, double value) {
    final base = widget.style ?? AppTextStyles.amount(context);
    final width = widget.maxWidth ?? 200;
    final digits = value.toStringAsFixed(0).length;
    double size = base.fontSize ?? 28;
    if (width < 170 || digits > 8) {
      size = 20;
    } else if (width < 200 || digits > 7) {
      size = 22;
    } else if (digits > 6) {
      size = 24;
    }
    return base.copyWith(fontSize: size, height: 1.1);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final value = _animation.value;
        final style = _resolvedStyle(context, value);
        final compact = PkrFormat.compactLabel(value);

        if (widget.hidden) {
          return Text('${widget.prefix}••••••', style: style, maxLines: 1);
        }

        final mainLine = '${widget.prefix}${PkrFormat.amount(value)}';
        final text = Text(
          mainLine,
          style: style,
          maxLines: 1,
          softWrap: false,
        );

        final child = widget.maxWidth != null
            ? FittedBox(
                fit: BoxFit.scaleDown,
                alignment: Alignment.centerLeft,
                child: text,
              )
            : text;

        if (compact == null) return child;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            child,
            Text(
              compact,
              style: style.copyWith(
                fontSize: (style.fontSize ?? 22) * 0.55,
                fontWeight: FontWeight.w500,
                color: style.color?.withValues(alpha: 0.75),
              ),
              maxLines: 1,
            ),
          ],
        );
      },
    );
  }
}
