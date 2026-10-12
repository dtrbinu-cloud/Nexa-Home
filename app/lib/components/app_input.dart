import 'package:flutter/material.dart';
import 'package:app/theme/tokens.dart';

class AppInput extends StatelessWidget {
  final String? label;
  final String? hint;
  final TextEditingController? controller;
  final bool obscureText;
  final TextInputType? keyboardType;
  final ValueChanged<String>? onChanged;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final bool autofocus;

  const AppInput({
    super.key,
    this.label,
    this.hint,
    this.controller,
    this.obscureText = false,
    this.keyboardType,
    this.onChanged,
    this.prefixIcon,
    this.suffixIcon,
    this.autofocus = false,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final surface = isDark ? AppColors.darkSurface : AppColors.lightSurface;
    final border = isDark ? AppColors.darkBorder : AppColors.lightBorder;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null) ...[
          Text(
            label!,
            style: AppTypography.body(
              textSec,
              size: AppTypography.textXs,
              weight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: AppSpacing.space1),
        ],
        SizedBox(
          height: AppDimensions.controlHeight,
          child: TextField(
            controller: controller,
            obscureText: obscureText,
            keyboardType: keyboardType,
            onChanged: onChanged,
            autofocus: autofocus,
            style: AppTypography.body(text, size: AppTypography.textSm),
            cursorColor: accent,
            decoration: InputDecoration(
              isDense: true,
              hintText: hint,
              hintStyle: AppTypography.body(textSec, size: AppTypography.textSm),
              filled: true,
              fillColor: surface,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.space3,
                vertical: AppSpacing.space2,
              ),
              prefixIcon: prefixIcon,
              suffixIcon: suffixIcon,
              enabledBorder: OutlineInputBorder(
                borderRadius: AppRadius.borderSm,
                borderSide: BorderSide(
                  color: border,
                  width: AppDimensions.borderWidth,
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: AppRadius.borderSm,
                borderSide: BorderSide(
                  color: accent,
                  width: AppDimensions.borderWidth,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
