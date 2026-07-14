import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/constants/app_spacing.dart';
import '../../../../core/constants/app_text_styles.dart';
import '../../../../core/network/network_exceptions.dart';
import '../../../../core/router/app_routes.dart';
import '../../../../shared/widgets/pp_button.dart';
import '../../../../shared/widgets/pp_form_scroll.dart';
import '../../../../shared/widgets/pp_screen_header.dart';
import '../../data/auth_repository.dart';
import '../../presentation/providers/onboarding_provider.dart';

class KycScreen extends ConsumerStatefulWidget {
  const KycScreen({super.key});

  @override
  ConsumerState<KycScreen> createState() => _KycScreenState();
}

class _KycScreenState extends ConsumerState<KycScreen> {
  final _nameController = TextEditingController();
  final _cnicController = TextEditingController();
  final _picker = ImagePicker();
  String? _frontPath;
  String? _backPath;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _nameController.dispose();
    _cnicController.dispose();
    super.dispose();
  }

  Future<void> _pick(ImageSource source, bool front) async {
    final file = await _picker.pickImage(source: source, imageQuality: 85);
    if (file == null || !mounted) return;
    setState(() {
      if (front) {
        _frontPath = file.path;
      } else {
        _backPath = file.path;
      }
    });
  }

  Future<void> _showPickOptions(bool front) async {
    final label = front ? 'CNIC front' : 'CNIC back';
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.lg,
            AppSpacing.sm,
            AppSpacing.lg,
            AppSpacing.lg,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Add $label', style: AppTextStyles.title(context)),
              const SizedBox(height: AppSpacing.md),
              ListTile(
                leading: const Icon(Icons.photo_library_outlined, color: AppColors.primary),
                title: const Text('Choose from gallery'),
                subtitle: const Text('Pick an existing photo'),
                onTap: () => Navigator.pop(context, ImageSource.gallery),
              ),
              ListTile(
                leading: const Icon(Icons.camera_alt_outlined, color: AppColors.primary),
                title: const Text('Take a photo'),
                subtitle: const Text('Use camera now'),
                onTap: () => Navigator.pop(context, ImageSource.camera),
              ),
            ],
          ),
        ),
      ),
    );
    if (source != null) {
      await _pick(source, front);
    }
  }

  String _cnicDigits() => _cnicController.text.replaceAll(RegExp(r'\D'), '');

  Future<void> _submit() async {
    final name = _nameController.text.trim();
    final cnic = _cnicDigits();
    if (name.length < 2) {
      setState(() => _error = 'Enter your full name');
      return;
    }
    if (cnic.length != 13) {
      setState(() => _error = 'CNIC must be 13 digits');
      return;
    }
    if (_frontPath == null) {
      setState(() => _error = 'Add CNIC front photo');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await ref.read(authRepositoryProvider).submitKyc(
            fullName: name,
            cnic: cnic,
            frontImagePath: _frontPath!,
            backImagePath: _backPath,
          );
      await ref.read(onboardingControllerProvider.notifier).refresh();
      if (!mounted) return;
      context.go(AppRoutes.palmEnroll);
    } on DioException catch (e) {
      setState(() => _error = dioErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verify identity')),
      body: PpFormScroll(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const PpScreenHeader(
              title: 'KYC verification',
              subtitle: 'CNIC and photo - auto-approved in dev mode',
            ),
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(labelText: 'Full name'),
            ),
            const SizedBox(height: AppSpacing.md),
            TextField(
              controller: _cnicController,
              keyboardType: TextInputType.number,
              inputFormatters: [
                FilteringTextInputFormatter.digitsOnly,
                LengthLimitingTextInputFormatter(13),
              ],
              decoration: const InputDecoration(
                labelText: 'CNIC',
                hintText: '13 digits',
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            _photoRow('CNIC front', _frontPath, () => _showPickOptions(true)),
            const SizedBox(height: AppSpacing.sm),
            _photoRow('CNIC back (optional)', _backPath, () => _showPickOptions(false)),
            if (_error != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text(_error!, style: AppTextStyles.body(context).copyWith(color: AppColors.error)),
            ],
            const SizedBox(height: AppSpacing.xl),
            PpButton(
              label: _loading ? 'Submitting…' : 'Submit KYC',
              onPressed: _loading ? null : _submit,
            ),
          ],
        ),
      ),
    );
  }

  Widget _photoRow(String label, String? path, VoidCallback onTap) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(
        path != null ? Icons.check_circle : Icons.add_photo_alternate_outlined,
        color: AppColors.primary,
      ),
      label: Text(path != null ? '$label added — tap to change' : 'Add $label'),
    );
  }
}
