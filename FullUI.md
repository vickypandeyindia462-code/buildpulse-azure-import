The current implementation does **not** match the intended BuildPulse UI. It currently looks like a default Streamlit dashboard (left gray panel with a Page dropdown, oversized plain headings, a large white canvas, sparse text metrics, and a generic line chart). Please replace that visual treatment with the following application design.

## Do not use this visual pattern

- Do not use a `Page` selectbox/dropdown as the primary navigation.
- Do not use a light-gray Streamlit side panel or generic Streamlit default widgets.
- Do not use large empty white areas with plain text/unstyled KPI values.
- Do not make the dashboard look like a data-science notebook or default admin page.
- Do not put a `Deploy` control or other Streamlit chrome in the product UI.

## BuildPulse visual target

Create a polished, responsive enterprise application shell.

```text
┌────────────── DARK NAVY SIDEBAR (252px) ──────────────┬──────────── WHITE TOP BAR ─────────────┐
│ ✦ BuildPulse                                           │ Operations / Executive Dashboard          │
│ AI OPS COMMAND CENTER                                  │                           ● All monitored  │
│                                                        ├────────────────────────────────────────┤
│ ▦  Executive Dashboard  ← selected                     │                                        │
│ ✦  AI Copilot Chat                                     │            page content                  │
│                                                        │                                        │
│ INTELLIGENCE                                           │                                        │
│ ◉  Risk Radar                                          │                                        │
│ ⌕  Knowledge Discovery                                 │                                        │
│ ⇧  Contribute Knowledge                                │                                        │
│ ⚡  Incident Intelligence                               │                                        │
│ ♙  SME Directory                                       │                                        │
│                                                        │                                        │
│ GOVERNANCE                                             │                                        │
│ ◈  Security & Trust                                    │                                        │
│                                                        │                                        │
│ [AR] Asha Rao · Release Manager                        │                                        │
└────────────────────────────────────────────────────────┴────────────────────────────────────────┘
```

### Exact visual tokens

```css
:root {
  --ink: #1D2433;
  --muted: #718097;
  --line: #E7EBF2;
  --page-bg: #F7F8FB;
  --navy: #111B2C;
  --navy-selected: #23304A;
  --primary: #456BF5;
  --primary-soft: #EEF2FF;
  --critical: #E6535D;
  --critical-soft: #FFF0F0;
  --warning: #D88D21;
  --warning-soft: #FFF7E8;
  --success: #15966C;
  --success-soft: #E9F8F1;
}
```

Use these fonts:

- `DM Sans` for normal interface text
- `Manrope` for headings and large KPI values
- `DM Mono` for small uppercase labels, metadata, scores, and status pills

Font sources are available from Google Fonts:

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
```

## Executive Dashboard — exact placement

Use a light `#F7F8FB` content background with 43px horizontal page padding on desktop. Cards are white, have a `#E7EBF2` 1px border, 8–10px corner radius, and 16px gaps.

```text
MONDAY, 14 SEPTEMBER                                      [ ✦ Ask BuildPulse AI ]
Good morning, Asha.
Here’s the pulse of your engineering organization.

[ RELEASE READINESS ] [ OPEN INCIDENTS ] [ KNOWLEDGE HEALTH ] [ SME COVERAGE ]
[ 82%              ] [ 7              ] [ 94%              ] [ 88%          ]
[ ↑ 6% last week   ] [ 1 needs action  ] [ ↑ 12 docs        ] [ 4 need backup]

[ Release 24.3 — readiness                             ][ Live signals / needs attention ]
[ circular 82% indicator | 2 blockers, explanation     ][ three compact alert rows        ]

[ Incidents by service / small bar chart                ][ Critical system owner list      ]
```

Specific controls:

- `✦ Ask BuildPulse AI` is at the **top-right** of the page title row. Blue `#456BF5`, white text, 6px radius.
- The four KPI cards are in an equal four-column row, not loose unframed text on the canvas.
- Metric label: 10px uppercase DM Mono, muted blue-gray.
- Metric value: 29px Manrope, dark ink.
- Release status is an amber pill: pale amber background with `At risk` text.
- Critical alert uses a small red dot plus a pale-red `Critical` pill.
- The owner list uses colored circular initials/avatars and small availability dots—not a raw HTML table as the primary treatment.

