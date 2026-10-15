---
name: Quiet Domesticity
colors:
  surface: '#fcf9f2'
  surface-dim: '#dcdad3'
  surface-bright: '#fcf9f2'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3ec'
  surface-container: '#f1eee7'
  surface-container-high: '#ebe8e1'
  surface-container-highest: '#e5e2db'
  on-surface: '#1c1c18'
  on-surface-variant: '#404945'
  inverse-surface: '#31312c'
  inverse-on-surface: '#f3f0e9'
  outline: '#707975'
  outline-variant: '#bfc9c4'
  surface-tint: '#2c6859'
  primary: '#115344'
  on-primary: '#ffffff'
  primary-container: '#2f6b5b'
  on-primary-container: '#abe9d5'
  inverse-primary: '#96d3bf'
  secondary: '#59605a'
  on-secondary: '#ffffff'
  secondary-container: '#dbe1da'
  on-secondary-container: '#5d645e'
  tertiary: '#26521c'
  on-tertiary: '#ffffff'
  tertiary-container: '#3e6b32'
  on-tertiary-container: '#b6eaa3'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b1efdb'
  primary-fixed-dim: '#96d3bf'
  on-primary-fixed: '#002019'
  on-primary-fixed-variant: '#0d5041'
  secondary-fixed: '#dde4dd'
  secondary-fixed-dim: '#c1c8c1'
  on-secondary-fixed: '#171d19'
  on-secondary-fixed-variant: '#424843'
  tertiary-fixed: '#bcf1a9'
  tertiary-fixed-dim: '#a1d48f'
  on-tertiary-fixed: '#012200'
  on-tertiary-fixed-variant: '#24501a'
  background: '#fcf9f2'
  on-background: '#1c1c18'
  surface-variant: '#e5e2db'
typography:
  headline-lg:
    fontFamily: Public Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Public Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Public Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-md:
    fontFamily: Public Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Public Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Public Sans
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.01em
  mono-data-lg:
    fontFamily: Courier Prime
    fontSize: 24px
    fontWeight: '400'
    lineHeight: 28px
  mono-data-md:
    fontFamily: Courier Prime
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 20px
  mono-data-sm:
    fontFamily: Courier Prime
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-compact: 0.5rem
  margin: 1rem
  space-xxs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.25rem
  space-xl: 1.5rem
---

## Brand & Style

The design system embodies "Quiet Domesticity"—an understated, calm sanctuary tailored for domestic environments. Rather than presenting home automation as an aggressive, high-tech command center, this system prioritizes unobtrusive utility, visual stillness, and tactile clarity. The target audience seeks seamless control over their private physical space without visual noise, alert fatigue, or decorative gimmicks.

The design movement is strictly flat, functional minimalism:
- **No shadows, glows, or bevels:** Surface elevations exist exclusively through tonal color shifts.
- **No gradients or glassmorphism:** Surfaces are solid, opaque, and grounded.
- **No decorative illustrations, AI sparkles, or emoji:** Iconography is purposeful and linear; information density remains controlled and breathable.
- **Tone:** Grounded, peaceful, precise, and private. Microcopy uses calm, concise Indonesian domestic phrasing.

## Colors

Hierarchy and state differentiation are communicated entirely through solid, calibrated color planes. Surfaces do not cast drop shadows; containers sit directly upon the canvas, visually demarcated by brightness and hue contrast.

### Light Mode (Default)
- **Canvas / Page Background:** `#F4F1EA` (Warm bone linen)
- **Surface / Card Background:** `#FBF9F4` (Alabaster cream)
- **Inset / Input / Inactive Pill Background:** `#ECE7DC` (Soft stone)
- **Divider & Structural Line:** `#E5E0D5` (Warm gray line)
- **Primary Text & High-Emphasis Glyphs:** `#1F2421` (Deep evergreen-slate)
- **Secondary Text & Metadata:** `#5E655F` (Muted spruce)
- **Accent / Interactive:** `#2F6B5B` (Deep pine sage; Pressed state: `#255849`)
- **Active State / ON Surface Tint:** `#E4EDE9` (Pale eucalyptus)

### Dark Mode Reference
- **Canvas / Page Background:** `#151816`
- **Surface / Card Background:** `#1D211E`
- **Inset / Input Background:** `#232824`
- **Divider & Structural Line:** `#2D332F`
- **Primary Text:** `#E8E6DF`
- **Secondary Text:** `#8A938C`
- **Accent / Interactive:** `#5FA08E`
- **Active State / ON Surface Tint:** `#1F2C27`

### Semantic Feedback
- **Status OK:** `#4C7A3F` (Natural olive moss)
- **Status Warning:** `#B7791F` (Muted amber ochre)
- **Status Danger:** `#B23A2E` (Earthy clay crimson)

## Typography

The typographic hierarchy uses **Public Sans** for all human interface communications, headers, and descriptions, pairing structured legibility with neutral domestic warmth. 

A monospaced system font (implemented as `IBM Plex Mono` in Flutter native assets, mapped to monospace tokens) is strictly isolated to technical data points:
- Sensor metrics (temperatures, wattages, air quality indices, humidity percentages).
- Timestamps and scheduling markers.
- Device hardware IDs and pairing PIN codes.

