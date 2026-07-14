import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

/// Android FLAG_SECURE — blocks screenshots on wallet/payment screens.
abstract final class SecureScreenService {
  static const _channel = MethodChannel('pk.palmpay/secure_screen');
  static int _depth = 0;

  static Future<void> enable() async {
    if (kIsWeb || !Platform.isAndroid) return;
    _depth++;
    if (_depth > 1) return;
    try {
      await _channel.invokeMethod<void>('enable');
    } catch (_) {}
  }

  static Future<void> disable() async {
    if (kIsWeb || !Platform.isAndroid) return;
    if (_depth <= 0) return;
    _depth--;
    if (_depth > 0) return;
    try {
      await _channel.invokeMethod<void>('disable');
    } catch (_) {}
  }
}

/// Wraps payment/wallet screens with FLAG_SECURE on Android.
class SecureScreen extends StatefulWidget {
  const SecureScreen({super.key, required this.child});

  final Widget child;

  @override
  State<SecureScreen> createState() => _SecureScreenState();
}

class _SecureScreenState extends State<SecureScreen> {
  @override
  void initState() {
    super.initState();
    SecureScreenService.enable();
  }

  @override
  void dispose() {
    SecureScreenService.disable();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
