---
name: BitGuard Sentinel
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#3d4947'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#6d7a77'
  outline-variant: '#bcc9c6'
  surface-tint: '#006a61'
  primary: '#00685f'
  on-primary: '#ffffff'
  primary-container: '#008378'
  on-primary-container: '#f4fffc'
  inverse-primary: '#6bd8cb'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#00628d'
  on-tertiary: '#ffffff'
  tertiary-container: '#007cb1'
  on-tertiary-container: '#fcfcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#c9e6ff'
  tertiary-fixed-dim: '#89ceff'
  on-tertiary-fixed: '#001e2f'
  on-tertiary-fixed-variant: '#004c6e'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 20px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 24px
---

## Brand & Style
The design system is engineered for high-stakes financial operations and security monitoring. The brand personality is clinical, precise, and authoritative, prioritizing cognitive efficiency over decorative flair. The target audience includes security analysts, institutional traders, and infrastructure engineers who require a "heads-up display" environment for rapid decision-making.

The aesthetic follows a **Corporate / Modern** approach with a heavy emphasis on **Minimalism** and data density. It avoids all non-functional elements like gradients, blurs, or shadows. Depth is communicated through structural layering and subtle border shifts rather than elevation. The interface should feel like a high-performance instrument—cold, reliable, and transparent.

## Colors
The palette is intentionally restrained to keep the focus on actionable data. 
- **Backgrounds:** A muted `#F8FAFC` serves as the canvas, with pure `#FFFFFF` used for active panels to create a subtle but clear hierarchy.
- **Accents:** The teal (`#0D9488`) is reserved exclusively for primary calls to action and active navigational states.
- **Semantic Colors:** Green, Red, and Amber are used strictly for status indicators and severity badges. These are high-saturation but used in small footprints to prevent visual fatigue.
- **Borders:** `#E2E8F0` is the primary structural tool, defining the limits of every container and data cell.

## Typography
This design system utilizes **Inter** for its exceptional legibility at small sizes and its neutral, systematic tone. For cryptographic hashes, transaction IDs, and specific numerical data, a monospaced font (JetBrains Mono) is introduced to ensure character alignment and prevent reading errors.

Typography is treated as a functional hierarchy:
- Use **headline-sm** for most card and section titles to maintain density.
- Use **label-md** with uppercase styling for table headers and metadata categories.
- Use **body-sm** as the standard size for data entry and table rows.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a strictly enforced 4px baseline rhythm. Given the operational nature of the product, "white space" is treated as a luxury; padding is compact to allow as much data as possible to be visible above the fold.

- **Desktop:** 12-column grid, 16px gutters. Sidebars are fixed-width (240px) to maximize the fluid central data area.
- **Tablet:** 8-column grid.
- **Mobile:** 4-column grid.
- **Density:** Elements like table rows and list items should use `sm` (8px) vertical padding to facilitate rapid scanning of large datasets.

## Elevation & Depth
This design system rejects shadows in favor of **Tonal Layers** and **Low-contrast outlines**. 

- **Level 0 (Background):** `#F8FAFC` - The main application canvas.
- **Level 1 (Surface):** `#FFFFFF` with a 1px solid `#E2E8F0` border. Used for cards, tables, and sidebar containers.
- **Level 2 (Interaction):** When an element is hovered, the border color shifts to `#CBD5E1`. 
- **Level 3 (Overlay):** Modals use a 1px border of `#94A3B8` and a subtle 4px blur backdrop to focus the user, but still refrain from heavy drop shadows.

## Shapes
A consistent **8px (0.5rem)** corner radius is applied to all primary containers, buttons, and input fields. This "Rounded" setting balances the clinical nature of the interface with enough softness to feel modern and professional.

Smaller elements like badges and checkboxes may use 4px (Soft) to maintain visual balance when their overall scale is reduced.

## Components
- **Buttons:** Primary buttons are solid Teal (`#0D9488`) with white text. Secondary buttons use a white background with the standard `#E2E8F0` border and Slate text.
- **Tables:** The core of the system. Rows have a 1px bottom border. Header background is `#F1F5F9`. Text is `body-sm`. Hover states on rows use `#F8FAFC`.
- **Severity Badges:**
    - **Info:** Blue (`#0EA5E9`) background at 10% opacity, solid blue text.
    - **Medium:** Amber (`#F59E0B`) background at 10% opacity, solid amber text.
    - **High:** Red (`#EF4444`) background at 10% opacity, solid red text.
- **Input Fields:** 1px solid `#E2E8F0` borders, `body-sm` text. Focus state uses a 1px Teal border and a 2px Teal outer ring at 20% opacity.
- **Status Indicators:** Small 8px circles. Positive is Green (`#10B981`), Negative is Red (`#EF4444`), Neutral/Offline is Slate (`#94A3B8`).
- **Data Cards:** No padding on the card itself if it contains a table; allow the table to bleed to the edges to maximize horizontal space.