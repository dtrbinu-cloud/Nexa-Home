import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/empty_state.dart';
import 'package:app/theme/tokens.dart';

class AssistantTab extends StatelessWidget {
  const AssistantTab({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final text = isDark ? AppColors.darkText : AppColors.lightText;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Icon(
              PhosphorIcons.chatCircleDots(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            const SizedBox(width: AppSpacing.space2),
            const Text('Asisten'),
          ],
        ),
      ),
      body: SafeArea(
        child: EmptyState(
          icon: Icon(
            PhosphorIcons.microphone(),
            size: AppDimensions.iconSizeMd * 2,
            color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
          ),
          title: 'Asisten Suara & Percakapan',
          description:
              'Integrasi LLM DeepSeek dengan function calling dan modul suara TTS/STT akan diaktifkan di Tahap 3.',
        ),
      ),
    );
  }
}
