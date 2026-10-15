---
name: Quiet Domesticity
colors:
  surface: '#f6fbf5'
  surface-dim: '#d7dbd6'
  surface-bright: '#f6fbf5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f5f0'
  surface-container: '#ebefea'
  surface-container-high: '#e5e9e4'
  surface-container-highest: '#dfe4df'
  on-surface: '#181d1a'
  on-surface-variant: '#404945'
  inverse-surface: '#2c322e'
  inverse-on-surface: '#edf2ed'
  outline: '#707975'
  outline-variant: '#bfc9c4'
  surface-tint: '#2c6859'
  primary: '#115344'
  on-primary: '#ffffff'
  primary-container: '#2f6b5b'
  on-primary-container: '#abe9d5'
  inverse-primary: '#96d3bf'
  secondary: '#4d635b'
  on-secondary: '#ffffff'
  secondary-container: '#cfe8de'
  on-secondary-container: '#536961'
  tertiary: '#703a32'
  on-tertiary: '#ffffff'
  tertiary-container: '#8c5148'
  on-tertiary-container: '#ffd3cc'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#b1efdb'
  primary-fixed-dim: '#96d3bf'
  on-primary-fixed: '#002019'
  on-primary-fixed-variant: '#0d5041'
  secondary-fixed: '#cfe8de'
  secondary-fixed-dim: '#b4ccc2'
  on-secondary-fixed: '#091f19'
  on-secondary-fixed-variant: '#354b44'
  tertiary-fixed: '#ffdad4'
  tertiary-fixed-dim: '#ffb4a8'
  on-tertiary-fixed: '#370e08'
  on-tertiary-fixed-variant: '#6d3830'
  background: '#f6fbf5'
  on-background: '#181d1a'
  surface-variant: '#dfe4df'
typography:
  headline-lg:
    fontFamily: Public Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Public Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Public Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Public Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Public Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 26px
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
    fontWeight: '500'
    lineHeight: 16px
  mono-metric:
    fontFamily: IBM Plex Mono
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 28px
  mono-body:
    fontFamily: IBM Plex Mono
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 20px
  mono-sm:
    fontFamily: IBM Plex Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 16px
  gutter-desktop: 24px
  margin: 16px
  margin-desktop: 32px
  space-xs: 4px
  space-sm: 8px
  space-md: 16px
  space-lg: 24px
  space-xl: 32px
---

## Brand & Style

This design system delivers a calm, domestic, and strictly private smart home control experience for households. The interface prioritizes emotional durability over tech novelty: it rejects glowing accents, animated micro-interactions, decorative illustrations, gradients, shadows, and synthetic embellishments. Instead, it mirrors well-crafted architectural signage and tactile physical switchboards—approachable, grounded, and quiet.

The target audience is multi-generational families sharing residential space. The interface behaves as a dependable appliance rather than an attention-seeking software platform. It prioritizes legibility, instant comprehension of domestic state, and discreet feedback. Information architecture is utilitarian, displaying state without editorializing or demanding action unless human intervention is required.

## Colors

The palette operates under absolute restraint. A single deep botanical green serves as the functional accent; there are no secondary or tertiary brand accents. Visual contrast is built strictly through surface values, borders, and typographic weights.

### Light Theme (Default)
- **Canvas / Page Background:** `#F4F1EA` (warm unbleached paper)
- **Card / Surface Background:** `#FBF9F4`
- **Subtle Surface (nested controls, toggle track inactive):** `#ECE7DC`
- **Primary Border:** `#D9D3C6` (1px solid on all structural containers)
- **Secondary Border / Dividers:** `#E5E0D5`
- **Primary Text:** `#1F2421` (deep spruce-charcoal)
- **Secondary / Supporting Text:** `#5E655F` (subdued slate-olive)
- **Primary Accent:** `#2F6B5B` (deep mineral green)
- **Primary Accent Hover:** `#255849`
- **Primary Accent Active / Selected Background:** `#E4EDE9` (tinted container fill)

### Dark Theme Alternative
- **Canvas / Page Background:** `#151816`
- **Card / Surface Background:** `#1D211E`
- **Subtle Surface:** `#232824`
- **Primary Border:** `#2D332F`
- **Secondary Border / Dividers:** `#242A26`
- **Primary Text:** `#E8E6DF`
- **Secondary / Supporting Text:** `#8A938C`
- **Primary Accent:** `#5FA08E`
- **Primary Accent Hover:** `#71B4A1`
- **Primary Accent Active / Selected Background:** `#1F2C27`

### Semantic Status Colors (Flat & Unadorned)
- **Status OK:** `#4C7A3F` (muted moss)
- **Status Warning:** `#B7791F` (matte amber)
- **Status Danger:** `#B23A2E` (brick red)

Status colors must never be rendered as glowing pills, tinted blurs, or gradients. Display status through text labels, 8px solid geometric indicator dots, or standard 1px container borders.

## Typography

