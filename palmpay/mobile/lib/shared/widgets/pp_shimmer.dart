import 'package:flutter/material.dart';

import '../../core/constants/app_spacing.dart';

/// Lightweight skeleton placeholder with a subtle shimmer sweep.
class PpShimmerBox extends StatefulWidget {
  const PpShimmerBox({
    super.key,
    required this.width,
    required this.height,
    this.borderRadius = 12,
  });

  final double width;
  final double height;
  final double borderRadius;

  @override
  State<PpShimmerBox> createState() => _PpShimmerBoxState();
}

class _PpShimmerBoxState extends State<PpShimmerBox> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final base = Theme.of(context).colorScheme.surfaceContainerHighest;
    final highlight = Theme.of(context).colorScheme.surface;

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(widget.borderRadius),
            gradient: LinearGradient(
              begin: Alignment(-1 + (_controller.value * 2), 0),
              end: Alignment(0 + (_controller.value * 2), 0),
              colors: [base, highlight, base],
            ),
          ),
        );
      },
    );
  }
}

class PpHomeSkeleton extends StatelessWidget {
  const PpHomeSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const PpShimmerBox(width: 160, height: 24, borderRadius: 8),
        const SizedBox(height: AppSpacing.lg),
        const PpShimmerBox(width: double.infinity, height: 172, borderRadius: 20),
        const SizedBox(height: AppSpacing.xl),
        const PpShimmerBox(width: 120, height: 20, borderRadius: 8),
        const SizedBox(height: AppSpacing.md),
        ...List.generate(
          3,
          (_) => const Padding(
            padding: EdgeInsets.only(bottom: AppSpacing.sm),
            child: PpShimmerBox(width: double.infinity, height: 72, borderRadius: 16),
          ),
        ),
      ],
    );
  }
}

class PpTransactionListSkeleton extends StatelessWidget {
  const PpTransactionListSkeleton({super.key, this.count = 6});

  final int count;

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const NeverScrollableScrollPhysics(),
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
      children: List.generate(
        count,
        (_) => const Padding(
          padding: EdgeInsets.only(bottom: AppSpacing.sm),
          child: PpShimmerBox(width: double.infinity, height: 72, borderRadius: 16),
        ),
      ),
    );
  }
}

class PpReceiptSkeleton extends StatelessWidget {
  const PpReceiptSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: const [
        PpShimmerBox(width: double.infinity, height: 140, borderRadius: 20),
        SizedBox(height: AppSpacing.lg),
        PpShimmerBox(width: double.infinity, height: 20, borderRadius: 8),
        SizedBox(height: AppSpacing.md),
        PpShimmerBox(width: double.infinity, height: 20, borderRadius: 8),
        SizedBox(height: AppSpacing.md),
        PpShimmerBox(width: double.infinity, height: 20, borderRadius: 8),
      ],
    );
  }
}

class PpAnalyticsSkeleton extends StatelessWidget {
  const PpAnalyticsSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      children: const [
        Row(
          children: [
            Expanded(child: PpShimmerBox(width: double.infinity, height: 88, borderRadius: 16)),
            SizedBox(width: AppSpacing.sm),
            Expanded(child: PpShimmerBox(width: double.infinity, height: 88, borderRadius: 16)),
          ],
        ),
        SizedBox(height: AppSpacing.sm),
        PpShimmerBox(width: double.infinity, height: 88, borderRadius: 16),
        SizedBox(height: AppSpacing.xl),
        PpShimmerBox(width: 140, height: 20, borderRadius: 8),
        SizedBox(height: AppSpacing.md),
        PpShimmerBox(width: double.infinity, height: 220, borderRadius: 16),
      ],
    );
  }
}