## All other page layout expectations

### AI Copilot Chat

- Center a narrow 910px chat column.
- Top: AI mark, eyebrow label, `What can I help you understand?`, and three white outlined suggested-prompt buttons.
- Bottom composer: add icon left, text field center, blue send button right, security note underneath.
- Assistant answers are white cards on the left with blue AI badge and source/evidence cards. User messages are pale blue and right-aligned.

### Risk Radar

- Page title at left; Release 24.3 selector at right.
- One three-column hero card: `72 / 100` score at left, summary and blue `Create mitigation plan` in center, deterministic risk factors at right.
- Below, three equal risk-driver cards: Open P1 (+35 red), Coverage gap (+22 amber), Change volume (+15 blue).

### Knowledge Discovery

- Title left; blue `⇧ Contribute knowledge` button right.
- Full search bar below, with search icon left and blue Search button right.
- 205px filter rail at left and white semantic-result cards stacked at right.
- Each result needs document icon, colored document-type pill, title, short description, owner/date/relevance, and arrow action.

### Contribute Knowledge

- Title left; outline `← Back to discovery` button right.
- Wide form card on the left (~70%) and narrow guidance/contribution cards on the right (~30%).
- Form order: pale-blue security note; large blue-dashed upload zone; selected-file confirmation; two-column metadata inputs; description; two access radio cards; full-width blue `Submit for indexing →` button.
- On submit, show a lower-right dark-navy toast with green check icon.

### Incident Intelligence

- Title left; blue `＋ Log incident` right.
- Tabs below title.
- Two-column workspace: ~300px incident list on left; selected incident detail on right.
- Selected list item: pale blue background and blue left border.
- Detail: P1 status pill, blue `Open war room` button, vertical timeline with blue dots, similar-incident rows.

### SME Directory

- Title left; blue `＋ Add ownership` right.
- Search field under title; light-gray `Filters ▾` control at right end.
- White table card with monospace uppercase header, owner avatars, and colored coverage pills.

### Security & Trust

- Title left; outline `Export audit log` right.
- First row: large “All safeguards active” card left; two smaller metric cards right.
- Second row: controls card left; audit trail card right.
- Green success checks show active controls; audit rows show time, query summary, agents used, and green completion mark.

## Interaction requirements

- Sidebar labels must be actual navigation actions, not a single dropdown.
- Use page routing or a show/hide SPA pattern; a full backend is not required for the UI demo.
- Link relevant actions across screens: Risk P1 → Incidents; coverage gap → SME Directory; contribute CTA → Contribute Knowledge.
- Copilot should render a demo answer with source cards when the user sends a question.
- File selection should show filename and readiness state; submit should show the confirmation toast.
- Responsive behavior: sidebar collapses behind a menu; multi-column cards/forms stack; wide tables can horizontally scroll.

## Reference implementation

The intended HTML prototype already exists here. Treat it as the visual reference and preserve/port its styles and interactions rather than redesigning it as a default Streamlit page:

```text
C:\Users\Vijay\Documents\Codex\2026-09-14\iwa\outputs\buildpulse-wireframes\index.html
C:\Users\Vijay\Documents\Codex\2026-09-14\iwa\outputs\buildpulse-wireframes\styles.css
C:\Users\Vijay\Documents\Codex\2026-09-14\iwa\outputs\buildpulse-wireframes\app.js
```

If the target remains Streamlit, use custom CSS and HTML components so its default sidebar, selectbox, heading, chart, button, and table styling are fully replaced by this design. Do not stop at generic Streamlit defaults.



# Paste this into the other agent — UI fix required

The current output is **not acceptable** as the BuildPulse UI. It has copied the text/data, but it is still rendering default Streamlit controls and layout:

