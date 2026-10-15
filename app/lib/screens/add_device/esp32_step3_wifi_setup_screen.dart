import 'package:flutter/material.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';
import 'package:app/components/app_button.dart';
import 'package:app/components/app_card.dart';
import 'package:app/components/app_input.dart';
import 'package:app/components/app_top_bar.dart';
import 'package:app/screens/add_device/esp32_step4_connecting_screen.dart';
import 'package:app/theme/tokens.dart';

class Esp32Step3WifiSetupScreen extends StatefulWidget {
  const Esp32Step3WifiSetupScreen({super.key});

  @override
  State<Esp32Step3WifiSetupScreen> createState() => _Esp32Step3WifiSetupScreenState();
}

class _Esp32Step3WifiSetupScreenState extends State<Esp32Step3WifiSetupScreen> {
  String _selectedWifi = 'Rumah-Utama';
  final _passwordController = TextEditingController(text: 'SandiRahasia123');
  bool _obscurePassword = true;

  @override
  void dispose() {
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final bg = isDark ? AppColors.darkBg : AppColors.lightBg;
    final text = isDark ? AppColors.darkText : AppColors.lightText;
    final textSec = isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary;
    final accent = isDark ? AppColors.darkAccent : AppColors.lightAccent;
    final subtle = isDark ? AppColors.darkSubtle : AppColors.lightSubtle;

    return Scaffold(
      backgroundColor: bg,
      appBar: AppTopBar(
        title: 'Setup WiFi',
        actions: [
          IconButton(
            tooltip: 'Bantuan',
            icon: PhosphorIcon(
              PhosphorIcons.question(),
              size: AppDimensions.iconSizeSm,
              color: text,
            ),
            onPressed: () {},
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Scrollable Content
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: AppDimensions.screenMargin),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: AppSpacing.space2),

                    // Stepper 3 dari 4
                    Text(
                      'Langkah 3 dari 4',
                      style: AppTypography.body(
                        textSec,
                        size: AppTypography.textXs,
                        weight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.space2),
                    Row(
                      children: [
                        Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                        const SizedBox(width: 6),
                        Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                        const SizedBox(width: 6),
                        Expanded(child: Container(height: 4, decoration: BoxDecoration(color: accent, borderRadius: AppRadius.borderBar))),
                        const SizedBox(width: 6),
                        Expanded(child: Container(height: 4, decoration: BoxDecoration(color: subtle, borderRadius: AppRadius.borderBar))),
                      ],
                    ),

                    const SizedBox(height: AppDimensions.sectionGap),

                    Text(
                      'Hubungkan ke WiFi rumah',
                      style: AppTypography.body(
                        text,
                        size: AppTypography.textLg,
                        weight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.space2),
                    Text(
                      'Pilih jaringan WiFi rumah 2.4 GHz untuk modul.',
                      style: AppTypography.body(textSec, size: AppTypography.textSm),
                    ),

                    const SizedBox(height: AppDimensions.sectionGap),

                    // Daftar Jaringan WiFi
                    AppCard(
                      padding: EdgeInsets.zero,
                      child: Column(
                        children: [
                          // WiFi 1: Rumah-Utama (Selected)
                          _buildWifiRow(
                            ssid: 'Rumah-Utama',
                            freq: '2.4 GHz',
                            isSelected: _selectedWifi == 'Rumah-Utama',
                            isSupported: true,
                            onTap: () => setState(() => _selectedWifi = 'Rumah-Utama'),
                            isDark: isDark,
                            text: text,
                            textSec: textSec,
                            accent: accent,
                            showDivider: true,
                          ),
                          // WiFi 2: Rumah-Lantai2
                          _buildWifiRow(
                            ssid: 'Rumah-Lantai2',
                            freq: '2.4 GHz',
                            isSelected: _selectedWifi == 'Rumah-Lantai2',
                            isSupported: true,
                            onTap: () => setState(() => _selectedWifi = 'Rumah-Lantai2'),
                            isDark: isDark,
                            text: text,
                            textSec: textSec,
                            accent: accent,
                            showDivider: true,
                          ),
                          // WiFi 3: Tetangga_Net (5 GHz - Tidak cocok)
                          _buildWifiRow(
                            ssid: 'Tetangga_Net',
                            freq: '5 GHz',
                            isSelected: false,
                            isSupported: false,
                            onTap: null,
                            isDark: isDark,
                            text: text,
                            textSec: textSec,
                            accent: accent,
                            showDivider: false,
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: AppDimensions.cardGap),

                    // Info: Alat hanya mendukung 2.4 GHz
                    AppCard(
                      backgroundColor: subtle,
                      padding: const EdgeInsets.all(AppSpacing.space3),
                      child: Row(
                        children: [
                          PhosphorIcon(
                            PhosphorIcons.info(),
                            size: AppDimensions.iconSizeSm,
                            color: textSec,
                          ),
                          const SizedBox(width: AppSpacing.space2),
                          Expanded(
                            child: Text(
                              'Alat hanya mendukung WiFi 2.4 GHz.',
                              style: AppTypography.body(textSec, size: AppTypography.textXs),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: AppDimensions.sectionGap),

                    // Input Kata Sandi WiFi
                    AppInput(
                      label: 'Kata sandi WiFi',
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      suffixIcon: IconButton(
                        icon: PhosphorIcon(
                          _obscurePassword ? PhosphorIcons.eyeSlash() : PhosphorIcons.eye(),
                          size: AppDimensions.iconSizeSm,
                          color: textSec,
                        ),
                        onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                      ),
                    ),

                    const SizedBox(height: AppDimensions.cardGap),

                    // Info Kode Pairing (read only display)
                    Text(
                      'Kode pairing',
                      style: AppTypography.body(
                        textSec,
                        size: AppTypography.textXs,
                        weight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.space2),
                    Container(
                      height: AppDimensions.controlHeight,
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.space4),
                      decoration: BoxDecoration(
                        color: subtle,
                        borderRadius: AppRadius.borderSm,
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            '482  915',
                            style: AppTypography.mono(
                              text,
                              size: AppTypography.textSm,
                              weight: FontWeight.w600,
                            ),
                          ),
                          PhosphorIcon(
                            PhosphorIcons.lock(),
                            size: AppDimensions.iconSizeSm,
                            color: textSec,
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: AppSpacing.space6),
                  ],
                ),
              ),
            ),

            // STICKY BOTTOM BUTTON (tidak terpotong di bawah)
            Container(
              padding: const EdgeInsets.all(AppDimensions.screenMargin),
              color: bg,
              child: AppButton(
                label: 'Hubungkan',
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const Esp32Step4ConnectingScreen()),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWifiRow({
    required String ssid,
    required String freq,
    required bool isSelected,
    required bool isSupported,
    required VoidCallback? onTap,
    required bool isDark,
    required Color text,
    required Color textSec,
    required Color accent,
    required bool showDivider,
  }) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.space4,
          vertical: AppSpacing.space3,
        ),
        decoration: showDivider
            ? BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                    width: AppDimensions.borderWidth,
                  ),
                ),
              )
            : null,
        child: Row(
          children: [
            PhosphorIcon(
              PhosphorIcons.wifiHigh(),
              size: AppDimensions.iconSizeMd,
              color: isSupported ? (isSelected ? accent : text) : textSec,
            ),
            const SizedBox(width: AppSpacing.space3),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Flexible(
                        child: Text(
                          ssid,
                          style: AppTypography.body(
                            isSupported ? text : textSec,
                            size: AppTypography.textSm,
                            weight: FontWeight.w600,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 4),
                      PhosphorIcon(
                        PhosphorIcons.lock(),
                        size: 14,
                        color: textSec,
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    freq,
                    style: AppTypography.mono(textSec, size: AppTypography.textXs),
                  ),
                ],
              ),
            ),
            if (!isSupported)
              Text(
                'Tidak cocok',
                style: AppTypography.body(textSec, size: AppTypography.textXs),
              )
            else if (isSelected)
              PhosphorIcon(
                PhosphorIcons.checkCircle(PhosphorIconsStyle.fill),
                size: AppDimensions.iconSizeMd,
                color: accent,
              )
            else
              PhosphorIcon(
                PhosphorIcons.caretRight(),
                size: AppDimensions.iconSizeSm,
                color: textSec,
              ),
          ],
        ),
      ),
    );
  }
}
