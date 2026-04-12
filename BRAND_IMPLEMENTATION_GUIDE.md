# Sidebar Code — Brand Implementation Guide

**For Claude Code / Coding Agent Use**

## Overview

This document contains every asset, token, and specification needed to implement the Sidebar Code brand on the website at sidebarcode.com and across all marketing materials. Read this entire file before touching any brand-related code.

**Logo concept:** The `< | >` bracket mark. The angle brackets reference code syntax. The vertical bar (the "sidebar") is the naming anchor. Together they read as a legal sidebar, a code delimiter, and a UI sidebar panel — all in one glyph.

**Do not modify the color assignments, font families, or logo geometry without explicit instruction.**

---

## 1. Core Brand Colors

| Token | Hex | Usage |
|-------|-----|-------|
| Teal | `#2A9D8F` | AI/tech accent — bracket marks |
| Brass | `#B8902A` | Gold accent — legal tradition |
| Navy | `#0D1A2D` | Primary background, text on light |
| Navy Mid | `#1E3A5F` | Cards, elevated surfaces on dark |
| Parchment | `#F5F3EE` | Warm off-white background |
| Slate | `#64748B` | Body text on light backgrounds |
| Linen | `#E2DDD4` | Borders, rules, dividers |
| White | `#FFFFFF` | Clean background |

## 2. Typography

| Role | Font | Size | Weight | Color | Letter-spacing |
|------|------|------|--------|-------|---------------|
| Logo wordmark | Georgia serif | SVG only | 400 | White or Navy | 0.2em |
| H1 / Hero | Georgia serif | 36-48px | 400 | Navy #0D1A2D | 0.01em |
| H2 / Section | Georgia serif | 24-30px | 400 | Navy #0D1A2D | 0.01em |
| H3 / Card title | System sans-serif | 18-20px | 500 | Navy #0D1A2D | 0 |
| Body copy | System sans-serif | 15-16px | 400 | Slate #64748B | 0.01em |
| Small / caption | System sans-serif | 12-13px | 400 | Slate #64748B | 0.05em |
| ALL-CAPS label | System sans-serif | 10-11px | 500 | Slate #64748B | 0.12em |
| Code accent | Courier New mono | 12-14px | 400 | Brass #B8902A | 0.07em |

**Font families:**
- Display: `Georgia, 'Times New Roman', serif`
- Body: `system-ui, -apple-system, 'Segoe UI', sans-serif`
- Mono: `'Courier New', Courier, monospace`

## 3. SVG Logo Assets

### 3a. Icon Mark — Dark Background
**File:** `icon-dark.svg` — Use for: Favicon, avatars, app icons, dark backgrounds.
```svg
<svg viewBox="0 0 76 58" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Sidebar Code icon mark">
  <text y="48" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#2A9D8F" font-weight="700">&lt;</text>
  <rect x="37" y="11" width="5" height="36" rx="2.5" fill="#B8902A"/>
  <text x="48" y="48" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#2A9D8F" font-weight="700">&gt;</text>
</svg>
```

### 3b. Icon Mark — Light Background
**File:** `icon-light.svg` — Use for: Light backgrounds, parchment, white paper, print.
```svg
<svg viewBox="0 0 76 58" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Sidebar Code icon mark">
  <text y="48" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#0D1A2D" font-weight="700">&lt;</text>
  <rect x="37" y="11" width="5" height="36" rx="2.5" fill="#B8902A"/>
  <text x="48" y="48" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#0D1A2D" font-weight="700">&gt;</text>
</svg>
```

### 3c. Full Lockup — Dark Background (Primary Logo)
**File:** `logo-dark.svg` — Use for: Email headers, slide decks, website nav on dark backgrounds.
```svg
<svg viewBox="0 0 222 58" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Sidebar Code">
  <text y="48" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#2A9D8F" font-weight="700">&lt;</text>
  <rect x="37" y="11" width="5" height="36" rx="2.5" fill="#B8902A"/>
  <text x="48" y="48" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#2A9D8F" font-weight="700">&gt;</text>
  <text x="82" y="32" font-family="Georgia, 'Times New Roman', serif" font-size="14" fill="#FFFFFF" letter-spacing="3" font-weight="400">SIDEBAR</text>
  <text x="83" y="50" font-family="'Courier New', Courier, monospace" font-size="10.5" fill="#B8902A" letter-spacing="4.5">code</text>
</svg>
```

