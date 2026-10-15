import 'package:flutter/material.dart';
import 'package:app/theme/tokens.dart';

class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final Color? backgroundColor;

  const AppCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(AppSpacing.space4),
    this.onTap,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = backgroundColor ?? (isDark ? AppColors.darkSurface : AppColors.lightSurface);

    final container = Container(
      decoration: BoxDecoration(
        color: bg,
        borderRadius: AppRadius.borderCard,
      ),
      padding: padding,
      child: child,
    );

    if (onTap != null) {
      return Material(
        color: AppColors.transparent,
        borderRadius: AppRadius.borderCard,
        child: InkWell(
          onTap: onTap,
          borderRadius: AppRadius.borderCard,
          child: container,
        ),
      );
    }

    return container;
  }
}