- radio-button circles beside every navigation label
- duplicate/extra navigation entries (`Ingest`, `SME Lookup`, `RAG Query`, `Security Scan`, `Agents Dashboard`)
- plain text KPI values without cards
- oversized blank white area
- no fixed dark sidebar
- no top bar, card system, status pills, visual hierarchy, or action-button styling

This is a **styling/implementation failure**, not a data failure. Do not continue polishing the default Streamlit page. Replace the page shell and controls.

## Required outcome

The finished result must visually match the existing BuildPulse static reference:

```text
C:\Users\Vijay\Documents\Codex\2026-09-14\iwa\outputs\buildpulse-wireframes\index.html
C:\Users\Vijay\Documents\Codex\2026-09-14\iwa\outputs\buildpulse-wireframes\styles.css
C:\Users\Vijay\Documents\Codex\2026-09-14\iwa\outputs\buildpulse-wireframes\app.js
```

Use those files directly as the source of truth. Do not reinterpret them as a default Streamlit dashboard.

## Preferred implementation: keep the working HTML UI

If a backend is not yet needed, use the existing `index.html` as the application UI. It already contains all eight screens, the correct sidebar, responsive styles, page switching, chat demo interaction, file-selection behavior, and upload toast.

Do not rebuild it with `st.radio`, `st.selectbox`, `st.metric`, `st.dataframe`, or default Streamlit buttons.

## If Streamlit must be used

Render the complete HTML/CSS/JS application as a custom component, rather than translating each element to standard Streamlit widgets.

Implementation expectations:

1. Load the full content of `index.html`, inline the contents of `styles.css` and `app.js` or serve them as accessible assets.
2. Render that full application inside one custom HTML component/container.
3. Make the component tall enough to display the app (for example, `height=1000` or dynamic height), with no internal border or default padding.
4. Do not render any Streamlit navigation, radio controls, page selector, default header, default footer, or duplicated sidebar alongside the HTML app.
5. If a Streamlit shell remains, hide its default chrome and let the custom app own the entire visual area.

Illustrative direction only:

```python
# Do not create st.radio/st.selectbox/st.metric UI.
# Instead, render the existing HTML prototype as one custom component.
import streamlit.components.v1 as components

components.html(full_buildpulse_html, height=1050, scrolling=True)
```

If custom components are not allowed, then port the source CSS class-for-class and use `st.markdown(..., unsafe_allow_html=True)` for the shell and cards. Do not use the default Streamlit widgets for visible navigation or KPI cards.

## Exact cleanup needed

### Remove these default UI artifacts

- All radio circles from navigation
- `Page` dropdown or radio/page selector
- The dark rectangle at the top of the sidebar with no content
- `Deploy` / default Streamlit toolbar/chrome from the product surface
- Duplicate entries: `Ingest`, `SME Lookup`, `RAG Query`, `Security Scan`, and `Agents Dashboard`
- Unframed individual KPI texts

### Keep this navigation only

```text
▦ Executive Dashboard
✦ AI Copilot Chat
◉ Risk Radar
⌕ Knowledge Discovery
⇧ Contribute Knowledge
⚡ Incident Intelligence
♙ SME Directory
◈ Security & Trust
```

### Required desktop geometry

- Sidebar: fixed left, 252px wide, full viewport height, background `#111B2C`
- Main area: starts immediately after sidebar; background `#F7F8FB`
- Top bar: fixed/normal 67px white strip with a bottom border `#E7EBF2`
- Main content: 43px horizontal padding, 39px top padding
- Page cards: white fill, `#E7EBF2` 1px border, 8–10px radius, 16px gaps

### Required Executive Dashboard structure

```text
top title row:       Monday label + “Good morning, Asha.”              [blue Ask BuildPulse AI]
metric row:          [82% Release readiness] [7 Open incidents] [94% Knowledge health] [88% SME coverage]
content row:         [Release 24.3 card / 82% ring / blockers]        [Needs attention alert list]
lower content row:   [Incidents by service chart]                       [Critical system owner cards]
```
