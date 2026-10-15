// ==============================================================================
// BERKAS OTOMATIS DIGENERATE - JANGAN EDIT MANUAL!
// Sumber kebenaran tunggal: web/src/design-tokens.json
// Dibuat oleh scripts/gen_flutter_theme.py
// ==============================================================================

import 'package:flutter/material.dart';

class AppColors {
  // Theme Terang (Light)
  static const Color lightBg = Color(0xFFF4F1EA);
  static const Color lightSurface = Color(0xFFFBF9F4);
  static const Color lightSubtle = Color(0xFFECE7DC);
  static const Color lightBorder = Color(0xFFE5E0D5);
  static const Color lightBorderSubtle = Color(0xFFE5E0D5);
  static const Color lightText = Color(0xFF1F2421);
  static const Color lightTextSecondary = Color(0xFF5E655F);
  static const Color lightAccent = Color(0xFF2F6B5B);
  static const Color lightAccentHover = Color(0xFF255849);
  static const Color lightAccentLight = Color(0xFFE4EDE9);
  static const Color lightAccentText = Color(0xFFFBF9F4);

  // Theme Gelap (Dark)
  static const Color darkBg = Color(0xFF151816);
  static const Color darkSurface = Color(0xFF1D211E);
  static const Color darkSubtle = Color(0xFF232824);
  static const Color darkBorder = Color(0xFF2D332F);
  static const Color darkBorderSubtle = Color(0xFF2D332F);
  static const Color darkText = Color(0xFFE8E6DF);
  static const Color darkTextSecondary = Color(0xFF8A938C);
  static const Color darkAccent = Color(0xFF5FA08E);
  static const Color darkAccentHover = Color(0xFF71B4A1);
  static const Color darkAccentLight = Color(0xFF1F2C27);
  static const Color darkAccentText = Color(0xFF151816);

  // Status (Universal)
  static const Color statusOk = Color(0xFF4C7A3F);
  static const Color statusWarn = Color(0xFFB7791F);
  static const Color statusDanger = Color(0xFFB23A2E);
  static const Color transparent = Color(0x00000000);
}

class AppSpacing {
  static const double space1 = 4.0; // 4px
  static const double space2 = 8.0; // 8px
  static const double space3 = 12.0; // 12px
  static const double space4 = 16.0; // 16px
  static const double space5 = 20.0; // 20px
  static const double space6 = 24.0; // 24px
  static const double space8 = 32.0; // 32px
}

class AppRadius {
  static const double sm = 12.0; // 12px (button, input)
  static const double md = 20.0; // 20px (card, panel)
  static const double lg = 24.0; // 24px (device tile)
  static const double chip = 8.0; // 8px (chip)
  static const double button = 12.0;
  static const double input = 12.0;
  static const double card = 20.0;
  static const double tile = 24.0;
  static const double pill = 16.0;
  static const double bar = 2.0;
  static const double full = 999.0;

  static const Radius radiusSm = Radius.circular(sm);
  static const Radius radiusMd = Radius.circular(md);
  static const Radius radiusLg = Radius.circular(lg);
  static const Radius radiusChip = Radius.circular(chip);
  static const Radius radiusBar = Radius.circular(bar);
  static const BorderRadius borderSm = BorderRadius.all(radiusSm);
  static const BorderRadius borderMd = BorderRadius.all(radiusMd);
  static const BorderRadius borderLg = BorderRadius.all(radiusLg);
  static const BorderRadius borderChip = BorderRadius.all(radiusChip);
  static const BorderRadius borderCard = BorderRadius.all(Radius.circular(card));
  static const BorderRadius borderTile = BorderRadius.all(Radius.circular(tile));
  static const BorderRadius borderButton = BorderRadius.all(Radius.circular(button));
  static const BorderRadius borderPill = BorderRadius.all(Radius.circular(pill));
  static const BorderRadius borderBar = BorderRadius.all(Radius.circular(bar));
}

class AppDimensions {
  static const double controlHeight = 48.0;
  static const double borderWidth = 1.0;
  static const double listRowMinHeight = 56.0;
  static const double toggleWidth = 56.0;
  static const double toggleHeight = 32.0;
  static const double toggleThumbSize = 26.0;
  static const double screenMargin = 16.0;
  static const double screenMarginAuth = 24.0;
  static const double cardGap = 12.0;
  static const double sectionGap = 24.0;
  static const double iconSizeSm = 20.0;
  static const double iconSizeMd = 24.0;
  static const double iconSizeLg = 32.0;
}

class AppTypography {
  static const String fontBody = 'Public Sans';
  static const String fontMono = 'IBM Plex Mono';

  static const double textXs = 13.0;
  static const double textSm = 15.0;
  static const double textMd = 18.0;
  static const double textLg = 24.0;
  static const double textXl = 32.0;

  static TextStyle body(Color color, {FontWeight weight = FontWeight.w400, double size = textSm}) {
    return TextStyle(
      fontFamily: fontBody,
      fontSize: size,
      fontWeight: weight,
      color: color,
      height: 1.5,
    );
  }

  static TextStyle mono(Color color, {FontWeight weight = FontWeight.w400, double size = textSm}) {
    return TextStyle(
      fontFamily: fontMono,
      fontSize: size,
      fontWeight: weight,
      color: color,
      height: 1.4,
    );
  }
}

class AppTheme {
  static ThemeData light() {
    return ThemeData(
      useMaterial3: false,
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.lightBg,
      primaryColor: AppColors.lightAccent,
      fontFamily: AppTypography.fontBody,
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.lightSurface,
        foregroundColor: AppColors.lightText,
        elevation: 0,
        scrolledUnderElevation: 0,
        shape: Border(
          bottom: BorderSide(
            color: AppColors.lightBorder,
            width: AppDimensions.borderWidth,
          ),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.lightSurface,
        selectedItemColor: AppColors.lightAccent,
        unselectedItemColor: AppColors.lightTextSecondary,
        elevation: 0,
        type: BottomNavigationBarType.fixed,
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.lightBorder,
        thickness: AppDimensions.borderWidth,
        space: 1,
      ),
    );
  }

  static ThemeData dark() {
    return ThemeData(
      useMaterial3: false,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.darkBg,
      primaryColor: AppColors.darkAccent,
      fontFamily: AppTypography.fontBody,
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.darkSurface,
        foregroundColor: AppColors.darkText,
        elevation: 0,
        scrolledUnderElevation: 0,
        shape: Border(
          bottom: BorderSide(
            color: AppColors.darkBorder,
            width: AppDimensions.borderWidth,
          ),
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.darkSurface,
        selectedItemColor: AppColors.darkAccent,
        unselectedItemColor: AppColors.darkTextSecondary,
        elevation: 0,
        type: BottomNavigationBarType.fixed,
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.darkBorder,
        thickness: AppDimensions.borderWidth,
        space: 1,
      ),
    );
  }
}
