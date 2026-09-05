"""DRAFT.md -> quiet-motive-writeup.docx, for upload to Google Docs."""
import os, re, subprocess, sys

SRC  = "/mnt/user-data/uploads/Potato/quiet-motive/DRAFT.md"
FIGS = "/home/claude/figs/"
OUT  = "/home/claude/build/"

FIGURES = [
 ("fig1_design.png", "## 2 Related work",
  "The design. Three arms share a scenario and an action; only the injected cause "
  "differs. The investigator never sees the arm label or the cause block, and the "
  "four evidence conditions run on the same 87 investigated cases."),
 ("fig5_selection.png", "### 3.3 Scenarios",
  "Only trajectories that took the concerning action are investigated, and that "
  "selection favours the arm-D runs where suppression failed."),
 ("fig2_ladder.png", "**The control, and where it broke.**",
  "Raw accuracy on the 87 investigated cases. Withholding the reasoning costs "
  "nothing. Requiring a quote from it is the only condition that beats showing it. "
  "The dashed line is a rule that convicts everything."),
 ("fig3_paired.png", "### 4.3 The interventions",
  "The same 87 cases in every condition, so each contrast is a paired test."),
 ("fig4_per_arm.png", "### 4.4 The preregistered",
  "Accuracy by arm. Arms A and D are correct for free under a convicting "
  "investigator; every informative number is an arm B number."),
 ("fig6_matching.png", "### 4.5 A hidden directive",
  "Arms A and D share a cause and should act at similar rates. They do in "
  "test_edit and do not in log_delete."),
 ("fig7_probe_layers.png", "### 4.6 Four ways these results",
  "Cross-scenario transfer against the quiet arm-D readout, by layer. The "
  "direction is stable above the embedding; the arm-D number is not."),
 ("fig8_probe_action.png", "## 5 Discussion",
  "Every arm-A trajectory carries the directive but only 9 of 45 acted on it, and "
  "the probe scores the two groups alike."),
]

md = open(SRC, encoding="utf-8").read()
md = re.sub(r"^> FINAL DRAFT.*?\n(?=\n---)", "", md, flags=re.S | re.M)
md = md.replace("\nDeven Choudhary\nMATS 12.0 application task, September 2026\n",
                "\nDeven Choudhary\n\nMATS 12.0 application task, September 2026\n")

for i, (f, anchor, cap) in enumerate(FIGURES, start=1):
    idx = md.find(anchor)
    if idx == -1:
        print(f"  ! anchor missing for {f}"); continue
    block = f"\n![Figure {i}. {cap}]({FIGS}{f})\n\n"
    md = md[:idx] + block + md[idx:]

# [FILL] blocks survive as visible bold callouts the author can find with ctrl-F
md = re.sub(r"`\[FILL(.*?)\]`",
            lambda m: "**[TO WRITE] " + re.sub(r"\s+", " ", m.group(1)).strip().lstrip(":.").strip() + "**",
            md, flags=re.S)

tmp = OUT + "_docx_src.md"
open(tmp, "w", encoding="utf-8").write(md)

# -smart keeps straight quotes and "..." rather than curly quotes and an ellipsis
# glyph; no --toc, because Google Docs builds its own outline and pandoc's
# static TOC renders empty until a reader refreshes the field.
cmd = ["pandoc", tmp, "-f", "markdown+pipe_tables+backtick_code_blocks-smart",
       "-t", "docx", "-o", OUT + "quiet-motive-writeup.docx"]
subprocess.run(cmd, check=True)
print("wrote", OUT + "quiet-motive-writeup.docx",
      os.path.getsize(OUT + "quiet-motive-writeup.docx") // 1024, "KB")
