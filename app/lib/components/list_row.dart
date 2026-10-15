import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/theme/tokens.dart';

class ListRow extends StatelessWidget {
  final Widget? leading;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;
  final bool showDivider;
  final bool isDestructive;

  const ListRow({
    super.key,
    this.leading,
    required this.title,
    this.subtitle,
    this.trailing,
    this.onTap,
    this.showDivider = true,
    this.isDestructive = false,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDestructive
        ? AppColors.statusDanger
        : (isDark ? AppColors.darkText : AppColors.lightText);
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final border = isDark ? AppColors.darkBorder : AppColors.lightBorder;

    final rowContent = Container(
      constraints: const BoxConstraints(minHeight: AppDimensions.listRowMinHeight), // min 56px
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.space4,
        vertical: AppSpacing.space3,
      ),
      decoration: showDivider
          ? BoxDecoration(
              border: Border(
                bottom: BorderSide(
                  color: border,
                  width: AppDimensions.borderWidth, // 1px
                ),
              ),
            )
          : null,
      child: Row(
        children: [
          if (leading != null) ...[
            leading!,
            const SizedBox(width: AppSpacing.space3),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  title,
                  style: AppTypography.body(
                    text,
                    size: AppTypography.textSm,
                    weight: isDestructive ? FontWeight.w600 : FontWeight.w500,
                  ),
                ),
                if (subtitle != null) ...[
                  const SizedBox(height: 2.0),
                  Text(
                    subtitle!,
                    style: AppTypography.body(
                      textSec,
                      size: AppTypography.textXs,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (trailing != null) ...[
            const SizedBox(width: AppSpacing.space3),
            trailing!,
          ] else if (onTap != null) ...[
            PhosphorIcon(
              PhosphorIcons.caretRight(),
              size: AppDimensions.iconSizeSm,
              color: textSec,
            ),
          ],
        ],
      ),
    );

    if (onTap != null) {
      return Material(
        color: AppColors.transparent,
        child: InkWell(
          onTap: onTap,
          child: rowContent,
        ),
      );
    }

    return rowContent;
  }
}
