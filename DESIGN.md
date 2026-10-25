# Heatwater UI design system

Reference: [VoltAgent/awesome-design-md — IBM DESIGN.md](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/ibm/DESIGN.md)
Reference Git blob: dbef1c5b20357a8953e6832e5d383a866a66f11a
Full source and license are retained in docs/design-sources/.

## Visual direction

An analytical workspace inspired by the reference's Carbon rules. It uses white
and neutral gray surfaces, charcoal typography, a single blue action accent,
square geometry, fine dividers and a four-pixel spacing scale. This project
retains its own identity; no IBM marks, logos or product endorsement are used.

## Tokens

- Action: #0f62fe; hover #0050e6; pressed #002d9c.
- Ink: #161616; secondary #525252; caption #6f6f6f.
- Canvas: #ffffff; supporting surface #f4f4f4; divider #e0e0e0.
- All cards and controls: radius 0; no soft shadows.
- Typography: IBM Plex Sans if locally available, then system/CJK sans fallback.
  No font CDN is used so the single-file edition remains offline.
- Display 48–60 px, weight 300; section headings 28–32 px, weight 400.
- Body 14–16 px, line-height 1.5–1.7; captions 12 px.
- Body letter spacing: 0.16 px.
- Four-pixel scale: 4, 8, 12, 16, 24, 32, 48, 64, 96.
- Max grid: 1584 px; 4 metric columns, 2 on tablet/mobile.
- Touch buttons and navigation: minimum 48 px target on mobile.
- Focus: visible blue outline. Honor prefers-reduced-motion.

## Data semantics

The four existing raster colors and continuous score palettes encode data, not
additional brand accents. Preserve their mapping in map, legend and statistics.
Keep blue for navigation, selection, links and actions. Do not recolor scientific
classes simply to match interface styling.

## Composition

1. Gray utility bar and white navigation.
2. Light display heading beside a flat study-frame metadata tile.
3. Dataset strip with clear real/synthetic labels.
4. Four metrics separated by hairlines.
5. Large map canvas with a square layer rail and fully visible legend.
6. Parameter controls, table-like zone summaries and a neutral interpretation panel.
7. Method steps, disclosure and study limits.
8. Inverted charcoal footer.

## Responsive behavior

Below 1056 px: compact map rail and two-column parameter layout.
Below 672 px: toggleable navigation, two-column metrics, three-column layer
buttons, single-column analysis cards. No horizontal page scrolling.
Do not hide map export on mobile.

## Verification

Retain calculation and data-parity tests. Check desktop and 390 px mobile views,
menu keyboard/focus behavior, all layer states, exports and standalone offline
HTML. Typography and component geometry must follow this document; numerical
values and scientific interpretation must remain unchanged.
