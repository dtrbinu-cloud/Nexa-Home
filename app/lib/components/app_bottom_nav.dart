import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/theme/tokens.dart';

class AppBottomNav extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;

  const AppBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final surface = isDark ? AppColors.darkSurface : AppColors.lightSurface;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final tintOn = isDark ? AppColors.darkAccentLight : AppColors.lightAccentLight;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;

    return Container(
      height: 80.0,
      color: surface,
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            _buildTabItem(
              index: 0,
              label: 'Beranda',
              iconRegular: PhosphorIcons.house(),
              iconFill: PhosphorIconsFill.house,
              isActive: currentIndex == 0,
              accent: accent,
              tintOn: tintOn,
              textSec: textSec,
            ),
            _buildTabItem(
              index: 1,
              label: 'Kamera',
              iconRegular: PhosphorIcons.videoCamera(),
              iconFill: PhosphorIconsFill.videoCamera,
              isActive: currentIndex == 1,
              accent: accent,
              tintOn: tintOn,
              textSec: textSec,
            ),
            _buildTabItem(
              index: 2,
              label: 'Asisten',
              iconRegular: PhosphorIcons.microphone(),
              iconFill: PhosphorIconsFill.microphone,
              isActive: currentIndex == 2,
              accent: accent,
              tintOn: tintOn,
              textSec: textSec,
            ),
            _buildTabItem(
              index: 3,
              label: 'Lainnya',
              iconRegular: PhosphorIcons.dotsThree(),
              iconFill: PhosphorIconsFill.dotsThree,
              isActive: currentIndex == 3,
              accent: accent,
              tintOn: tintOn,
              textSec: textSec,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTabItem({
    required int index,
    required String label,
    required PhosphorIconData iconRegular,
    required PhosphorIconData iconFill,
    required bool isActive,
    required Color accent,
    required Color tintOn,
    required Color textSec,
  }) {
    return Expanded(
      child: Semantics(
        label: 'Tab $label',
        selected: isActive,
        button: true,
        child: InkWell(
          onTap: () => onTap(index),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 64.0,
                height: 32.0,
                decoration: BoxDecoration(
                  color: isActive ? tintOn : AppColors.transparent,
                  borderRadius: const BorderRadius.all(Radius.circular(AppRadius.pill)),
                ),
                alignment: Alignment.center,
                child: PhosphorIcon(
                  isActive ? iconFill : iconRegular,
                  size: AppDimensions.iconSizeMd, // 24px
                  color: isActive ? accent : textSec,
                ),
              ),
              const SizedBox(height: 4.0),
              Text(
                label,
                style: AppTypography.body(
                  isActive ? accent : textSec,
                  size: AppTypography.textXs,
                  weight: isActive ? FontWeight.w600 : FontWeight.w400,
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
