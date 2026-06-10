# DESIGN.md — EcoTrace India
### UI/UX Design Specification
> Anti-Gravity must follow this design spec consistently across all pages.
> Do not change colors, fonts, or component styles between sessions.

---

## <ColorPalette>

```css
:root {
  /* Primary */
  --green-dark:    #1B5E20;   /* Deep forest green — headers, CTAs */
  --green-mid:     #2E7D32;   /* Mid green — buttons, accents */
  --green-light:   #43A047;   /* Light green — hover states */
  --green-pale:    #E8F5E9;   /* Very pale green — backgrounds, cards */

  /* Background */
  --bg-dark:       #0D1F0E;   /* Near-black green — main background */
  --bg-card:       #152416;   /* Dark card background */
  --bg-elevated:   #1E3320;   /* Slightly elevated surfaces */

  /* Text */
  --text-primary:  #F1F8E9;   /* Off-white — main text */
  --text-secondary:#A5D6A7;   /* Pale green — secondary text */
  --text-muted:    #66BB6A;   /* Muted green — labels, hints */

  /* Semantic */
  --eco-excellent: #00C853;   /* A+ score */
  --eco-good:      #43A047;   /* A/B score */
  --eco-average:   #FDD835;   /* C score */
  --eco-warning:   #FB8C00;   /* D score */
  --eco-danger:    #E53935;   /* F score */

  /* Borders */
  --border:        rgba(67, 160, 71, 0.2);
  --border-strong: rgba(67, 160, 71, 0.4);

  /* India accent */
  --saffron:       #FF9933;   /* Use sparingly — India flag reference */
  --india-blue:    #1A237E;   /* Use sparingly */
}
```

</ColorPalette>

---

## <Typography>

```css
/* Import in all HTML files */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Usage */
font-family: 'Syne', sans-serif;    /* Headings, nav logo, badges, scores */
font-family: 'DM Sans', sans-serif; /* Body text, labels, descriptions */

/* Scale */
--text-xs:   0.72rem;   /* Labels, legal text */
--text-sm:   0.85rem;   /* Secondary content */
--text-base: 0.95rem;   /* Body text */
--text-lg:   1.1rem;    /* Subheadings */
--text-xl:   1.4rem;    /* Section headings */
--text-2xl:  1.8rem;    /* Page titles */
--text-hero: clamp(2.2rem, 5vw, 3.5rem);  /* Hero titles */
```

</Typography>

---

## <Components>

### Navigation Bar
```
- Left: Logo "EcoTrace" in Syne 800 weight, --green-light colored
- Right: Progress indicator (Civic Points equivalent = "Eco Points")
- Thin tricolor stripe at very top (saffron/white/green — India flag colors)
- Backdrop blur on scroll
```

### Cards
```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 1.5rem;
  transition: border-color 0.2s, transform 0.2s;
}
.card:hover {
  border-color: var(--border-strong);
  transform: translateY(-3px);
}
```

### Primary Button
```css
.btn-primary {
  background: var(--green-mid);
  color: white;
  border: none;
  padding: 0.85rem 2rem;
  border-radius: 99px;
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  box-shadow: 0 8px 25px rgba(46, 125, 50, 0.35);
  transition: all 0.2s;
}
.btn-primary:hover {
  background: var(--green-light);
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(46, 125, 50, 0.45);
}
```

### Eco Score Badge
```
- Large circular badge, centered
- Grade letter in Syne 800, 3rem
- Color from eco_score.color value
- Glowing ring animation matching the grade color
- Label text below in DM Sans
```

### Progress Bar (for calculator steps)
```css
.progress-bar {
  height: 6px;
  background: var(--border);
  border-radius: 99px;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--green-mid), var(--eco-excellent));
  border-radius: 99px;
  transition: width 0.5s ease;
}
```

### Form Inputs
```css
.form-input {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text-primary);
  padding: 0.75rem 1rem;
}
.form-input:focus {
  border-color: var(--green-light);
  outline: none;
  box-shadow: 0 0 0 3px rgba(67,160,71,0.15);
}
```

### Category Breakdown Bar
```
- Horizontal stacked bar chart
- Energy: #1976D2 (blue)
- Transport: #F57C00 (orange)
- Diet: #388E3C (green)
- Waste: #757575 (grey)
- Tooltip on hover showing exact value
```

</Components>

---

## <PageLayouts>

### Landing Page (index.html)
```
[Tricolor stripe]
[Nav]
[Hero section]
  - Animated leaf/earth icon
  - Headline: "Know Your Carbon Footprint"
  - Subline: "Built for India. Powered by Google AI."
  - CTA button: "Calculate Mine →"
[3 feature cards row]
  - 🧮 Calculate | 🤖 AI Insights | 📈 Track Progress
[India stats section]
  - "Average Indian emits 2.19 tonnes/year"
  - "Urban Indian emits ~5 tonnes/year"
  - "Global target by 2050: 2 tonnes"
[Footer]
```

### Calculator Page (calculator.html)
```
[Nav]
[Step indicator: 1 2 3 4] — Energy / Transport / Diet / Waste
[Step content — one category per step]
[Running total widget — updates in real time]
[Back / Next buttons]
[Final: Calculate button]
```

### Results Page (results.html)
```
[Nav]
[Eco Score Badge — large, center]
[Your footprint: X.XX tonnes/year]
[Benchmark comparison bar]
[Category breakdown chart]
[3 AI Insight cards]
[Tree offset section]
[CTA: Generate My 30-Day Plan →]
[CTA: Track Monthly Progress →]
```

### Action Plan Page (action_plan.html)
```
[Nav]
[Header: "Your 30-Day Eco Action Plan"]
[Estimated saving banner]
[4 week accordion cards]
[Copy/Share button]
```

</PageLayouts>

---

## <AnimationsAndMicroInteractions>

- Floating animation on hero icon (same as CivicPulse mascot)
- Counter animation on footprint number (count up from 0 to result)
- Eco Score badge reveal with scale + glow animation
- Confetti on A+ or A grade
- Smooth step transitions in calculator (slide left/right)
- Chart bars animate in on page load
- Points toast notification (same pattern as CivicPulse)

---

## <Accessibility>

- All form inputs have aria-label
- Color is never the only indicator (always paired with text/icon)
- Keyboard navigation works throughout
- Focus rings visible on all interactive elements
- Minimum contrast ratio 4.5:1 on all text
- Screen reader friendly (semantic HTML — use nav, main, section, article)
- Alt text on all images and SVGs
<!-- Just add this CDN for the chart — that's all you actually need -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>