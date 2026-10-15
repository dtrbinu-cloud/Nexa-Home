import 'package:flutter/material.dart';
import 'package:camera_app/core/storage.dart';
import 'package:camera_app/screens/camera_live_screen.dart';
import 'package:camera_app/screens/pairing_screen.dart';
import 'package:camera_app/theme/tokens.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final isPaired = await CameraStorage.isPaired();
  runApp(CameraApp(isPaired: isPaired));
}

class CameraApp extends StatelessWidget {
  final bool isPaired;

  const CameraApp({super.key, required this.isPaired});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Rumah Camera',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark(),
      home: isPaired ? const CameraLiveScreen() : const PairingScreen(),
    );
  }
}
