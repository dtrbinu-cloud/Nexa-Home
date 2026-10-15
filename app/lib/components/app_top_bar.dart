import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/theme/tokens.dart';

class AppTopBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final bool showBackButton;
  final VoidCallback? onBack;
  final List<Widget>? actions;
  final bool isLargeTitle;

  const AppTopBar({
    super.key,
    required this.title,
    this.showBackButton = true,
    this.onBack,
    this.actions,
    this.isLargeTitle = false,
  });

  @override
  Size get preferredSize => Size.fromHeight(isLargeTitle ? 72.0 : 56.0);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final textColor = isDark ? AppColors.darkText : AppColors.lightText;

    return Container(
      color: bg,
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
          child: Row(
            children: [
              if (showBackButton) ...[
                IconButton(
                  icon: PhosphorIcon(
                    PhosphorIcons.arrowLeft(),
                    size: AppDimensions.iconSizeMd,
                    color: textColor,
                  ),
                  tooltip: 'Kembali',
                  onPressed: onBack ?? () => Navigator.of(context).maybePop(),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
                ),
                const SizedBox(width: AppSpacing.space2),
              ],
              Expanded(
                child: Text(
                  title,
                  style: isLargeTitle
                      ? AppTypography.body(
                          textColor,
                          size: AppTypography.textXl, // 32px
                          weight: FontWeight.w600,
                        )
                      : AppTypography.body(
                          textColor,
                          size: AppTypography.textMd, // 18px
                          weight: FontWeight.w600,
                        ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (actions != null) ...actions!,
            ],
          ),
        ),
      ),
    );
  }
}
