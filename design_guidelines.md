{
  "brand_attributes": [
    "serious",
    "developer-first",
    "security-grade",
    "high-signal / low-noise",
    "fast to scan",
    "trustworthy",
    "production-ready"
  ],
  "visual_personality": {
    "style_fusion": [
      "Swiss/International Typographic Style (grid + hierarchy)",
      "Security dashboard (dense but breathable)",
      "Subtle glass-on-charcoal surfaces (NOT gradients)",
      "Terminal/editor cues for code areas"
    ],
    "do_not": [
      "No playful illustrations",
      "No purple accents (security dashboards often use it; avoid to stay distinct)",
      "No neon-on-black everywhere (use restrained accents)",
      "No centered app container"
    ]
  },
  "typography": {
    "google_fonts_import": {
      "instructions": "Add to /app/frontend/public/index.html <head> (or equivalent) as <link> tags.",
      "links": [
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap",
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap"
      ]
    },
    "font_pairing": {
      "display": "Space Grotesk",
      "body": "IBM Plex Sans",
      "mono": "JetBrains Mono"
    },
    "tailwind_font_setup": {
      "instructions": "If Tailwind config is available, map fonts to CSS variables; otherwise set in index.css under :root and apply via utility classes.",
      "css_vars": {
        "--font-sans": "\"IBM Plex Sans\", ui-sans-serif, system-ui",
        "--font-display": "\"Space Grotesk\", ui-sans-serif, system-ui",
        "--font-mono": "\"JetBrains Mono\", ui-monospace, SFMono-Regular"
      },
      "usage_classes": {
        "display": "font-[var(--font-display)]",
        "body": "font-[var(--font-sans)]",
        "mono": "font-[var(--font-mono)]"
      }
    },
    "text_size_hierarchy": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base",
      "small": "text-xs text-muted-foreground"
    },
    "weights": {
      "body_default": "font-normal",
      "ui_labels": "font-medium",
      "headings": "font-semibold",
      "numbers_stats": "font-semibold tracking-tight"
    },
    "line_height": {
      "body": "leading-6",
      "dense_lists": "leading-5",
      "code": "leading-6"
    }
  },
  "color_system": {
    "notes": [
      "Dark theme is non-negotiable: use layered charcoals, not pure black.",
      "Severity colors are fixed by requirement; tune shades for dark backgrounds.",
      "Avoid large gradients; use subtle noise + thin borders for depth."
    ],
    "design_tokens_css": {
      "instructions": "Replace the current :root and .dark tokens in /app/frontend/src/index.css with these (keep Tailwind @layer structure).",
      "tokens": {
        "--background": "220 18% 6%",
        "--foreground": "210 20% 96%",
        "--card": "220 18% 8%",
        "--card-foreground": "210 20% 96%",
        "--popover": "220 18% 8%",
        "--popover-foreground": "210 20% 96%",
        "--primary": "174 72% 40%",
        "--primary-foreground": "220 18% 8%",
        "--secondary": "220 14% 14%",
        "--secondary-foreground": "210 20% 96%",
        "--muted": "220 14% 14%",
        "--muted-foreground": "215 14% 70%",
        "--accent": "220 14% 14%",
        "--accent-foreground": "210 20% 96%",
        "--destructive": "0 72% 52%",
        "--destructive-foreground": "210 20% 96%",
        "--border": "220 14% 18%",
        "--input": "220 14% 18%",
        "--ring": "174 72% 40%",
        "--radius": "0.75rem",
        "--chart-1": "174 72% 40%",
        "--chart-2": "28 92% 56%",
        "--chart-3": "48 96% 58%",
        "--chart-4": "210 90% 60%",
        "--chart-5": "0 72% 52%",
        "--severity-critical": "0 72% 52%",
        "--severity-high": "28 92% 56%",
        "--severity-medium": "48 96% 58%",
        "--severity-low": "210 90% 60%",
        "--surface-1": "220 18% 8%",
        "--surface-2": "220 16% 10%",
        "--surface-3": "220 14% 12%",
        "--shadow-elev-1": "0 0% 0% / 0.35",
        "--shadow-elev-2": "0 0% 0% / 0.55"
      }
    },
    "palette_hex_reference": {
      "bg": "#0B0F14",
      "surface": "#101722",
      "surface_2": "#141E2B",
      "border": "#223042",
      "text": "#E7EEF7",
      "muted": "#A9B6C6",
      "primary_teal": "#1FB6A6",
      "focus_teal": "#2AD3C2",
      "critical": "#EF4444",
      "high": "#F97316",
      "medium": "#FACC15",
      "low": "#60A5FA"
    },
    "gradients_and_texture": {
      "allowed_usage": [
        "Only as a thin top-of-page ambient glow behind the header (<= 12vh)",
        "Only as decorative overlay in hero/summary header area"
      ],
      "safe_gradient_examples": [
        "radial-gradient(600px circle at 20% 0%, rgba(31,182,166,0.18), transparent 55%)",
        "radial-gradient(500px circle at 80% 10%, rgba(96,165,250,0.12), transparent 60%)"
      ],
      "noise_overlay_css": "background-image: url('data:image/svg+xml,%3Csvg xmlns=\"http://www.w3.org/2000/svg\" width=\"160\" height=\"160\"%3E%3Cfilter id=\"n\"%3E%3CfeTurbulence type=\"fractalNoise\" baseFrequency=\"0.8\" numOctaves=\"3\" stitchTiles=\"stitch\"/%3E%3C/filter%3E%3Crect width=\"160\" height=\"160\" filter=\"url(%23n)\" opacity=\"0.08\"/%3E%3C/svg%3E');"
    }
  },
  "layout_and_grid": {
    "app_shell": {
      "desktop": "Sidebar (280px) + main content; main content max-w-none; use container only for inner sections if needed.",
      "mobile": "Sidebar becomes Sheet/Drawer; top bar shows section title + search.",
      "tailwind_scaffold": {
        "root": "min-h-dvh bg-background text-foreground",
        "shell": "grid grid-cols-1 lg:grid-cols-[280px_1fr]",
        "sidebar": "hidden lg:flex lg:flex-col lg:sticky lg:top-0 lg:h-dvh border-r border-border bg-[hsl(var(--surface-1))]",
        "main": "min-w-0",
        "main_inner": "px-4 py-6 md:px-6 lg:px-8"
      }
    },
    "content_grid": {
      "summary_cards": "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4",
      "two_column_sections": "grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-6",
      "issue_list": "space-y-3",
      "kanban": "grid grid-cols-1 md:grid-cols-3 gap-4"
    },
    "spacing": {
      "section_padding": "py-6 md:py-8",
      "card_padding": "p-4 md:p-5",
      "dense_row_padding": "py-2.5"
    }
  },
  "components": {
    "component_path": {
      "navigation": [
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/navigation-menu.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/separator.jsx",
        "/app/frontend/src/components/ui/breadcrumb.jsx"
      ],
      "filters_search": [
        "/app/frontend/src/components/ui/input.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/command.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/tabs.jsx"
      ],
      "issue_cards": [
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/collapsible.jsx",
        "/app/frontend/src/components/ui/accordion.jsx",
        "/app/frontend/src/components/ui/tooltip.jsx",
        "/app/frontend/src/components/ui/hover-card.jsx"
      ],
      "code_and_diffs": [
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/tabs.jsx"
      ],
      "dialogs_toasts": [
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/alert-dialog.jsx",
        "/app/frontend/src/components/ui/sonner.jsx"
      ],
      "data_display": [
        "/app/frontend/src/components/ui/table.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx"
      ]
    },
    "severity_badges": {
      "mapping": {
        "Critical": {
          "badge_class": "bg-[hsl(var(--severity-critical))]/15 text-[hsl(var(--severity-critical))] border border-[hsl(var(--severity-critical))]/30",
          "dot_class": "bg-[hsl(var(--severity-critical))]"
        },
        "High": {
          "badge_class": "bg-[hsl(var(--severity-high))]/15 text-[hsl(var(--severity-high))] border border-[hsl(var(--severity-high))]/30",
          "dot_class": "bg-[hsl(var(--severity-high))]"
        },
        "Medium": {
          "badge_class": "bg-[hsl(var(--severity-medium))]/15 text-[hsl(var(--severity-medium))] border border-[hsl(var(--severity-medium))]/30",
          "dot_class": "bg-[hsl(var(--severity-medium))]"
        },
        "Low": {
          "badge_class": "bg-[hsl(var(--severity-low))]/15 text-[hsl(var(--severity-low))] border border-[hsl(var(--severity-low))]/30",
          "dot_class": "bg-[hsl(var(--severity-low))]"
        }
      },
      "badge_shape": "rounded-full px-2.5 py-0.5 text-xs font-medium"
    },
    "issue_card_anatomy": {
      "header_row": [
        "Severity badge + category chip",
        "Issue title (1 line clamp)",
        "Right side: file path + line, GitHub link icon, expand/collapse"
      ],
      "body": [
        "Impact summary (2–3 lines)",
        "Tabs: Details | Evidence | Fix | References",
        "Code block with copy button",
        "Optional: before/after diff view"
      ],
      "footer": [
        "Tags (OWASP, CWE, module)",
        "Confidence indicator",
        "Created/updated timestamps"
      ]
    },
    "buttons": {
      "brand": "Professional / Corporate",
      "tokens": {
        "--btn-radius": "12px",
        "--btn-shadow": "0 10px 30px rgba(0,0,0,0.35)",
        "--btn-press-scale": "0.98"
      },
      "variants": {
        "primary": "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        "secondary": "bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border",
        "ghost": "hover:bg-accent hover:text-accent-foreground"
      },
      "micro_interaction": "On hover: subtle translateY(-1px) + shadow increase; on active: scale to 0.98. Do NOT use transition-all; use transition-[background-color,box-shadow,color,opacity] duration-200."
    },
    "sidebar_nav": {
      "items": [
        "Dashboard",
        "Architecture",
        "Bugs & Vulnerabilities",
        "Refactoring",
        "AI/ML Optimization",
        "Action Plan"
      ],
      "active_state": "bg-accent text-foreground border border-border",
      "inactive_state": "text-muted-foreground hover:text-foreground hover:bg-accent/60",
      "item_class": "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-[background-color,color] duration-200"
    },
    "search_filter_bar": {
      "layout": "Sticky within main content top (below header) on desktop; collapses into 2-row on mobile.",
      "elements": [
        "Search input (CmdK optional)",
        "Severity Select",
        "Category Select",
        "Sort Select (severity desc, newest, file path)",
        "Export Markdown button"
      ]
    },
    "charts": {
      "library": "recharts",
      "install": "npm i recharts",
      "severity_donut": {
        "notes": "Use donut with center label: total issues. Use muted gridlines; legend uses severity dots.",
        "colors": {
          "Critical": "hsl(var(--severity-critical))",
          "High": "hsl(var(--severity-high))",
          "Medium": "hsl(var(--severity-medium))",
          "Low": "hsl(var(--severity-low))"
        }
      },
      "bar_chart": {
        "notes": "Use stacked bar by section (Architecture/Bugs/Refactor/AI/ActionPlan) with severity stacks."
      }
    },
    "action_plan_kanban": {
      "columns": [
        "P0 Critical",
        "P1 High",
        "P2 Medium/Low"
      ],
      "column_card_style": "rounded-xl border border-border bg-[hsl(var(--surface-1))]",
      "item_style": "rounded-lg border border-border bg-[hsl(var(--surface-2))] p-3 hover:bg-[hsl(var(--surface-3))] transition-[background-color] duration-200",
      "empty_state": "Use Skeleton + muted text: 'No items in this lane'."
    },
    "code_blocks": {
      "library": "react-syntax-highlighter",
      "install": "npm i react-syntax-highlighter",
      "style": "Use a dark theme (e.g., oneDark) but reduce saturation; wrap in Card with border.",
      "container_class": "relative rounded-xl border border-border bg-[hsl(var(--surface-2))]",
      "code_class": "font-[var(--font-mono)] text-[13px] leading-6",
      "copy_button": "Use shadcn Button size=sm variant=secondary; position absolute top-3 right-3"
    },
    "github_deep_links": {
      "pattern": "https://github.com/<org>/<repo>/blob/<branch>/<path>#L<start>-L<end>",
      "ui": "Show file path as mono text; add external-link icon button with Tooltip."
    },
    "loading_and_error_states": {
      "loading": "Use /ui/skeleton.jsx for summary cards, issue list rows, and chart placeholders.",
      "error": "Use /ui/alert.jsx with destructive variant; include retry button."
    }
  },
  "motion_and_microinteractions": {
    "library": "framer-motion",
    "install": "npm i framer-motion",
    "principles": [
      "Entrance: fade + slight y (8px) for cards; stagger lists.",
      "Expand/collapse: height animation for issue details (Collapsible).",
      "Hover: raise cards by 1px + shadow; keep subtle.",
      "Reduce motion: respect prefers-reduced-motion; disable parallax and heavy transitions."
    ],
    "durations": {
      "fast": "150ms",
      "base": "200ms",
      "slow": "280ms"
    },
    "easing": {
      "standard": "cubic-bezier(0.2, 0.8, 0.2, 1)"
    }
  },
  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text and badges on dark surfaces.",
      "Visible focus rings: use ring color = --ring (teal).",
      "Keyboard navigation for sidebar, filters, collapsibles.",
      "Tooltips must not be the only way to access info (duplicate in aria-label).",
      "Charts: provide textual summary + table fallback for screen readers."
    ],
    "aria_patterns": {
      "icon_buttons": "Always include aria-label (e.g., aria-label=\"Open GitHub link\").",
      "collapsible": "Use aria-expanded and aria-controls."
    }
  },
  "data_testid_conventions": {
    "rules": [
      "kebab-case",
      "role-based, not appearance-based",
      "apply to all interactive + key informational elements"
    ],
    "examples": {
      "sidebar": "data-testid=\"sidebar-nav\"",
      "nav_item": "data-testid=\"sidebar-nav-item-bugs\"",
      "search": "data-testid=\"issue-search-input\"",
      "severity_filter": "data-testid=\"severity-filter-select\"",
      "issue_card": "data-testid=\"issue-card-<issueId>\"",
      "issue_expand": "data-testid=\"issue-card-expand-button-<issueId>\"",
      "copy_code": "data-testid=\"codeblock-copy-button-<issueId>\"",
      "export": "data-testid=\"export-markdown-button\"",
      "kanban_column": "data-testid=\"action-plan-column-p0\"",
      "chart": "data-testid=\"severity-distribution-chart\""
    }
  },
  "image_urls": {
    "notes": "This app is primarily data/UI; avoid stock photos. Use subtle SVG patterns/noise only.",
    "assets": [
      {
        "category": "background_texture",
        "description": "Inline SVG noise overlay (see color_system.gradients_and_texture.noise_overlay_css).",
        "url": "inline-data-uri"
      }
    ]
  },
  "instructions_to_main_agent": [
    "Remove/avoid App.css centered header styles; do not use .App-header align-items:center/justify-content:center for the dashboard shell.",
    "Switch the app to dark by default by applying class 'dark' on <html> or <body> (preferred: <html class=\"dark\">).",
    "Replace index.css tokens with the provided dark-first token set; keep Tailwind @layer base structure.",
    "Use shadcn components from /src/components/ui for all primitives (Select, Sheet, Tabs, Collapsible, Skeleton, etc.).",
    "Implement IssueCard with Collapsible + Tabs; include copy-to-clipboard and GitHub deep link icon button with Tooltip.",
    "Add recharts for severity donut/bar; ensure chart has textual summary for accessibility.",
    "Add react-syntax-highlighter for code blocks; wrap in ScrollArea for long code.",
    "Add framer-motion for subtle entrance + expand animations; respect prefers-reduced-motion.",
    "Every interactive element and key info must include data-testid attributes per conventions.",
    "Do NOT use transition: all; use transition-[background-color,color,box-shadow,opacity] only."
  ],
  "general_ui_ux_design_guidelines": [
    "- You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms",
    "- You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text",
    "- NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json",
    "",
    " **GRADIENT RESTRICTION RULE**",
    "NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc",
    "NEVER use dark gradients for logo, testimonial, footer etc",
    "NEVER let gradients cover more than 20% of the viewport.",
    "NEVER apply gradients to text-heavy content or reading areas.",
    "NEVER use gradients on small UI elements (<100px width).",
    "NEVER stack multiple gradient layers in the same viewport.",
    "",
    "**ENFORCEMENT RULE:**",
    "    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors",
    "",
    "**How and where to use:**",
    "   • Section backgrounds (not content backgrounds)",
    "   • Hero section header content. Eg: dark to light to dark color",
    "   • Decorative overlays and accent elements only",
    "   • Hero section with 2-3 mild color",
    "   • Gradients creation can be done for any angle say horizontal, vertical or diagonal",
    "",
    "- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**",
    "",
    "</Font Guidelines>",
    "",
    "- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead.",
    "",
    "- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.",
    "",
    "- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.",
    "",
    "- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly",
    "    Eg: - if it implies playful/energetic, choose a colorful scheme",
    "           - if it implies monochrome/minimal, choose a black–white/neutral scheme",
    "",
    "**Component Reuse:**",
    "\t- Prioritize using pre-existing components from src/components/ui when applicable",
    "\t- Create new components that match the style and conventions of existing components when needed",
    "\t- Examine existing components to understand the project's component patterns before creating new ones",
    "",
    "**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component",
    "",
    "**Best Practices:**",
    "\t- Use Shadcn/UI as the primary component library for consistency and accessibility",
    "\t- Import path: ./components/[component-name]",
    "",
    "**Export Conventions:**",
    "\t- Components MUST use named exports (export const ComponentName = ...)",
    "\t- Pages MUST use default exports (export default function PageName() {...})",
    "",
    "**Toasts:**",
    "  - Use `sonner` for toasts\"",
    "  - Sonner component are located in `/app/src/components/ui/sonner.tsx`",
    "",
    "Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
  ]
}