Typography relies on two typefaces: **Public Sans** for human interaction, layout titles, and structural labels; and **IBM Plex Mono** strictly for telemetric data, hardware sensor readouts, network identifiers, and timestamps.

### Typographic Hierarchy Rules
- Headlines and section anchors use `Public Sans` with a semi-bold weight (`600`).
- Text content is never justified and never uppercase-tracked, except for short technical abbreviations (e.g., `kWh`, `PPM`, `IP`).
- Monospace figures must always be used for changing numeric values to eliminate horizontal jitter during live telemetry updates.
- Microcopy in Indonesian must be flat, factual, concise, and non-conversational (e.g., use "Ruang Tamu: 24.5°C — Stabil" instead of "Ruang tamu Anda terasa nyaman!").

## Elevation & Depth

This system is strictly flat. It prohibits:
- Drop shadows, box shadows, and ambient elevation blurs (`box-shadow: none !important`).
- Linear, radial, or conic gradients.
- Backdrop blurs and frosted glass transparency (`backdrop-filter: none !important`).
- Decorative glows, skeuomorphic bevels, or inner shadows.

### Spatial Distinction
Depth and containment are achieved exclusively through:
1. **Low-contrast 1px outlines:** Cards, popovers, and containers use a crisp `1px solid #D9D3C6` (Light) or `1px solid #2D332F` (Dark).
2. **Surface alternation:** Interactive target regions sit on `#FBF9F4`, surrounded by `#F4F1EA` canvas space. Active states leverage solid tinted fills (`#E4EDE9` in light mode) rather than elevated shadow offsets.
3. **Layered nesting:** Inset device controllers (such as slider wells or grouped relay blocks) use `#ECE7DC` backgrounds with no border, seated cleanly inside `#FBF9F4` cards.

## Shapes

Shapes are geometric and disciplined:
- **Buttons, input fields, dropdown triggers, and badges:** Exactly `6px` corner radius (`border-radius: 6px`).
- **Cards, structural panels, and modal containers:** Exactly `10px` corner radius (`border-radius: 10px`).
- **Status indicator dots and toggle handles:** Circular (`border-radius: 50%` or full pill for switch bodies).
- **No pill-shaped action buttons or asymmetric rounded corners.**

## Components

All interactive components must preserve standard tactile ergonomics with zero decorative overhead.

### Buttons & Input Fields
- **Fixed Height:** Both buttons and text inputs are strictly 40px tall (`height: 40px; box-sizing: border-box;`).
- **Primary Button:** `#2F6B5B` solid background, `#FBF9F4` text, no border, 6px radius. Hover: `#255849`. Active: `#1F4A3D`.
- **Secondary / Outline Button:** Transparent background, `1px solid #D9D3C6`, `#1F2421` text, 6px radius. Hover: `#ECE7DC` background.
- **Input Field:** `#FBF9F4` background, `1px solid #D9D3C6`, 6px radius, `13px` internal horizontal padding. Focused: `1px solid #2F6B5B` outline, no glow rings.
- **Disabled State:** 40% overall opacity; maintain 1px border.

### Toggle Switches (Smart Relays)
- **Dimensions:** 44px wide, 24px high.
- **Track (Off):** `#ECE7DC` fill, `1px solid #D9D3C6`.
- **Track (On):** `#2F6B5B` fill, `1px solid #2F6B5B`.
- **Knob:** 18px diameter solid circle, `#FBF9F4` fill, mechanically offset by 2px margin. Zero drop shadow. Transitions must be instant or under 150ms linear motion.

### Cards & Room Tiles
- **Structure:** `#FBF9F4` fill, `1px solid #D9D3C6` border, 10px radius, 16px internal padding.
- **Header Structure:** Title in `Public Sans` 18px / 600 weight, trailing sensor metric in `IBM Plex Mono` 13px / 400 weight (`#5E655F`).
- **Dividers:** 1px solid `#E5E0D5` spanning edge-to-edge inside cards.

### Chips & Sensor Badges
- **Dimensions:** 24px fixed height, 6px radius, 8px horizontal padding.
- **Typography:** `IBM Plex Mono` 13px.
- **Coloration:** `#ECE7DC` fill, `1px solid #D9D3C6`, `#1F2421` text. No colored chips for purely decorative categorization.

### Status Indicators
- **Format:** 8px diameter solid circle positioned beside textual descriptions.
- **States:** OK (`#4C7A3F`), Warning (`#B7791F`), Danger (`#B23A2E`). No flashing, no halo rings.

### Checkboxes & Radios
- **Checkboxes:** 18px × 18px square, 4px corner radius, `1px solid #D9D3C6`. Checked state: `#2F6B5B` background with a crisp white checkmark.
- **Radios:** 18px diameter circle, `1px solid #D9D3C6`. Selected state: `#2F6B5B` outer border, 8px solid center dot.

### Iconography
- Icons must follow a clean outline aesthetic (Phosphor-style, 1.5px stroke width, square terminals).
- Banned icons: Sparkles, magical wands, ai-stars, decorative speech bubbles, and filled novelty badges.