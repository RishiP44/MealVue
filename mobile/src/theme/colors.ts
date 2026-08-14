/**
 * Shelfie Design Tokens — Reconciled from Approved Stitch Archival Linen Design
 */
export const colors = {
  // Backgrounds & Canvas
  background: '#f4ecd8',        // Warm archival parchment
  surface: '#fbf6ec',           // Light archival paper surface
  surfaceWhite: '#ffffff',      // Pure white container
  surfaceContainer: '#f5ece3',   // Warm soft container
  surfaceContainerHigh: '#f0e7de',
  surfaceContainerHighest: '#eae1d8',

  // Outlines & Borders
  border: '#dac2b6',            // Warm outline
  borderLight: '#e8decb',       // Subtle passe-partout border
  borderDark: '#2a1c15',        // Dark leather border

  // Ink Typography
  textPrimary: '#3c2a21',       // Dark chocolate ink
  textSecondary: '#5a4538',     // Muted warm chocolate
  textMuted: '#877369',         // Outline warm gray
  textGold: '#e5b66d',          // Debossed gold text on leather
  textInverse: '#ffffff',

  // Leather Brand Elements
  leather: '#3c2a21',           // Dark leather brown
  leatherDark: '#2a1c15',       // Deep leather shadow
  leatherGold: '#e5b66d',       // Embossed gold accent
  primary: '#3c2a21',           // Dark chocolate primary

  // Status & Confidence States
  matched: {
    text: '#15803d',            // Deep green
    bg: '#dcfce7',              // Soft green
    border: '#86efac',
    solid: '#15803d',
  },
  needsReview: {
    text: '#b45309',            // Warm amber
    bg: '#fef3c7',              // Soft amber
    border: '#fde68a',
    solid: '#b45309',
  },
  unmatched: {
    text: '#5a4538',            // Dark muted chocolate
    bg: '#f5ece3',              // Soft parchment container
    border: '#dac2b6',
  },
  unreadable: {
    text: '#877369',            // Outline gray
    bg: '#eae1d8',              // Muted paper
    border: '#dac2b6',
  },
  failed: {
    text: '#ba1a1a',            // Restrained red
    bg: '#ffdad6',              // Soft red
    border: '#fca5a5',
  },
};
