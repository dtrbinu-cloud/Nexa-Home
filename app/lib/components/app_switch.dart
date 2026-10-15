import 'package:flutter/material.dart';
import 'package:app/theme/tokens.dart';

class AppSwitch extends StatelessWidget {
  final bool value;
  final ValueChanged<bool>? onChanged;
  final String? semanticLabel;

  const AppSwitch({
    super.key,
    required this.value,
    required this.onChanged,
    this.semanticLabel,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final inactiveBg = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;
    final thumbColor = isDark ? AppColors.darkText : AppColors.lightSurface;

    return Semantics(
      label: semanticLabel ?? 'Saklar',
      toggled: value,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onChanged == null ? null : () => onChanged!(!value),
        child: Container(
          constraints: const BoxConstraints(
            minWidth: 48.0,
            minHeight: 48.0,
          ),
          alignment: Alignment.center,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeInOut,
            width: AppDimensions.toggleWidth, // 56.0
            height: AppDimensions.toggleHeight, // 32.0
            padding: const EdgeInsets.all(3.0), // offset 3
            decoration: BoxDecoration(
              color: value ? accent : inactiveBg,
              borderRadius: const BorderRadius.all(Radius.circular(AppRadius.pill)),
            ),
            alignment: value ? Alignment.centerRight : Alignment.centerLeft,
            child: Container(
              width: AppDimensions.toggleThumbSize, // 26.0
              height: AppDimensions.toggleThumbSize, // 26.0
              decoration: BoxDecoration(
                color: thumbColor,
                shape: BoxShape.circle,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
