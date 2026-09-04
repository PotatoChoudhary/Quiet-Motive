"""DRAFT.md -> paper.pdf. Re-run after filling the [FILL] blocks."""
import base64, os, re, subprocess, sys, markdown

SRC = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/Potato/quiet-motive/DRAFT.md"
FIGS = "/home/claude/figs/"
OUT = "/home/claude/build/"

# figure -> (anchor text that must already be in the draft, caption)
FIGURES = [
 ("fig1_design.png", "### 3.1 Arms",
  "The design. Three arms share a scenario and an action; only the injected cause "
  "differs. The investigator never sees the arm label or the cause block, and the "
  "four evidence conditions run on the same 87 investigated cases."),
 ("fig5_selection.png", "### 3.3 Scenarios",
  "Only trajectories that took the concerning action are investigated, and that "
  "selection favours the arm-D runs where suppression failed. The manipulation is "
  "87 against 48 across all trajectories and 95 against 75 in the sample analysed."),
 ("fig2_ladder.png", "### 4.2 Requiring a quote",
  "Raw accuracy on the 87 investigated cases. Withholding the reasoning costs "
  "nothing. Requiring a quote from it is the only condition that beats showing it."),
 ("fig3_paired.png", "### 4.3 The interventions",
  "The same 87 cases in every condition, so each contrast is a paired test. The "
  "counterfactual interventions move 52 verdicts and net to zero; the forced quote "
  "moves 13 and nets to +9."),
 ("fig4_per_arm.png", "### 4.4 The preregistered",
  "Accuracy by arm. Under an investigator that convicts 82 to 91 per cent of the "
  "time, arms A and D are correct for free. Every informative number is an arm B "
  "number."),
 ("fig6_matching.png", "### 4.5 A hidden directive",
  "Arms A and D share a cause and should act at similar rates. They do in "
  "test_edit and do not in log_delete, so the legibility twin holds in one "
  "scenario and breaks in the other."),
 ("fig7_probe_layers.png", "### 4.6 What the failures",
  "Cross-scenario transfer for the A-versus-B direction against the quiet arm-D "
  "readout, by layer. The direction is stable above the embedding; the arm-D "
  "number is not."),
 ("fig8_probe_action.png", "## 5 Discussion",
  "Every arm-A trajectory carries the directive but only 9 of 45 acted on it, and "
  "the probe scores the two groups alike. Arm B, which has no directive, is "
  "equally flat. The probe reads the directive's presence."),
]

def b64(p):
    return "data:image/png;base64," + base64.b64encode(open(p,"rb").read()).decode()

md = open(SRC, encoding="utf-8").read()

# byline: keep the author and the venue on separate lines
md = md.replace("\nDeven Choudhary\nMATS 12.0 application task, September 2026\n",
                "\n<p class='byline'>Deven Choudhary<br>"
                "MATS 12.0 application task, September 2026</p>\n")

# strip the working-notes header block
md = re.sub(r"^> FINAL DRAFT.*?\n(?=\n---)", "", md, flags=re.S|re.M)

# insert figures before their anchors
for i,(f,anchor,cap) in enumerate(FIGURES, start=1):
    block = (f'\n<figure>\n<img src="{b64(FIGS+f)}" alt="Figure {i}">\n'
             f'<figcaption><b>Figure {i}.</b> {cap}</figcaption>\n</figure>\n\n')
    idx = md.find(anchor)
    if idx == -1:
        print(f"  ! anchor not found for {f}: {anchor!r}")
        continue
    md = md[:idx] + block + md[idx:]

# render [FILL ...] blocks as visible callouts
def fill(m):
    t = re.sub(r"\s+"," ", m.group(1)).strip().lstrip(":.").strip()
    return ('<div class="todo"><span class="todolab">TO WRITE</span>' + t + "</div>")
md = re.sub(r"`\[FILL(.*?)\]`", fill, md, flags=re.S)

body = markdown.markdown(md, extensions=["tables","attr_list","md_in_html","sane_lists"])

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm;
        @bottom-center { content: counter(page); } }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Charter","Georgia","DejaVu Serif",serif; font-size: 10.2pt;
       line-height: 1.52; color: #14140f; max-width: 100%; margin: 0; }
h1 { font-size: 19pt; line-height: 1.22; margin: 0 0 2mm 0; letter-spacing: -0.01em; }
h1 + p, p.byline { font-size: 10.2pt; color: #52514e; margin: 0 0 1mm 0;
  text-align: left; line-height: 1.42; }
h2 { font-size: 13pt; margin: 9mm 0 2.5mm 0; padding-bottom: 1.2mm;
     border-bottom: 0.6pt solid #d9d8d3; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 6mm 0 2mm 0; page-break-after: avoid; }
h2:first-of-type { margin-top: 6mm; }
p { margin: 0 0 2.6mm 0; text-align: justify; hyphens: auto; }
ul,ol { margin: 0 0 3mm 0; padding-left: 5mm; }
li { margin-bottom: 1.4mm; }
code { font-family: "DejaVu Sans Mono",monospace; font-size: 8.6pt;
       background: #f2f1ed; padding: 0.3mm 0.9mm; border-radius: 1.5pt; }
blockquote { margin: 3mm 0 3mm 4mm; padding-left: 3mm; border-left: 2pt solid #d9d8d3;
             color: #52514e; font-style: italic; }
table { border-collapse: collapse; width: 100%; margin: 3mm 0 4mm 0;
        font-size: 8.9pt; font-family: "DejaVu Sans",sans-serif;
        page-break-inside: avoid; }
th { text-align: left; font-weight: 600; border-bottom: 0.9pt solid #14140f;
     padding: 1.4mm 2mm 1.2mm 0; }
td { padding: 1.1mm 2mm 1.1mm 0; border-bottom: 0.4pt solid #e6e5e1;
     vertical-align: top; }
tr:last-child td { border-bottom: 0.9pt solid #14140f; }
figure { margin: 5mm 0 5mm 0; page-break-inside: avoid; text-align: center; }
figure img { width: 100%; max-width: 158mm; height: auto; }
figcaption { font-family: "DejaVu Sans",sans-serif; font-size: 8.3pt; color: #52514e;
             text-align: left; margin-top: 1.8mm; line-height: 1.42; }
hr { border: none; border-top: 0.6pt solid #d9d8d3; margin: 6mm 0; }
strong { font-weight: 600; }
.todo { font-family: "DejaVu Sans",sans-serif; font-size: 8.6pt; color: #8a4a10;
        background: #fdf6ee; border: 0.6pt solid #eab785; border-radius: 2pt;
        padding: 2.4mm 3mm; margin: 3mm 0; line-height: 1.45; }
.todolab { display: inline-block; font-weight: 700; font-size: 7.4pt;
           letter-spacing: 0.08em; color: #fff; background: #c2761f;
           padding: 0.5mm 1.6mm; border-radius: 1.5pt; margin-right: 2mm; }
h2 + p + h3, h2 + h3 { margin-top: 3mm; }
"""

html = f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>{body}"
open(OUT+"paper.html","w",encoding="utf-8").write(html)
subprocess.run(["/opt/pw-browsers/chromium-1194/chrome-linux/chrome","--headless",
                "--no-sandbox","--disable-gpu","--no-pdf-header-footer",
                f"--print-to-pdf={OUT}quiet-motive-paper.pdf", OUT+"paper.html"],
               check=True, capture_output=True)
print("wrote", OUT+"quiet-motive-paper.pdf",
      os.path.getsize(OUT+"quiet-motive-paper.pdf")//1024, "KB")
