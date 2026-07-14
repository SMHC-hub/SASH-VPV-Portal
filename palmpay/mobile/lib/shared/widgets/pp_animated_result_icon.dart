import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Scale + fade checkmark / error icon for payment and transfer results.
class PpAnimatedResultIcon extends StatefulWidget {
  const PpAnimatedResultIcon({
    super.key,
    required this.icon,
    required this.color,
    this.size = 88,
    this.iconSize = 48,
  });

  final IconData icon;
  final Color color;
  final double size;
  final double iconSize;

  @override
  State<PpAnimatedResultIcon> createState() => _PpAnimatedResultIconState();
}

class _PpAnimatedResultIconState extends State<PpAnimatedResultIcon>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 520),
    );
    _scale = CurvedAnimation(parent: _controller, curve: Curves.elasticOut);
    _controller.forward();
    HapticFeedback.mediumImpact();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scale,
      child: FadeTransition(
        opacity: _controller,
        child: Container(
          width: widget.size,
          height: widget.size,
          decoration: BoxDecoration(
            color: widget.color.withValues(alpha: 0.15),
            shape: BoxShape.circle,
          ),
          child: Icon(widget.icon, size: widget.iconSize, color: widget.color),
        ),
      ),
    );
  }
}
