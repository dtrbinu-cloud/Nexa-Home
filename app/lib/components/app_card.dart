import 'package:flutter/material.dart';
import 'package:app/theme/tokens.dart';

class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;

  const AppCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(AppSpacing.space4),
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkSurface : AppColors.lightSurface;
    final border = isDark ? AppColors.darkBorder : AppColors.lightBorder;

    final container = Container(
      decoration: BoxDecoration(
        color: bg,
        borderRadius: AppRadius.borderMd,
        border: Border.all(color: border, width: AppDimensions.borderWidth),
      ),
      padding: padding,
      child: child,
    );

    if (onTap != null) {
      return Material(
        color: AppColors.transparent,
        borderRadius: AppRadius.borderMd,
        child: InkWell(
          onTap: onTap,
          borderRadius: AppRadius.borderMd,
          child: container,
        ),
      );
    }

    return container;
  }
}
