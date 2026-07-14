import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../core/constants/veinpay_brand.dart';
import '../../../../core/theme/palmpay_palette.dart';
import '../../../../core/theme/theme_mode_provider.dart';
import '../../../../core/utils/pkr_format.dart';
import '../../domain/profile_models.dart';
import '../providers/profile_provider.dart';
import '../../../onboarding/presentation/providers/auth_provider.dart';
import '../../../onboarding/presentation/providers/onboarding_provider.dart';
import '../../../wallet/presentation/providers/wallet_provider.dart';
import '../../../../shared/widgets/veinpay_logo.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  Future<void> _showLimitDialog(BuildContext context, WidgetRef ref, double current) async {
    final controller = TextEditingController(text: current.round().toString());
    final result = await showDialog<double>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Set per-transaction limit'),
          content: TextField(
            controller: controller,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              prefixText: 'PKR ',
              hintText: '100 - 500000',
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancel'),
            ),
            TextButton(
              onPressed: () {
                final value = double.tryParse(controller.text.trim());
                Navigator.of(context).pop(value);
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );

    if (result == null) return;
    if (result < 100 || result > 500000) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Limit must be between PKR 100 and 500,000')),
        );
      }
      return;
    }
    await ref.read(walletControllerProvider.notifier).updatePerTxnLimit(result);
  }

  Future<void> _showDeviceManager(
    BuildContext context,
    WidgetRef ref,
    List<DeviceSession> sessions,
  ) async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) {
        final activeSessions = sessions.where((s) => s.isActive).toList();
        return SafeArea(
          child: SizedBox(
            height: MediaQuery.of(context).size.height * 0.7,
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text('Device manager', style: AppTextStyles.title(context)),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    'Revoke old sessions to force re-login on those devices.',
                    style: AppTextStyles.body(context),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  Expanded(
                    child: activeSessions.isEmpty
                        ? Center(
                            child: Text(
                              'No active sessions found',
                              style: AppTextStyles.body(context),
                            ),
                          )
                        : ListView.separated(
                            itemCount: activeSessions.length,
                            separatorBuilder: (_, __) => const Divider(height: 1),
                            itemBuilder: (context, i) {
                              final s = activeSessions[i];
                              return ListTile(
                                contentPadding: EdgeInsets.zero,
                                leading: const Icon(Icons.smartphone),
                                title: Text(s.deviceName),
                                subtitle: Text('Active until: ${s.expiresAt}'),
                                trailing: IconButton(
                                  icon: const Icon(Icons.logout),
                                  onPressed: () async {
                                    await ref.read(profileSettingsProvider.notifier).revokeSession(s.id);
                                    if (context.mounted) Navigator.of(context).pop();
                                  },
                                ),
                              );
                            },
                          ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Future<void> _showNotificationSettings(
    BuildContext context,
    WidgetRef ref,
    NotificationPreferences prefs,
  ) async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text('Notification settings', style: AppTextStyles.title(context)),
                const SizedBox(height: AppSpacing.md),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Transaction notifications'),
                  value: prefs.transactionNotifications,
                  onChanged: (v) async {
                    await ref.read(profileSettingsProvider.notifier).updateNotificationPreferences(
                          transactionNotifications: v,
                        );
                    if (context.mounted) Navigator.of(context).pop();
                  },
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Security notifications'),
                  value: prefs.securityNotifications,
                  onChanged: (v) async {
                    await ref.read(profileSettingsProvider.notifier).updateNotificationPreferences(
                          securityNotifications: v,
                        );
                    if (context.mounted) Navigator.of(context).pop();
                  },
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Promotional notifications'),
                  value: prefs.promoNotifications,
                  onChanged: (v) async {
                    await ref.read(profileSettingsProvider.notifier).updateNotificationPreferences(
                          promoNotifications: v,
                        );
                    if (context.mounted) Navigator.of(context).pop();
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pp = context.pp;
    final cs = context.cs;
    final themeMode = ref.watch(themeModeProvider);
    final auth = ref.watch(authControllerProvider);
    final onboarding = ref.watch(onboardingControllerProvider);
    final walletState = ref.watch(walletControllerProvider);
    final wallet = walletState.wallet;
    final profileState = ref.watch(profileSettingsProvider);
    final displayName = () {
      final sessionName = auth.session?.fullName ?? '';
      if (sessionName.isNotEmpty) return sessionName;
      final profileName = onboarding.profile?.fullName ?? '';
      if (profileName.isNotEmpty) return profileName;
      return '${VeinPayBrand.appName} user';
    }();

    return Scaffold(
      appBar: AppBar(title: const Text('More')),
      body: RefreshIndicator(
        onRefresh: () async {
          await Future.wait([
            ref.read(walletControllerProvider.notifier).refresh(),
            ref.read(profileSettingsProvider.notifier).refresh(),
            ref.read(onboardingControllerProvider.notifier).refresh(),
          ]);
        },
        child: ListView(
            padding: const EdgeInsets.all(AppSpacing.lg),
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
          Row(
            children: [
              CircleAvatar(
                radius: 28,
                backgroundColor: pp.mint.withValues(alpha: 0.2),
                child: Icon(Icons.person, color: pp.mintDark, size: 32),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      displayName,
                      style: AppTextStyles.title(context),
                    ),
                    Text(auth.session?.phone ?? '', style: AppTextStyles.body(context)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xl),
          Text('Appearance', style: AppTextStyles.title(context)),
          const SizedBox(height: AppSpacing.sm),
          Center(
            child: VeinPayLogo(size: VeinPayBrand.logoMd),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Logo follows your theme (light or dark). Default is light.',
            style: AppTextStyles.label(context),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: AppSpacing.sm),
          _SettingsCard(
            child: Column(
              children: [
                _ThemeOption(
                  label: 'Light',
                  icon: Icons.light_mode_outlined,
                  selected: themeMode == ThemeMode.light,
                  onTap: () => ref.read(themeModeProvider.notifier).setMode(ThemeMode.light),
                  logoPreview: const VeinPayLogo(size: VeinPayBrand.logoSm, forceLight: true),
                ),
                Divider(height: 1, color: pp.border),
                _ThemeOption(
                  label: 'Dark',
                  icon: Icons.dark_mode_outlined,
                  selected: themeMode == ThemeMode.dark,
                  onTap: () => ref.read(themeModeProvider.notifier).setMode(ThemeMode.dark),
                  logoPreview: const VeinPayLogo(size: VeinPayBrand.logoSm, forceDark: true),
                ),
                Divider(height: 1, color: pp.border),
                _ThemeOption(
                  label: 'System default',
                  icon: Icons.settings_brightness_outlined,
                  selected: themeMode == ThemeMode.system,
                  onTap: () => ref.read(themeModeProvider.notifier).setMode(ThemeMode.system),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Account & security', style: AppTextStyles.title(context)),
          const SizedBox(height: AppSpacing.sm),
          _SettingsCard(
            child: Column(
              children: [
                const _BiometricLoginToggle(),
                Divider(height: 1, color: pp.border),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.verified_user_outlined, color: pp.mintDark),
                  title: Text('KYC & identity', style: TextStyle(color: cs.onSurface)),
                  subtitle: Text('View verification status', style: AppTextStyles.label(context)),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
                Divider(height: 1, color: pp.border),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.fingerprint, color: pp.mintDark),
                  title: Text('Palm enrollment', style: TextStyle(color: cs.onSurface)),
                  subtitle: Text('Manage enrolled palm', style: AppTextStyles.label(context)),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Wallet protection', style: AppTextStyles.title(context)),
          const SizedBox(height: AppSpacing.sm),
          _SettingsCard(
            child: Column(
              children: [
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  secondary: Icon(Icons.lock_outline, color: pp.mintDark),
                  title: const Text('Freeze wallet'),
                  subtitle: Text(
                    wallet?.isFrozen == true
                        ? 'Outgoing payments are blocked'
                        : 'Allow transfers and palm payments',
                    style: AppTextStyles.label(context),
                  ),
                  value: wallet?.isFrozen ?? false,
                  onChanged: wallet == null
                      ? null
                      : (value) async {
                          await ref.read(walletControllerProvider.notifier).updateWalletSettings(
                                isFrozen: value,
                              );
                        },
                ),
                Divider(height: 1, color: pp.border),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  secondary: Icon(Icons.touch_app_outlined, color: pp.mintDark),
                  title: const Text('Vein Pay enabled'),
                  subtitle: Text(
                    'Merchant palm payments',
                    style: AppTextStyles.label(context),
                  ),
                  value: wallet?.palmPayEnabled ?? true,
                  onChanged: wallet == null
                      ? null
                      : (value) async {
                          await ref.read(walletControllerProvider.notifier).updateWalletSettings(
                                palmPayEnabled: value,
                              );
                        },
                ),
                Divider(height: 1, color: pp.border),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.tune, color: pp.mintDark),
                  title: const Text('Per-transaction limit'),
                  subtitle: Text(
                    wallet == null
                        ? 'Loading...'
                        : 'PKR ${PkrFormat.amount(wallet.perTxnLimitPkr, showDecimals: false)}',
                    style: AppTextStyles.label(context),
                  ),
                  trailing: const Icon(Icons.edit_outlined),
                  onTap: wallet == null
                      ? null
                      : () => _showLimitDialog(context, ref, wallet.perTxnLimitPkr),
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Text('Sessions & notifications', style: AppTextStyles.title(context)),
          const SizedBox(height: AppSpacing.sm),
          _SettingsCard(
            child: Column(
              children: [
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.devices_outlined, color: pp.mintDark),
                  title: const Text('Device manager'),
                  subtitle: Text(
                    profileState.sessions.isEmpty
                        ? 'No active sessions found'
                        : '${profileState.sessions.where((s) => s.isActive).length} active session(s)',
                    style: AppTextStyles.label(context),
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () async {
                    if (profileState.sessions.isEmpty) {
                      await ref.read(profileSettingsProvider.notifier).refresh();
                    }
                    if (!context.mounted) return;
                    await _showDeviceManager(context, ref, ref.read(profileSettingsProvider).sessions);
                  },
                ),
                Divider(height: 1, color: pp.border),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.notifications_outlined, color: pp.mintDark),
                  title: const Text('Notification preferences'),
                  subtitle: Text(
                    profileState.notifications == null
                        ? 'Tap to load preferences'
                        : 'Manage alerts for wallet and security',
                    style: AppTextStyles.label(context),
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () async {
                    if (profileState.notifications == null) {
                      await ref.read(profileSettingsProvider.notifier).refresh();
                    }
                    final prefs = ref.read(profileSettingsProvider).notifications;
                    if (prefs == null || !context.mounted) return;
                    await _showNotificationSettings(context, ref, prefs);
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: Icon(Icons.logout, color: cs.error),
            title: Text('Sign out', style: TextStyle(color: cs.error, fontWeight: FontWeight.w600)),
            onTap: () async {
              await ref.read(authControllerProvider.notifier).logout();
              if (context.mounted) context.go(AppRoutes.login);
            },
          ),
        ],
        ),
      ),
    );
  }
}

class _SettingsCard extends StatelessWidget {
  const _SettingsCard({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final cs = context.cs;
    final pp = context.pp;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md, vertical: AppSpacing.xs),
      decoration: BoxDecoration(
        color: cs.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: pp.border),
      ),
      child: Material(
        color: Colors.transparent,
        child: child,
      ),
    );
  }
}

class _BiometricLoginToggle extends ConsumerStatefulWidget {
  const _BiometricLoginToggle();

  @override
  ConsumerState<_BiometricLoginToggle> createState() => _BiometricLoginToggleState();
}

class _BiometricLoginToggleState extends ConsumerState<_BiometricLoginToggle> {
  bool? _enabled;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final v = await ref.read(authControllerProvider.notifier).isBiometricEnabled();
    if (mounted) setState(() => _enabled = v);
  }

  Future<void> _toggle(bool value) async {
    setState(() => _busy = true);
    if (value) {
      final available = await ref.read(authControllerProvider.notifier).isBiometricAvailable();
      if (!available) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Fingerprint not available on this device')),
          );
          setState(() => _busy = false);
        }
        return;
      }
    }
    final ok = await ref.read(authControllerProvider.notifier).setBiometricEnabled(value);
    if (mounted) {
      if (!ok && value) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not enable fingerprint. Confirm with your fingerprint while logged in.'),
          ),
        );
      }
      setState(() {
        _enabled = ok ? value : _enabled;
        _busy = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    if (_enabled == null) {
      return const ListTile(title: Text('Fingerprint login'), subtitle: Text('Loading...'));
    }
    return SwitchListTile(
      contentPadding: EdgeInsets.zero,
      secondary: Icon(Icons.fingerprint, color: pp.mintDark),
      title: const Text('Fingerprint login'),
      subtitle: const Text('Unlock with fingerprint on login screen'),
      value: _enabled!,
      onChanged: _busy ? null : _toggle,
    );
  }
}

class _ThemeOption extends StatelessWidget {
  const _ThemeOption({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
    this.logoPreview,
  });

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;
  final Widget? logoPreview;

  @override
  Widget build(BuildContext context) {
    final pp = context.pp;
    final cs = context.cs;

    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: logoPreview ?? Icon(icon, color: selected ? pp.primary : pp.textSecondary),
      title: Text(label, style: TextStyle(color: cs.onSurface, fontWeight: selected ? FontWeight.w600 : FontWeight.w400)),
      trailing: selected ? Icon(Icons.check_circle, color: pp.primary) : null,
      onTap: onTap,
    );
  }
}
