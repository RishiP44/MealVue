---
name: Shelfie Editorial
colors:
  surface: '#fff8f3'
  surface-dim: '#e1d9d0'
  surface-bright: '#fff8f3'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fbf2e9'
  surface-container: '#f5ece3'
  surface-container-high: '#f0e7de'
  surface-container-highest: '#eae1d8'
  on-surface: '#1f1b16'
  on-surface-variant: '#54433a'
  inverse-surface: '#34302a'
  inverse-on-surface: '#f8efe6'
  outline: '#877369'
  outline-variant: '#dac2b6'
  surface-tint: '#934b19'
  primary: '#6c2f00'
  on-primary: '#ffffff'
  primary-container: '#8b4513'
  on-primary-container: '#ffc29f'
  inverse-primary: '#ffb68c'
  secondary: '#635d5a'
  on-secondary: '#ffffff'
  secondary-container: '#e6ded9'
  on-secondary-container: '#67625e'
  tertiary: '#5b3912'
  on-tertiary: '#ffffff'
  tertiary-container: '#765027'
  on-tertiary-container: '#f9c592'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdbc9'
  primary-fixed-dim: '#ffb68c'
  on-primary-fixed: '#321200'
  on-primary-fixed-variant: '#753401'
  secondary-fixed: '#e9e1dc'
  secondary-fixed-dim: '#cdc5c0'
  on-secondary-fixed: '#1e1b18'
  on-secondary-fixed-variant: '#4b4642'
  tertiary-fixed: '#ffdcbd'
  tertiary-fixed-dim: '#f0bd8b'
  on-tertiary-fixed: '#2c1600'
  on-tertiary-fixed-variant: '#623f18'
  background: '#fff8f3'
  on-background: '#1f1b16'
  surface-variant: '#eae1d8'
typography:
  display-lg:
    fontFamily: Playfair Display
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Playfair Display
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Playfair Display
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-max-width: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

This design system is built upon a **Restrained Editorial** aesthetic, specifically tailored for the tactile and intellectual experience of a personal library. It balances the timelessness of a printed literary journal with the precision of a modern archival tool. 

The visual narrative prioritizes content—the books—by using "paper" tones and generous whitespace to reduce cognitive load. The emotional response is one of calm, focus, and stewardship. The style avoids trendy digital effects, opting instead for a **Minimalist-Tactile** approach where depth is conveyed through subtle color shifts and fine lines rather than heavy shadows.

## Colors

The palette is rooted in organic, earthy tones reminiscent of high-quality paper stock, ink, and leather binding.

- **Primary & Active:** Deep terracotta and dark warm brown serve as the "leather" accents, used for primary actions and key navigation states.
- **Surface & Background:** A dual-tone approach where the main background is a warm ivory (#FDFCF8) to reduce screen glare, while interactive surfaces use pure white (#FFFFFF) to create a subtle lift.
- **Functional Tones:** Success, uncertainty, and error states are muted and desaturated to remain harmonious with the warm editorial theme, avoiding the harshness of standard digital utility colors.

## Typography

The typographic hierarchy utilizes a high-contrast pairing between a sophisticated serif and a technical sans-serif.

- **Headlines:** Playfair Display provides an authoritative, literary feel. Use it for page titles, book titles, and major section headings. Ensure "Display" styles use tighter letter spacing.
- **Body & UI:** Geist is used for its exceptional legibility and neutral, modern character. It handles metadata, descriptions, and functional UI elements with clarity.
- **Labels:** Use uppercase Geist with slight tracking for category labels, metadata headers, and small button text to create a disciplined, archival look.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy on desktop to mimic the structured columns of a book or magazine, while transitioning to a fluid, high-margin layout on mobile devices.

- **Rhythm:** A base 4px unit governs all spacing. Vertical rhythm should be strictly maintained, with larger gaps (40px+) between major content sections to emphasize the "quiet" nature of the app.
- **Grid:** On desktop, use a 12-column grid with a 24px gutter. Content should be centered with a maximum width of 1280px to prevent line lengths from becoming unreadable.
- **Mobile:** Transition to a 4-column grid with 16px side margins. Increase the vertical padding on list items to ensure a comfortable touch target and a premium, uncrowded feel.

## Elevation & Depth

This design system avoids traditional box shadows in favor of **Tonal Layers** and **Fine Outlines**.

- **Layering:** Hierarchy is established by placing white (#FFFFFF) elements on the warm ivory (#FDFCF8) background. This creates a natural "paper on desk" elevation.
- **Outlines:** Use 1px solid borders in Soft Warm Gray (#E5E1DA) to define boundaries. 
- **Active State Elevation:** When an element is pressed or active, do not increase shadow. Instead, shift the border color to the Primary Accent or apply a subtle inner-tint of the accent color to indicate "pressed" depth.

## Shapes

The shape language is structured yet approachable. 

- **Cards & Containers:** Use a consistent 0.5rem (8px) radius. This provides enough softness to feel "warm" without losing the professional, geometric integrity of the editorial style.
- **Buttons:** Follow the same 8px radius for a cohesive look.
- **Imagery:** Book covers should retain their natural aspect ratios and sharp corners to maintain the realism of physical objects, while their containers may have the 8px corner treatment.

## Components

- **Buttons:** Primary buttons are solid Deep Terracotta with White text. Secondary buttons use a 1px Soft Warm Gray outline with Ink Charcoal text. Tertiary buttons are text-only with a slight underline on hover.
- **Cards:** White surface, 1px Soft Warm Gray border, 8px radius. Padding should be generous (20px or 24px) to give book metadata room to breathe.
- **Input Fields:** Use a subtle background of the warm ivory, a bottom-only 1px border for a "notepaper" feel, or a full 1px border for high-density forms.
- **Icons:** Use a 1.5px stroke weight. Icons should be functional and literal—avoid overly abstract or rounded "bubbly" icon sets.
- **Chips/Tags:** Use a pill shape (rounded-xl) but with the secondary text color and a very light tint of the primary accent for background.
- **Progress Indicators:** For reading progress, use a thin 4px bar in Deep Terracotta against a Soft Warm Gray track.