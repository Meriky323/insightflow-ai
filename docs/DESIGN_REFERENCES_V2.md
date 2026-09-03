# InsightFlow 2.0 — Design References & Logic

## Selected direction: Evidence Editorial

The final visual language combines a warm research-document canvas with a modern intelligence workspace. The product's own motif is the **Evidence Thread**: sources visually converge into an insight, and any major insight can open a drawer containing the source evidence behind it.

## References used as principles, not templates

- **Linear** — quiet navigation, high information density without visual noise, contextual actions.
- **Raycast** — a single obvious primary action, keyboard-first command interaction, fast micro-motion.
- **Vercel Geist** — typography hierarchy, grid discipline, spacing and accessible contrast.
- **ReactBits** — magnetic hover, spotlight/glare ideas, reveal timing; rebuilt dependency-free in native JS/CSS.
- **MotionSites / MotionSite** — cinematic section composition and scroll rhythm; intentionally restrained for a research product.
- **Brandwatch / Sprinklr** — consumer-intelligence workflow expectations: trend detection, evidence, benchmarking, source coverage, actionability.

## Why the site is not a generic AI SaaS dashboard

- Cards are used only when they express an object or state; they are not the whole layout system.
- The serif italic is used only for editorial emphasis, not as a decorative font everywhere.
- Signal blue has one job: evidence/insight state. Coral is reserved for guardrails/risk.
- Motion is limited to reveal, evidence-flow, magnetic CTA, spotlight hover, subtle tilt, drawer transition and command interaction.
- No purple-gradient AI hero, particles, glass-everywhere, 3D globe, or decorative “AI sparkle” language.

## Motion system

- Scroll reveal: 0.75s, easing `cubic-bezier(.22,.8,.24,1)`
- Magnetic CTA: pointer-fine only, small translation
- Spotlight cards: local radial response to cursor position
- Evidence flow: animated SVG stroke + moving evidence nodes
- Case tilt: under 2 degrees, pointer-fine only
- Evidence drawer: 0.38s side sheet / mobile bottom sheet
- Reduced-motion media query disables non-essential animation
