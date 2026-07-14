import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../shared/widgets/pp_empty_state.dart';
import '../../../../shared/widgets/pp_error_state.dart';
import '../../../../shared/widgets/pp_shimmer.dart';
import '../../../wallet/presentation/providers/transactions_provider.dart';
import '../../../wallet/domain/wallet_models.dart';

class AnalyticsScreen extends ConsumerStatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  ConsumerState<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends ConsumerState<AnalyticsScreen> {
  String _period = 'week';

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final summary = ref.watch(analyticsSummaryProvider(_period));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analytics'),
        actions: [
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'week', label: Text('7d')),
              ButtonSegment(value: 'month', label: Text('30d')),
            ],
            selected: {_period},
            onSelectionChanged: (value) => setState(() => _period = value.first),
          ),
          const SizedBox(width: AppSpacing.sm),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(analyticsSummaryProvider(_period));
          await ref.read(analyticsSummaryProvider(_period).future);
        },
        child: summary.when(
            loading: () => const PpAnalyticsSkeleton(),
            error: (e, _) => ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              children: [
                PpErrorState(
                  message: userFacingError(e),
                  onRetry: () => ref.invalidate(analyticsSummaryProvider(_period)),
                ),
              ],
            ),
            data: (AnalyticsSummary data) {
            if (data.txCount == 0) {
              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                children: [
                  PpEmptyState(
                    icon: Icons.bar_chart_outlined,
                    title: 'No spending data yet',
                    message: 'Transactions in this period will appear here with charts and breakdowns.',
                  ),
                ],
              );
            }

              return ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(AppSpacing.lg),
                children: [
                Row(
                  children: [
                    Expanded(child: _StatCard(label: 'Money in', value: data.totalInPkr, color: pp.primary)),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(child: _StatCard(label: 'Money out', value: data.totalOutPkr, color: pp.accent)),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                _StatCard(label: 'Net', value: data.netPkr, color: pp.mintDark, wide: true),
                const SizedBox(height: AppSpacing.xl),
                Text('Daily activity', style: AppTextStyles.title(context)),
                const SizedBox(height: AppSpacing.md),
                SizedBox(
                  height: 220,
                  child: _DailyChart(daily: data.daily, palette: pp),
                ),
                const SizedBox(height: AppSpacing.xl),
                Text('By type', style: AppTextStyles.title(context)),
                const SizedBox(height: AppSpacing.sm),
                ...data.byType.map(
                  (row) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(row.txType.replaceAll('_', ' ')),
                    subtitle: Text('${row.count} transactions'),
                    trailing: Text('Rs. ${row.amountPkr.toStringAsFixed(0)}'),
                  ),
                ),
              ],
              );
            },
          ),
        ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.label,
    required this.value,
    required this.color,
    this.wide = false,
  });

  final String label;
  final double value;
  final Color color;
  final bool wide;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    return Container(
      width: wide ? double.infinity : null,
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: context.cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: pp.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppTextStyles.label(context)),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Rs. ${value.toStringAsFixed(0)}',
            style: AppTextStyles.title(context).copyWith(color: color, fontSize: 20),
          ),
        ],
      ),
    );
  }
}

class _DailyChart extends StatelessWidget {
  const _DailyChart({required this.daily, required this.palette});

  final List<AnalyticsDailyBreakdown> daily;
  final PalmPayPalette palette;

  @override
  Widget build(BuildContext context) {
    final spotsIn = <FlSpot>[];
    final spotsOut = <FlSpot>[];
    for (var i = 0; i < daily.length; i++) {
      final day = daily[i];
      spotsIn.add(FlSpot(i.toDouble(), day.inPkr));
      spotsOut.add(FlSpot(i.toDouble(), day.outPkr));
    }

    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: false),
        titlesData: const FlTitlesData(show: false),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: spotsIn,
            isCurved: true,
            color: palette.primary,
            barWidth: 3,
            dotData: const FlDotData(show: false),
          ),
          LineChartBarData(
            spots: spotsOut,
            isCurved: true,
            color: palette.accent,
            barWidth: 3,
            dotData: const FlDotData(show: false),
          ),
        ],
      ),
    );
  }
}