Headings maintain an authoritative, calm weight (600), while explanatory content remains soft and readable at weight 400.

## Layout & Spacing

Designed against Android’s core baseline frame of **360dp × 800dp**:
- **Grid Structure:** 2-column or 4-column fluid mobile grid. Device tiles systematically span 2 columns within a 4-column layout (effectively a side-by-side 2-column device matrix).
- **Outer Canvas Margins:** Strict `16px` (`margin: 1rem`) screen edge margins.
- **Gutters:** `12px` (`gutter: 0.75rem`) between adjacent grid tiles.
- **Touch Ergonomics:** Interactive elements have a minimum physical bounding box of `48px`, even when the visual container height is `44px` or `32px`.

## Elevation & Depth

This system operates under an absolute **zero-shadow, flat plane** paradigm. Elevation is communicated strictly through surface layering:

1. **Floor 0 (Canvas):** Page background (`#F4F1EA`). Represents the fundamental ground of the application.
2. **Floor 1 (Containers & Cards):** Default card background (`#FBF9F4`). Flat, unbordered surfaces resting directly on Floor 0.
3. **Floor 2 (Recessed & Segmented Targets):** Inset controls, inputs, and unselected filter track elements (`#ECE7DC`). Communicates actionable recesses.
4. **Floor 3 (Active / Engaged States):** State-activated tiles and selection pills (`#E4EDE9`). Emphasizes live smart home nodes.
5. **Separators:** Shadows are prohibited for edge definition. Boundaries between lists and navigation segments use a hairline `1px` solid divider (`#E5E0D5`). Cards never use borders.

## Shapes

Corner radii are structured systematically to create a friendly, tactile quality without appearing cartoonish:

- **Device Tiles:** Radius `24px`. Emphasizes the main interactive hardware components of the household.
- **Content Cards:** Radius `20px`. Used for aggregate groups, climate hubs, and routine summaries.
- **Action Buttons & Form Inputs:** Radius `12px`.
- **Chips, Badges & Filter Tags:** Radius `8px`.
- **Navigation Indicators & Switches:** Full pill geometries (`border-radius: 9999px`).
- **Dividers:** Clean, square-cut 1px hairline rules without border-radii.

## Components

### Top App Bar
- **Structure:** Flat layout matching the page background (`#F4F1EA`). No drop shadows or bottom dividers.
- **Content:** Left-aligned 24px/600 primary title (`#1F2421`). Contextual actions (e.g., "Tambah", "Profil") aligned right with 48px touch bounding areas.

### Bottom Navigation Bar
- **Structure:** Height 64px, surface color `#F4F1EA` anchored by a single 1px top hairline divider (`#E5E0D5`).
- **Items (5):** *Beranda*, *Perangkat*, *Asisten*, *Kamera*, *Lainnya*.
- **Active State:** Icon sits inside an active pill (`64px × 32px`) filled with `#E4EDE9`. Icon and label use `#2F6B5B`.
- **Inactive State:** Unfilled pill, text, and icons use `#5E655F`.

### Device Tiles
- **Geometry:** 2-column grid cards with `24px` radius. Height is typically 120–140px.
- **Default (OFF):** Background `#FBF9F4`. Primary text `#1F2421`, subtext `#5E655F`.
- **Active (ON):** Background `#E4EDE9`. Icon and active markers `#2F6B5B`. Primary text `#1F2421`.
- **Telemetry Display:** Temperature, wattage, or timing values rendered in monospace typography (`mono-data-sm` or `mono-data-md`).

### Buttons
- **Primary Button:** 44px height, `#2F6B5B` solid surface, `12px` radius. Text color `#FBF9F4` (Public Sans, 15px/600). Pressed state: `#255849`. No borders or shadows.
- **Secondary / Inset Button:** 44px height, `#ECE7DC` solid surface, `12px` radius. Text color `#1F2421`. Pressed state: `#E5E0D5`.

### Toggle Switch
- **Dimensions:** Pill track `56px × 32px`.
- **Track (Inactive):** Solid `#ECE7DC`.
- **Track (Active):** Solid `#2F6B5B`.
- **Thumb:** `26px × 26px` circle (`#FBF9F4`), completely flat. Offset 3px from track edge.

### Chips & Tags
- **Dimensions:** Height 32px, `8px` corner radius.
- **Inactive:** Solid `#ECE7DC` fill, `#5E655F` text.
- **Selected:** Solid `#2F6B5B` fill, `#FBF9F4` text, or `#E4EDE9` tint with `#2F6B5B` text depending on prominence.

### Form Inputs
- **Dimensions:** Height 44px (touch target 48px), `12px` corner radius.
- **Surface:** `#ECE7DC` flat fill. No default outline.
- **Active Focus:** 1.5px solid border in `#2F6B5B`. Text `#1F2421`. Placeholder `#5E655F`.

### Lists
- **Structure:** Spans full content card or runs across `#F4F1EA` canvas.
- **Separators:** Rows are separated by a 1px solid line (`#E5E0D5`), inset by 16px on the leading edge. Row height is minimum 56px to ensure accessibility.