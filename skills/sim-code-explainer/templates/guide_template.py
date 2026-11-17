"""GUIDE TEMPLATE - copy to the work folder as make_guide.py, fill every TODO, run:  python make_guide.py

Chapter blueprint (keep the order; drop a chapter only if it truly does not apply):
  cover -> scope -> how to read -> contents
  1 Python from Zero        (auto from detected features, tied to this program)
  2 The Ideas Behind ...    (domain background a beginner needs; concept diagrams)
  3 The System Model        (equations numbered (3.x) + map equation -> function -> lines)
  4 The Code, Block by Block (every block: summary, code, line table, boxes)
  5 The Control Panel       (every tunable variable: meaning, default, range, effect)
  6 How the Simulation Works (time stepping / Monte Carlo / event loop; data flow; validity)
  7 Results                 (every figure + numbers from the actual run + interpretation)
  8 Summary / lessons       (+ scope reminder)
  9 Hands-on exercises      (predict -> run -> check)
  10 Glossary (+ references)
"""
import json
import os
import sys

SKILL = os.environ.get("SCE_SKILL_DIR", "/path/to/sim-code-explainer")          # TODO: set (or export SCE_SKILL_DIR)
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from guide_lib import *                      # noqa: E402,F403
from diagram_kit import pipeline, loop_flow  # noqa: E402

CODE_FILE = "my_sim_marked.py"               # TODO: the block-marked copy of the user's code
RUN_DIR = "run_out"                          # TODO: output folder of run_and_capture.py
FIG = f"{RUN_DIR}/figures"
ANALYSIS = json.load(open("my_sim.analysis.json"))   # TODO: from code_parser.py
RUN = json.load(open(f"{RUN_DIR}/run_report.json"))
STDOUT = open(f"{RUN_DIR}/stdout.txt").read()         # parse the numbers you quote from here

load_source(CODE_FILE)
B = SRC["blocks"]

# ---------------------------------------------------------------- diagrams (draw them once)
pipeline([("INPUT / SETTINGS", [("Parameters", "make_config")]),          # TODO: the real stages of the program
          ("MODEL", [("Plant / system", "plant_step"), ("Controller", "update")]),
          ("OUTPUT", [("Metrics", "metrics"), ("Plots", "")])],
         "build/diag/pipeline.png")

set_meta(title="TODO Name of the Simulator",                       # short, e.g. "DC Motor PID Control"
         subtitle="Build it in Python, simulate it, measure TODO,\nand understand every line and every curve.",
         tags=["TODO tag 1", "TODO tag 2", "TODO tag 3"],          # 4-6 short tags: methods, metrics
         cover_image="build/diag/pipeline.png",
         companion=f"Companion files: {os.path.basename(CODE_FILE)}  •  notebook (.ipynb)  •  figures/")

story = start_story()

# ---------------------------------------------------------------- scope + how to read + contents
story += scope_page(
    included=["TODO what the code models", "TODO measurements it makes"],
    excluded=["TODO what it deliberately ignores (ideal sensors, no noise, ...)"],
    statement="This report explains **TODO** — one paragraph: what system, what question the simulation answers.",
    note="TODO the single most important limitation the reader must keep in mind when quoting the results.")
story += legend_page()
story += section("Running the code in Google Colab", toc=False)
story += bullets(["Open **colab.research.google.com** → **File → Upload notebook** → choose the `.ipynb`.",
                  "Click **Runtime → Run all**. TODO: runtime and any `pip install` needed.",
                  "Change a value in a cell and re-run from that cell to experiment."])
story += toc_page()

# ---------------------------------------------------------------- 1 Python from zero
story += python_chapter(ANALYSIS["feature_ids"], num=1, uses={
    # TODO: tie features to THIS program, e.g. "classes": "`class PID` (line 18) keeps the integral between steps."
})

# ---------------------------------------------------------------- 2 ideas
story += chapter(2, "TODO The Ideas Behind ...", "the background you need before the code")
story += section("2.1  TODO The problem")
story += para("TODO plain-language explanation, then the key idea.")
story += box("idea", "TODO the one insight that makes the method work.")

# ---------------------------------------------------------------- 3 system model
story += chapter(3, "The System Model", "every equation, mapped to the code")
story += figure("build/diag/pipeline.png", 1.0, "Figure 3.1 – TODO caption")
story += section("3.1  TODO Equations")
story += eq_box([r"$TODO\ \frac{dx}{dt} = f(x,u)$"], "(3.1)")
story += table([["Eq.", "What", "Function", "Lines"],
                ["(3.1)", "TODO", "`TODO`", f"{B[1]['start']}–{B[1]['end']}"]])
story += section("3.x  Assumptions (what is idealised)")
story += bullets(["TODO"])

# ---------------------------------------------------------------- 4 code block by block
story += chapter(4, "The Code, Block by Block", "every group of related lines: what, why, and what if")
story += table([["Block", "Role"]] + [[str(n), B[n]["title"]] for n in sorted(B)], [1.6 * cm, PAGE_W - 1.6 * cm])
# One call per block. Line rows: (substring that appears on the line, explanation). Explain EVERY non-trivial line.
story += explain_block(
    0, "TODO one sentence.",
    [("import numpy", "TODO"),
     ],
    boxes=[("py", "TODO Python point first used here"),
           ("idea", "TODO why"),
           ("what", "TODO what changes if the reader edits these values"),
           ])
# ... TODO explain_block(1, ...), explain_block(2, ...), ... for every block

# ---------------------------------------------------------------- 5 control panel
story += chapter(5, "The Control Panel", "every variable, what it means, and what changing it does")
rows = [["Variable", "Meaning", "Default", "Range", "Effect of increasing it"]]
for p in ANALYSIS["parameters"]:
    rows.append([f"`{p['name']}`", "TODO", p["value"], "TODO", "TODO"])   # TODO fill meaning/range/effect
story += table(rows, [2.6 * cm, 3.6 * cm, 1.8 * cm, 2.4 * cm, PAGE_W - 10.4 * cm], font_size=8)
story += section("5.2  The big trade-offs")
story += table([["If you want...", "turn this knob", "and you pay with..."], ["TODO", "TODO", "TODO"]])

# ---------------------------------------------------------------- 6 how the simulation works
story += chapter(6, "How the Simulation Works", "from one step to a result you can trust")
story += para("TODO time stepping / Monte Carlo / events; accuracy (step size, number of runs); runtime "
              f"(this run took {RUN['seconds']} s).")

# ---------------------------------------------------------------- 7 results
story += chapter(7, "Experiments and Results", "running the program and reading every figure")
for f in RUN["figures"]:
    story += figure(f"{FIG}/{f}", 0.85, f"TODO caption for {f}")
    story += box("res", ["TODO what we see (quote numbers from STDOUT)", "TODO why (link to equation (3.x))"])

# ---------------------------------------------------------------- 8-10
story += chapter(8, "Summary", "what the simulation teaches")
story += bullets(["TODO lesson 1", "TODO lesson 2"])
story += box("note", "TODO scope reminder.", title="SCOPE")
story += chapter(9, "Hands-On Exercises", "predict first, then run and check")
for i, (title, task, expect) in enumerate([("TODO", "TODO task", "TODO expected outcome")], 1):
    story += box("try", [f"**Task:** {task}", f"**What you should see:** {expect}"], title=f"EXERCISE {i}: {title.upper()}")
story += chapter(10, "Glossary")
story += table([["Term", "Meaning"], ["TODO", "TODO"]], [3.6 * cm, PAGE_W - 3.6 * cm])

build_pdf(story, "TODO_Guide.pdf")
