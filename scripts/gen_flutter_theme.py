#!/usr/bin/env python3
"""
Generator Tema Flutter Otomatis — Smart Home "Rumah"
Membaca 'web/src/design-tokens.json' dan menghasilkan 'app/lib/theme/tokens.dart'.
Ini adalah satu-satunya berkas Dart yang dilegalkan mendefinisikan Color(0x...).
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TOKENS_JSON_PATH = ROOT_DIR / "web" / "src" / "design-tokens.json"
FLUTTER_THEME_OUT = ROOT_DIR / "app" / "lib" / "theme" / "tokens.dart"


def hex_to_flutter_color(hex_str: str) -> str:
    """Mengubah '#RRGGBB' menjadi 'Color(0xFFRRGGBB)'."""
    hex_clean = hex_str.strip().lstrip("#").upper()
    if len(hex_clean) == 6:
        return f"Color(0xFF{hex_clean})"
    elif len(hex_clean) == 8:
        return f"Color(0x{hex_clean})"
    raise ValueError(f"Format hex tidak dikenali: {hex_str}")


def generate_flutter_theme():
    print(f"[*] Membaca token dari {TOKENS_JSON_PATH}...")
    with open(TOKENS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    light = data["theme"]["light"]
    dark = data["theme"]["dark"]
    spacing = data["spacing"]
    radius = data["radius"]

    content = f"""// ==============================================================================
// BERKAS OTOMATIS DIGENERATE - JANGAN EDIT MANUAL!
// Sumber kebenaran tunggal: web/src/design-tokens.json
// Dibuat oleh scripts/gen_flutter_theme.py
// ==============================================================================

import 'package:flutter/material.dart';

class AppColors {{
  // Theme Terang (Light)
  static const Color lightBg = {hex_to_flutter_color(light["bg"])};
  static const Color lightSurface = {hex_to_flutter_color(light["surface"])};
  static const Color lightBorder = {hex_to_flutter_color(light["border"])};
  static const Color lightText = {hex_to_flutter_color(light["text"])};
  static const Color lightTextSecondary = {hex_to_flutter_color(light["textSecondary"])};
  static const Color lightAccent = {hex_to_flutter_color(light["accent"])};
  static const Color lightAccentHover = {hex_to_flutter_color(light["accentHover"])};
  static const Color lightAccentText = {hex_to_flutter_color(light["surface"])};

  // Theme Gelap (Dark)
  static const Color darkBg = {hex_to_flutter_color(dark["bg"])};
  static const Color darkSurface = {hex_to_flutter_color(dark["surface"])};
  static const Color darkBorder = {hex_to_flutter_color(dark["border"])};
  static const Color darkText = {hex_to_flutter_color(dark["text"])};
  static const Color darkTextSecondary = {hex_to_flutter_color(dark["textSecondary"])};
  static const Color darkAccent = {hex_to_flutter_color(dark["accent"])};
  static const Color darkAccentHover = {hex_to_flutter_color(dark["accentHover"])};
  static const Color darkAccentText = {hex_to_flutter_color(dark["bg"])};

  // Status (Universal)
  static const Color statusOk = {hex_to_flutter_color(light["statusOk"])};
  static const Color statusWarn = {hex_to_flutter_color(light["statusWarn"])};
  static const Color statusDanger = {hex_to_flutter_color(light["statusDanger"])};
  static const Color transparent = Color(0x00000000);
}}

class AppSpacing {{
  static const double space1 = {float(spacing["1"].replace("px", ""))}; // 4px
  static const double space2 = {float(spacing["2"].replace("px", ""))}; // 8px
  static const double space3 = {float(spacing["3"].replace("px", ""))}; // 12px
  static const double space4 = {float(spacing["4"].replace("px", ""))}; // 16px
  static const double space6 = {float(spacing["6"].replace("px", ""))}; // 24px
  static const double space8 = {float(spacing["8"].replace("px", ""))}; // 32px
}}

class AppRadius {{
  static const double sm = {float(radius["sm"].replace("px", ""))}; // 6px
  static const double md = {float(radius["md"].replace("px", ""))}; // 10px
  static const Radius radiusSm = Radius.circular(sm);
  static const Radius radiusMd = Radius.circular(md);
  static const BorderRadius borderSm = BorderRadius.all(radiusSm);
  static const BorderRadius borderMd = BorderRadius.all(radiusMd);
}}

class AppDimensions {{
  static const double controlHeight = 40.0;
  static const double borderWidth = 1.0;
  static const double iconSizeSm = 20.0;
  static const double iconSizeMd = 24.0;
}}

class AppTypography {{
  static const String fontBody = 'Public Sans';
  static const String fontMono = 'IBM Plex Mono';

  static const double textXs = 13.0;
  static const double textSm = 15.0;
  static const double textMd = 18.0;
  static const double textLg = 24.0;
  static const double textXl = 32.0;

  static TextStyle body(Color color, {{FontWeight weight = FontWeight.w400, double size = textSm}}) {{
    return TextStyle(
      fontFamily: fontBody,
      fontSize: size,
      fontWeight: weight,
      color: color,
      height: 1.5,
    );
  }}

  static TextStyle mono(Color color, {{FontWeight weight = FontWeight.w400, double size = textSm}}) {{
    return TextStyle(
      fontFamily: fontMono,
      fontSize: size,
      fontWeight: weight,
      color: color,
      height: 1.4,
    );
  }}
}}

class AppTheme {{
  static ThemeData light() {{
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
  }}

  static ThemeData dark() {{
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
  }}
}}
"""
    FLUTTER_THEME_OUT.parent.mkdir(parents=True, exist_ok=True)
    FLUTTER_THEME_OUT.write_text(content, encoding="utf-8")
    print(f"[OK] Berhasil menghasilkan {FLUTTER_THEME_OUT}")


if __name__ == "__main__":
    generate_flutter_theme()
