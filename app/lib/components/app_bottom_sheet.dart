import 'package:flutter/material.dart';
import 'package:app/theme/tokens.dart';

Future<T?> showAppBottomSheet<T>({
  required BuildContext context,
  required Widget child,
  String? title,
  bool isDismissible = true,
}) {
  final isDark = Theme.of(context).brightness == Brightness.dark;
  final surface = isDark ? AppColors.darkSurface : AppColors.lightSurface;
  final text = isDark ? AppColors.darkText : AppColors.lightText;
  final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

  return showModalBottomSheet<T>(
    context: context,
    isDismissible: isDismissible,
    isScrollControlled: true,
    backgroundColor: AppColors.transparent,
    builder: (context) {
      return Container(
        decoration: BoxDecoration(
          color: surface,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(AppRadius.card),
            topRight: Radius.circular(AppRadius.card),
          ),
        ),
        padding: EdgeInsets.only(
          left: AppDimensions.screenMargin,
          right: AppDimensions.screenMargin,
          top: AppSpacing.space3,
          bottom: MediaQuery.of(context).viewInsets.bottom + AppSpacing.space6,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 36.0,
                height: 4.0,
                decoration: BoxDecoration(
                  color: subtle,
                  borderRadius: AppRadius.borderBar,
                ),
              ),
            ),
            if (title != null) ...[
              const SizedBox(height: AppSpacing.space4),
              Text(
                title,
                style: AppTypography.body(
                  text,
                  size: AppTypography.textMd,
                  weight: FontWeight.w600,
                ),
              ),
            ],
            const SizedBox(height: AppSpacing.space4),
            child,
          ],
        ),
      );
    },
  );
}
