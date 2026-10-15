import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_switch.dart';
import 'package:app/theme/tokens.dart';

class DeviceTile extends StatelessWidget {
  final String name;
  final String subtitle;
  final bool isOn;
  final bool isOnline;
  final PhosphorIconData icon;
  final ValueChanged<bool>? onToggle;
  final VoidCallback? onTap;

  const DeviceTile({
    super.key,
    required this.name,
    required this.subtitle,
    required this.isOn,
    this.isOnline = true,
    required this.icon,
    this.onToggle,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final onBg = isDark ? AppColors.darkAccentLight : AppColors.lightAccentLight;
    final offBg = isDark ? AppColors.darkSurface : AppColors.lightSurface;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;

    final tileBg = !isOnline
        ? (isDark ? AppColors.darkSubtle : AppColors.lightSubtle)
        : (isOn ? onBg : offBg);

    final opacity = isOnline ? 1.0 : 0.6;

    final content = AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: tileBg,
        borderRadius: AppRadius.borderTile, // Radius 24
      ),
      padding: const EdgeInsets.all(AppSpacing.space4),
      child: Opacity(
        opacity: opacity,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                PhosphorIcon(
                  icon,
                  size: AppDimensions.iconSizeMd,
                  color: isOn && isOnline ? accent : textSec,
                ),
                if (isOnline && onToggle != null)
                  AppSwitch(
                    value: isOn,
                    onChanged: onToggle,
                    semanticLabel: 'Saklar $name',
                  ),
              ],
            ),
            const SizedBox(height: AppSpacing.space3),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  name,
                  style: AppTypography.body(
                    text,
                    size: AppTypography.textSm, // 15px
                    weight: FontWeight.w600,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2.0),
                Text(
                  subtitle,
                  style: AppTypography.body(
                    isOn && isOnline ? accent : textSec,
                    size: AppTypography.textXs, // 13px
                    weight: FontWeight.w400,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ],
        ),
      ),
    );

    return Material(
      color: AppColors.transparent,
      borderRadius: AppRadius.borderTile,
      child: InkWell(
        onTap: onTap,
        borderRadius: AppRadius.borderTile,
        child: content,
      ),
    );
  }
}
