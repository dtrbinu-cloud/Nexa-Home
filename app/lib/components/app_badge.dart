import 'package:flutter/material.dart';
import 'package:app/theme/tokens.dart';

enum AppBadgeVariant { ok, warn, danger, neutral }

class AppBadge extends StatelessWidget {
  final String label;
  final AppBadgeVariant variant;
  final Widget? icon;

  const AppBadge({
    super.key,
    required this.label,
    this.variant = AppBadgeVariant.neutral,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    Color color;
    switch (variant) {
      case AppBadgeVariant.ok:
        color = AppColors.statusOk;
        break;
      case AppBadgeVariant.warn:
        color = AppColors.statusWarn;
        break;
      case AppBadgeVariant.danger:
        color = AppColors.statusDanger;
        break;
      case AppBadgeVariant.neutral:
        color = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.space2,
        vertical: AppSpacing.space1,
      ),
      decoration: BoxDecoration(
        color: AppColors.transparent,
        borderRadius: AppRadius.borderSm,
        border: Border.all(color: color, width: AppDimensions.borderWidth),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            icon!,
            const SizedBox(width: AppSpacing.space1),
          ],
          Text(
            label,
            style: AppTypography.mono(
              color,
              size: AppTypography.textXs,
              weight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
