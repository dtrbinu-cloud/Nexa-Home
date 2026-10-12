import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/screens/tabs/assistant_tab.dart';
import 'package:app/screens/tabs/cameras_tab.dart';
import 'package:app/screens/tabs/devices_tab.dart';
import 'package:app/screens/tabs/family_tab.dart';
import 'package:app/screens/tabs/home_tab.dart';
import 'package:app/screens/tabs/settings_tab.dart';
import 'package:app/theme/tokens.dart';

class ShellScreen extends StatefulWidget {
  const ShellScreen({super.key});

  @override
  State<ShellScreen> createState() => _ShellScreenState();
}

class _ShellScreenState extends State<ShellScreen> {
  int _currentIndex = 0;

  final _tabs = const [
    HomeTab(),
    DevicesTab(),
    AssistantTab(),
    CamerasTab(),
    FamilyTab(),
    SettingsTab(),
  ];

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final surface = isDark ? AppColors.darkSurface : AppColors.lightSurface;
    final border = isDark ? AppColors.darkBorder : AppColors.lightBorder;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _tabs,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: surface,
          border: Border(
            top: BorderSide(color: border, width: AppDimensions.borderWidth),
          ),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (idx) => setState(() => _currentIndex = idx),
          backgroundColor: surface,
          selectedItemColor: accent,
          unselectedItemColor: textSec,
          selectedLabelStyle: AppTypography.body(
            accent,
            size: AppTypography.textXs,
            weight: FontWeight.w600,
          ),
          unselectedLabelStyle: AppTypography.body(
            textSec,
            size: AppTypography.textXs,
          ),
          items: [
            BottomNavigationBarItem(
              icon: Icon(PhosphorIcons.house(), size: AppDimensions.iconSizeSm),
              label: 'Beranda',
            ),
            BottomNavigationBarItem(
              icon: Icon(PhosphorIcons.cpu(), size: AppDimensions.iconSizeSm),
              label: 'Perangkat',
            ),
            BottomNavigationBarItem(
              icon: Icon(PhosphorIcons.chatCircleDots(), size: AppDimensions.iconSizeSm),
              label: 'Asisten',
            ),
            BottomNavigationBarItem(
              icon: Icon(PhosphorIcons.videoCamera(), size: AppDimensions.iconSizeSm),
              label: 'Kamera',
            ),
            BottomNavigationBarItem(
              icon: Icon(PhosphorIcons.users(), size: AppDimensions.iconSizeSm),
              label: 'Keluarga',
            ),
            BottomNavigationBarItem(
              icon: Icon(PhosphorIcons.gear(), size: AppDimensions.iconSizeSm),
              label: 'Pengaturan',
            ),
          ],
        ),
      ),
    );
  }
}