### 3d. Full Lockup — Light Background
**File:** `logo-light.svg` — Use for: Letterhead, proposals, white website backgrounds, print.
```svg
<svg viewBox="0 0 222 58" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Sidebar Code">
  <text y="48" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#2A9D8F" font-weight="700">&lt;</text>
  <rect x="37" y="11" width="5" height="36" rx="2.5" fill="#B8902A"/>
  <text x="48" y="48" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#2A9D8F" font-weight="700">&gt;</text>
  <text x="82" y="32" font-family="Georgia, 'Times New Roman', serif" font-size="14" fill="#0D1A2D" letter-spacing="3" font-weight="400">SIDEBAR</text>
  <text x="83" y="50" font-family="'Courier New', Courier, monospace" font-size="10.5" fill="#B8902A" letter-spacing="4.5">code</text>
</svg>
```

### 3e. Wordmark Only — Dark Background
**File:** `wordmark-dark.svg`
```svg
<svg viewBox="0 0 152 56" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Sidebar Code">
  <text x="0" y="34" font-family="Georgia, 'Times New Roman', serif" font-size="22" fill="#FFFFFF" letter-spacing="5" font-weight="400">SIDEBAR</text>
  <rect x="1" y="40" width="148" height="1.5" fill="#B8902A" opacity="0.5"/>
  <text x="1" y="55" font-family="'Courier New', Courier, monospace" font-size="13" fill="#B8902A" letter-spacing="9">code</text>
</svg>
```

### 3f. Wordmark Only — Light Background
**File:** `wordmark-light.svg`
```svg
<svg viewBox="0 0 152 56" fill="none" xmlns="http://www.w3.org/2000/svg" aria-label="Sidebar Code">
  <text x="0" y="34" font-family="Georgia, 'Times New Roman', serif" font-size="22" fill="#0D1A2D" letter-spacing="5" font-weight="400">SIDEBAR</text>
  <rect x="1" y="40" width="148" height="1.5" fill="#B8902A" opacity="0.5"/>
  <text x="1" y="55" font-family="'Courier New', Courier, monospace" font-size="13" fill="#B8902A" letter-spacing="9">code</text>
</svg>
```

## 4. CSS Design Tokens

Import once at root of application:

```css
:root {
  /* Core Brand Colors */
  --sc-navy:        #0D1A2D;
  --sc-navy-mid:    #1E3A5F;
  --sc-brass:       #B8902A;
  --sc-teal:        #2A9D8F;
  --sc-parchment:   #F5F3EE;
  --sc-slate:       #64748B;
  --sc-linen:       #E2DDD4;
  --sc-white:       #FFFFFF;

  /* Typography */
  --sc-font-display: Georgia, 'Times New Roman', serif;
  --sc-font-body:    system-ui, -apple-system, 'Segoe UI', sans-serif;
  --sc-font-mono:    'Courier New', Courier, monospace;

  /* Font Sizes */
  --sc-text-xs:   0.75rem;
  --sc-text-sm:   0.875rem;
  --sc-text-base: 1rem;
  --sc-text-lg:   1.125rem;
  --sc-text-xl:   1.25rem;
  --sc-text-2xl:  1.5rem;
  --sc-text-3xl:  1.875rem;
  --sc-text-4xl:  2.25rem;

  /* Letter Spacing */
  --sc-tracking-wordmark:  0.2em;
  --sc-tracking-label:     0.12em;
  --sc-tracking-body:      0.01em;

  /* Spacing Scale */
  --sc-space-1:   0.25rem;
  --sc-space-2:   0.5rem;
  --sc-space-3:   0.75rem;
  --sc-space-4:   1rem;
  --sc-space-6:   1.5rem;
  --sc-space-8:   2rem;
  --sc-space-12:  3rem;
  --sc-space-16:  4rem;

  /* Border Radius */
  --sc-radius-sm:  4px;
  --sc-radius-md:  8px;
  --sc-radius-lg:  12px;
  --sc-radius-xl:  16px;

  /* Borders */
  --sc-border-linen:  0.5px solid #E2DDD4;
  --sc-border-navy:   0.5px solid #1E3A5F;

  /* Gold Rule */
  --sc-rule-height:  3px;
  --sc-rule-color:   #B8902A;
}
```

## 5. Tailwind Config Extension

Merge into `theme.extend`:

```ts
colors: {
  sc: {
    navy:       '#0D1A2D',
    'navy-mid': '#1E3A5F',
    brass:      '#B8902A',
    teal:       '#2A9D8F',
    parchment:  '#F5F3EE',
    slate:      '#64748B',
    linen:      '#E2DDD4',
  },
},
fontFamily: {
  display: ["Georgia", "'Times New Roman'", "serif"],
  mono:    ["'Courier New'", "Courier", "monospace"],
},
letterSpacing: {
  wordmark: '0.2em',
  label:    '0.12em',
},
```

## 6. Document / Letterhead Layout

