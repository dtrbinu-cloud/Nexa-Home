import 'package:flutter/material.dart';
import 'package:app/theme/tokens.dart';

enum AppButtonVariant { primary, secondary, danger }

class AppButton extends StatelessWidget {
  final String label;
  final VoidCallback? onPressed;
  final AppButtonVariant variant;
  final bool isLoading;
  final Widget? icon;
  final bool isFullWidth;

  const AppButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.variant = AppButtonVariant.primary,
    this.isLoading = false,
    this.icon,
    this.isFullWidth = true,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    Color bg;
    Color border;
    Color textColor;

    switch (variant) {
      case AppButtonVariant.primary:
        bg = isDark ? AppColors.darkAccent : AppColors.lightAccent;
        border = bg;
        textColor = isDark ? AppColors.darkAccentText : AppColors.lightAccentText;
        break;
      case AppButtonVariant.secondary:
        bg = isDark ? AppColors.darkSurface : AppColors.lightSurface;
        border = isDark ? AppColors.darkBorder : AppColors.lightBorder;
        textColor = isDark ? AppColors.darkText : AppColors.lightText;
        break;
      case AppButtonVariant.danger:
        bg = AppColors.statusDanger;
        border = AppColors.statusDanger;
        textColor = AppColors.lightSurface;
        break;
    }

    Widget content;
    if (isLoading) {
      content = SizedBox(
        width: AppDimensions.iconSizeSm,
        height: AppDimensions.iconSizeSm,
        child: CircularProgressIndicator(
          strokeWidth: AppDimensions.borderWidth * 2,
          valueColor: AlwaysStoppedAnimation<Color>(textColor),
        ),
      );
    } else {
      content = Row(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (icon != null) ...[
            icon!,
            const SizedBox(width: AppSpacing.space2),
          ],
          Text(
            label,
            style: AppTypography.body(
              textColor,
              weight: FontWeight.w600,
              size: AppTypography.textSm,
            ),
          ),
        ],
      );
    }

    final btn = Material(
      color: bg,
      shape: RoundedRectangleBorder(
        borderRadius: AppRadius.borderSm,
        side: BorderSide(color: border, width: AppDimensions.borderWidth),
      ),
      child: InkWell(
        onTap: isLoading ? null : onPressed,
        borderRadius: AppRadius.borderSm,
        child: Container(
          height: AppDimensions.controlHeight,
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4),
          alignment: Alignment.center,
          child: content,
        ),
      ),
    );

    if (isFullWidth) {
      return SizedBox(width: double.infinity, child: btn);
    }
    return btn;
  }
}
