import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/theme/tokens.dart';

class DangerBanner extends StatelessWidget {
  final String title;
  final int currentValue;
  final int threshold;
  final VoidCallback onTriggerAlarm;
  final VoidCallback onMuteAlarm;

  const DangerBanner({
    super.key,
    required this.title,
    required this.currentValue,
    required this.threshold,
    required this.onTriggerAlarm,
    required this.onMuteAlarm,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.statusDanger,
        borderRadius: AppRadius.borderCard, // Radius 20
      ),
      padding: const EdgeInsets.all(AppSpacing.space4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32.0,
                height: 32.0,
                decoration: BoxDecoration(
                  color: AppColors.lightSurface.withValues(alpha: 0.2),
                  shape: BoxShape.circle,
                ),
                alignment: Alignment.center,
                child: PhosphorIcon(
                  PhosphorIcons.warning(PhosphorIconsStyle.bold),
                  size: AppDimensions.iconSizeSm,
                  color: AppColors.lightSurface,
                ),
              ),
              const SizedBox(width: AppSpacing.space3),
              Expanded(
                child: Text(
                  title,
                  style: AppTypography.body(
                    AppColors.lightSurface,
                    size: AppTypography.textSm,
                    weight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.space2),
          Padding(
            padding: const EdgeInsets.only(left: 44.0),
            child: Text.rich(
              TextSpan(
                children: [
                  TextSpan(
                    text: '$currentValue ',
                    style: AppTypography.mono(
                      AppColors.lightSurface,
                      size: AppTypography.textSm,
                      weight: FontWeight.w600,
                    ),
                  ),
                  TextSpan(
                    text: 'dari batas ',
                    style: AppTypography.body(
                      AppColors.lightSurface.withValues(alpha: 0.8),
                      size: AppTypography.textSm,
                    ),
                  ),
                  TextSpan(
                    text: '$threshold',
                    style: AppTypography.mono(
                      AppColors.lightSurface,
                      size: AppTypography.textSm,
                      weight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.space4),
          Row(
            children: [
              Expanded(
                child: InkWell(
                  onTap: onTriggerAlarm,
                  borderRadius: AppRadius.borderSm,
                  child: Container(
                    height: AppDimensions.controlHeight,
                    decoration: BoxDecoration(
                      color: AppColors.lightSurface.withValues(alpha: 0.2),
                      borderRadius: AppRadius.borderSm,
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      'Bunyikan alarm',
                      style: AppTypography.body(
                        AppColors.lightSurface,
                        size: AppTypography.textSm,
                        weight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.space3),
              Expanded(
                child: InkWell(
                  onTap: onMuteAlarm,
                  borderRadius: AppRadius.borderSm,
                  child: Container(
                    height: AppDimensions.controlHeight,
                    decoration: const BoxDecoration(
                      color: AppColors.lightSurface,
                      borderRadius: AppRadius.borderSm,
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      'Matikan alarm',
                      style: AppTypography.body(
                        AppColors.statusDanger,
                        size: AppTypography.textSm,
                        weight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