```
+----------------------------------------------------------+
|  [DARK NAVY BAND - padding: 20px 28px]                   |
|  [Logo: logo-light.svg, h=40]    [Contact - right]       |
|  sidebarcode.com  |  Legal AI Consulting  |  Tempe, AZ   |
+----------------------------------------------------------+
|  [BRASS RULE - height: 3px, full width, #B8902A]         |
+----------------------------------------------------------+
|  [DOCUMENT BODY - background #F5F3EE, padding: 32px]     |
|  ...content...                                           |
+----------------------------------------------------------+
|  [LINEN DIVIDER - 0.5px, #E2DDD4]                       |
+----------------------------------------------------------+
|  [FOOTER - white bg, padding: 12px 28px]                 |
|  Banfield Consulting, LLC dba Sidebar Code - Confidential|
+----------------------------------------------------------+
```

## 7. Business Card Spec

**Front (dark):** Background #0D1A2D, logo-dark.svg top-left h=28, gold rule 20px wide 2px height, name Georgia 13px white bold, title system sans 9px #94A3B8, contact Courier New 8.5px #64748B.

**Back (light):** Background #F5F3EE border 0.5px #E2DDD4, icon-light.svg centered h=50, tagline system sans 9px #94A3B8 uppercase centered.

**Dimensions:** 3.5" x 2" at 300dpi (1050px x 600px).

## 8. Navigation Bar

```css
.sc-navbar {
  background:  var(--sc-navy);
  padding:     0 var(--sc-space-8);
  height:      64px;
  display:     flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--sc-navy-mid);
}

.sc-nav-link {
  font-family:     var(--sc-font-body);
  font-size:       var(--sc-text-sm);
  color:           #94A3B8;
  letter-spacing:  0.04em;
  text-decoration: none;
  transition:      color 150ms ease;
}
.sc-nav-link:hover { color: var(--sc-white); }

.sc-nav-cta {
  background:    var(--sc-brass);
  color:         var(--sc-navy);
  font-size:     var(--sc-text-sm);
  font-weight:   600;
  padding:       8px 20px;
  border-radius: var(--sc-radius-md);
  text-decoration: none;
  letter-spacing: 0.02em;
  transition:    opacity 150ms ease;
}
.sc-nav-cta:hover { opacity: 0.88; }
```

## 9. Email Signature HTML

```html
<table cellpadding="0" cellspacing="0" border="0" style="font-family: system-ui, -apple-system, sans-serif;">
  <tr>
    <td style="padding-bottom: 12px;">
      <img src="https://sidebarcode.com/brand/logo-dark.svg" alt="Sidebar Code" height="32" style="display: block;" />
    </td>
  </tr>
  <tr>
    <td style="padding-bottom: 2px;">
      <span style="font-size: 13px; font-weight: 700; color: #0D1A2D;">Kyle Banfield</span>
    </td>
  </tr>
  <tr>
    <td style="padding-bottom: 10px;">
      <span style="font-size: 11px; color: #64748B; letter-spacing: 0.04em;">
        Founder, Legal AI Strategist &nbsp;|&nbsp; Sidebar Code
      </span>
    </td>
  </tr>
  <tr>
    <td style="padding-bottom: 4px;">
      <div style="width: 28px; height: 2px; background: #B8902A; border-radius: 1px;"></div>
    </td>
  </tr>
  <tr>
    <td>
      <a href="https://sidebarcode.com" style="font-size: 11px; color: #B8902A; text-decoration: none; font-family: 'Courier New', monospace;">
        sidebarcode.com
      </a>
    </td>
  </tr>
</table>
```

## 10. File Structure (Target)

```
public/
  brand/
    logo-dark.svg
    logo-light.svg
    icon-dark.svg
    icon-light.svg
    wordmark-dark.svg
    wordmark-light.svg
    favicon.svg          <- use icon-dark.svg content
    favicon.ico          <- generate from icon-dark.svg at 32x32

src/
  components/
    brand/
      SidebarCodeLogo.tsx
      index.ts           <- re-export { SidebarCodeLogo }
  styles/
    brand-tokens.css     <- import in globals.css
```

## 11. Usage Rules (Hard Constraints)

1. Never alter the three logo colors: Teal #2A9D8F, Brass #B8902A, Navy #0D1A2D
2. Never place the logo on any background other than Navy, Parchment, or White without explicit approval
3. Never stretch, skew, rotate, or restyle the logo SVG geometry
4. Always use the gold brass rule (height: 3px; background: #B8902A) as the divider between dark header and light body in all document templates
5. Always use Georgia serif for display headings and all-caps wordmark treatments
6. Always use Courier New for code accent text, pricing callouts, and the "code" portion of the wordmark
7. Minimum usable logo height: 24px for full lockup, 16px for icon mark. Below these sizes, do not use the logo
8. Do not add drop shadows, glows, or background fills behind the SVG mark
9. The `< | >` mark is the symbol. Never substitute a different character or shape

---

*Sidebar Code — Banfield Consulting, LLC*
*sidebarcode.com*
