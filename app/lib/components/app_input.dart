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
  final bool isMono;
  final int? maxLines;

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
    this.isMono = false,
    this.maxLines = 1,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;
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
              weight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: AppSpacing.space2),
        ],
        Container(
          constraints: BoxConstraints(
            minHeight: AppDimensions.controlHeight,
          ),
          child: TextField(
            controller: controller,
            obscureText: obscureText,
            keyboardType: keyboardType,
            onChanged: onChanged,
            autofocus: autofocus,
            maxLines: maxLines,
            style: isMono
                ? AppTypography.mono(text, size: AppTypography.textSm)
                : AppTypography.body(text, size: AppTypography.textSm),
            cursorColor: accent,
            decoration: InputDecoration(
              isDense: true,
              hintText: hint,
              hintStyle: AppTypography.body(textSec, size: AppTypography.textSm),
              filled: true,
              fillColor: subtle,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.space4,
                vertical: 14.0,
              ),
              prefixIcon: prefixIcon,
              suffixIcon: suffixIcon,
              enabledBorder: const OutlineInputBorder(
                borderRadius: AppRadius.borderSm,
                borderSide: BorderSide.none,
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: AppRadius.borderSm,
                borderSide: BorderSide(
                  color: accent,
                  width: 2.0,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
