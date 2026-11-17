---
name: sim-code-explainer
description: Turn any Python simulation or engineering program into a colourful, zero-to-hero PDF guide that explains every block and line, the theory and system model behind it, every variable and what changing it does, and the actual results of running it (plus a Google Colab notebook). Use this whenever the user uploads or points to Python code and wants it explained, documented, taught, turned into a report/tutorial/lecture notes, or "explained from zero for someone who doesn't know Python" - for any domain (communications/OFDM/5G, control/PID, power systems, signal processing, queueing, Monte-Carlo, physics, ML, finance models). Also use it when the user asks to first WRITE a simulator for a system (e.g. "simulate OFDM and measure BER vs SNR, then explain the code in a PDF") and then explain it.
---

# Simulation Code Explainer

Produce a guide that lets a reader with **zero Python knowledge** understand a program completely: what
problem it solves, the theory, how every group of lines works, why it is written that way, what each
variable does to the results, and what the actual results mean.

Examples (look at them before writing your first guide):
- `examples/pid_motor/` - a complete worked case: original code, block-marked code, the full
  `make_guide.py` and the resulting 31-page PDF. **Use its `make_guide.py` as the model for yours.**
- `examples/mm1_queue/` - a shorter guide (24 pages) for an event-driven simulation.
- `examples/ofdm_reference_guide.pdf` - a 65-page guide for a 5G MIMO-OFDM simulator: the depth to aim
  for when the code is large and the domain is rich.

Deliverables: `<Name>_Guide.pdf`, `<name>.ipynb` (Colab), the block-marked `.py`, and the figures.

## Workflow

### 0. Agree on scope (one short message, then proceed)
Confirm in one message, with sensible defaults so the user can just say "go":
- **audience** (default: zero Python, basic engineering maths),
- **language** of the PDF (default English; the PDF engine is Latin/Greek only, so warn that Arabic or
  other right-to-left output is not supported),
- **scope**: what the report covers and what it deliberately leaves out. Users care about this - they
  will present the report, so the scope must be stated explicitly in the PDF (a scope page is built in).
- If the user has no code yet and wants you to write the simulator first, also agree on the system
  model, the parameters and the measurements, then write clean, block-marked code (see "Writing
  the simulator" below) before continuing.

Set up: `SK=<this skill folder>`; work in a fresh folder; `pip install reportlab pygments matplotlib numpy`
if missing (pdftoppm from poppler-utils is used for QA if present).

### 1. Analyse the code
```bash
python $SK/scripts/code_parser.py user_code.py --write-markers user_code_marked.py
```
This prints the blocks, functions/classes, tunable parameters and the Python features used, and writes
`user_code.analysis.json`. If the file had no `# ==== [BLOCK n] Title ====` markers it writes a copy
with proposed markers. Then **open the marked copy and refine it by hand**:
- give every block a meaningful title ("Motor model: one Euler step" rather than "motor_step()"),
- split blocks longer than ~40-60 lines at natural boundaries (a marker may be indented inside a
  function; the block then ends at the next marker),
- never change the program's logic; only add or edit marker comments (and, at most, explanatory
  comments). Re-run `code_parser.py` on the marked file afterwards.

Read the whole program carefully. You must understand every line before explaining it - trace the
data flow (what each array/object holds, its shape/units) and identify the system model it implements.

### 2. Run it and capture the results
```bash
python $SK/scripts/run_and_capture.py user_code_marked.py --out run_out --timeout 900
```
Figures land in `run_out/figures/`: those the program saves keep their own names, those it only
shows become `auto_01.png, auto_02.png, ...` in display order. Printed output goes to
`run_out/stdout.txt`, a summary to `run_out/run_report.json` (status, run time, `work_dir`). Look at
every figure (open the PNGs) and read the output; these are the only numbers you may quote as results.
To compute extra numbers (a value at another setting, a check against theory, exercise outcomes),
import the marked program as a module in `make_guide.py` and call its functions, as
`examples/pid_motor/make_guide.py` does - never type numbers by hand.
- If the run is slow, look for a quick-mode flag in the code or ask the user before editing values;
  say in the guide which settings were used.
- If it cannot run here (missing data files, GPU, licences, hours of runtime), still write the guide,
  but say clearly in the scope page and results chapter that results are not shown and why. Never
  invent numbers or draw "expected" plots as if they were results.
- If the code has a bug, tell the user; explain the code as written and mention the issue in a
  `warn` box rather than silently fixing it.

### 3. Write the guide script
Copy `templates/guide_template.py` to `make_guide.py` in the work folder and fill it in (set
`SCE_SKILL_DIR` or the `SKILL` path at its top). Read
`references/api.md` for the helper functions and `references/writing_guide.md` for how to write each
part - it describes the depth and tone that make these guides good. Key points:
- Follow the chapter blueprint at the top of the template (scope, Python from zero, ideas, system
  model, code block by block, control panel, how the simulation works, results, summary,
  exercises, glossary).
- **Every block** gets `explain_block(...)`: one-sentence summary, the code with real line numbers, a
  line-by-line table covering every non-trivial line, and the boxes that apply (idea / model / what /
  py / warn).
- **Every tunable variable** appears in the control-panel table with meaning, default, sensible
  range and the effect of increasing it on the results.
- **Every figure** of the run appears in the results chapter with a `res` box that quotes the real
  numbers (parse them from `stdout.txt` or recompute them from saved data) and explains *why* the
  curve looks the way it does, linking back to equations (3.x) and to variables.
- Draw 1-3 concept diagrams with `scripts/diagram_kit.py` (pipeline of the system with function names,
  a simulation-loop flowchart); add matplotlib explanatory plots where a picture teaches better.

### 4. Build and check visually
```bash
python make_guide.py
python $SK/scripts/render_check.py <Name>_Guide.pdf --out qa
```
Open the contact sheets in `qa/` and fix what you see: overlapping text, figures too small or split,
empty half pages, red "figure not found" boxes, unreadable equations, tables overflowing. Zoom into
a few pages with `--pages 3 12 25 --dpi 80`. Iterate until clean.

### 5. Notebook and delivery
```bash
python $SK/scripts/make_notebook.py user_code_marked.py <name>.ipynb --title "..." [--pip "pkg1 pkg2"]
```
Execute it once if Jupyter is available (`jupyter nbconvert --to notebook --execute`) to be sure it
runs top to bottom. Deliver the PDF, notebook, marked `.py` and figures (a zip is convenient), with a
short summary of what the guide contains and any limitations (e.g. results not reproducible here).

## Writing the simulator (only when the user asks you to create it)
Write code a beginner can follow: one `make_config(**changes)` (or a clear parameter section) with a
comment on every parameter, small single-purpose functions, `# ==== [BLOCK n] Title ====` markers from
the start, vectorised NumPy where natural, a fixed random seed, plots saved to `figures/` and also shown,
a theory/validation check against a closed-form result whenever one exists (it is what makes the
results trustworthy), and a `FAST` flag if the full run takes more than a few minutes.

## Quality bar (why it matters)
- The reader is a beginner who will present or reuse this work: a wrong number or an unexplained line
  breaks their trust and their presentation. Accuracy beats length.
- Explanations should connect three levels every time: *Python mechanics* (what the line does) ->
  *engineering meaning* (what it represents in the system) -> *consequence* (what changes in the
  results if it changes).
- Quote results only from the actual run, with units, and say how reliable they are (statistical
  noise, step size, number of runs).
- Keep the scope honest: list what the model ignores; do not add features the user did not ask for.
