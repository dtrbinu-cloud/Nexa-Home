import 'package:flutter/material.dart';
import 'package:app/theme/tokens.dart';

class AppToast {
  static void show(
    BuildContext context,
    String message, {
    bool isError = false,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkSurface : AppColors.lightSurface;
    final border = isError
        ? AppColors.statusDanger
        : (isDark ? AppColors.darkAccent : AppColors.lightAccent);
    final text = isDark ? AppColors.darkText : AppColors.lightText;

    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        elevation: 0,
        backgroundColor: AppColors.transparent,
        duration: const Duration(seconds: 3),
        behavior: SnackBarBehavior.floating,
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space4,
          vertical: AppSpacing.space2,
        ),
        content: Container(
          decoration: BoxDecoration(
            color: bg,
            borderRadius: AppRadius.borderSm,
            border: Border.all(color: border, width: AppDimensions.borderWidth),
          ),
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.space4,
            vertical: AppSpacing.space3,
          ),
          child: Text(
            message,
            style: AppTypography.body(
              text,
              size: AppTypography.textSm,
              weight: FontWeight.w500,
            ),
          ),
        ),
      ),
    );
  }
}
