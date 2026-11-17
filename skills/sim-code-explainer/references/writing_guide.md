# Writing guide: how to explain code from zero

The guide is good when a beginner can (1) read any line and say what it does, (2) say why it is
there in terms of the real system, and (3) predict how the results move when a value changes.
Write with that reader in mind: curious, intelligent, but new to both Python and the domain.

## Contents
1. Chapter by chapter
2. The block recipe (most important)
3. Results chapter
4. Tone, honesty and common failures
5. Sizing

## 1. Chapter by chapter
- **Scope page** - one paragraph on what the work is, a two-column table included / deliberately
  excluded, and an IMPORTANT note with the main limitation (e.g. "uncoded BER", "ideal sensor",
  "Euler integration with dt = 1 ms"). Users present these reports; the scope protects them.
- **Python from Zero** - generated from detected features. Use `uses=` to tie each lesson to this
  program ("`class PID` (line 18) remembers the integral between calls"). Add lessons for libraries the
  catalog lacks.
- **Ideas behind** - the domain background as a story: the problem -> why naive approaches fail ->
  the key idea -> how it shows up in the code. Use pictures (matplotlib) generously: a concept plot is
  worth a page of text. 4-8 sections.
- **System model** - write the system as numbered equations (3.1), (3.2)... in the order data flows;
  each equation followed by one sentence in words. End with a table equation -> function -> lines and a
  list of assumptions (what is idealised).
- **Code block by block** - see section 2.
- **Control panel** - a table of every tunable value: name, physical meaning (with units), default,
  sensible range, effect of increasing it. Then derived quantities (with their formulas and values) and
  a trade-off table ("if you want X, turn knob Y, and you pay with Z").
- **How the simulation works** - the numerical method in plain words: time stepping (step size and
  stability), Monte Carlo (how many runs, statistical uncertainty ~ 1/sqrt(events)), event-driven
  loops, optimisation iterations... plus a data-flow walk (shapes/units of the main arrays) and how the
  code was validated (comparison with theory).
- **Results** - section 3.
- **Summary** - 4-6 lessons, each anchored in a result; a scope reminder box.
- **Exercises** - 6-10: each "task" + "what you should see", ranging from changing one value to
  small code extensions. **Run every exercise** (a short verify script that imports the program's
  functions and changes the value) and write the measured outcome with numbers. Intuition is often
  wrong: in testing, "a 20x larger time step will visibly break the response" turned out false
  (overshoot 2.4 % vs 2.6 %). A wrong prediction in a teaching document is worse than none.
- **Glossary** - every acronym and technical term used.

## 2. The block recipe
For each block, `explain_block(n, summary, rows, boxes)`:
- **summary**: one sentence, the job of the block in the system ("One Euler step of the motor equations:
  new speed and current from the old ones and the applied voltage").
- **line rows**: every line that does something (skip blank lines, pure `return` of an obvious
  value, closing brackets). Each explanation says what the line does *and* what it means: "`di = (v - R*i
  - K*w) / L` - Kirchhoff's voltage law solved for the current derivative: supply minus resistive drop
  minus back-EMF, divided by the inductance (Eq. 3.2)". Mention shapes and units when they help.
- **boxes** (use those that genuinely apply, typically 2-4 per block):
  - `py` the first time a Python construct appears (not repeated later),
  - `idea` why the block exists / why this design (alternatives and why not),
  - `model` which equation it implements and how the symbols map to variables,
  - `what` concrete consequences of changing values in the block (direction and size of the effect),
  - `warn` real traps (off-by-one, units, sign, numerical stability, shapes).
Long blocks: show the code once, then split the line table with `a=`/`b=` and interleave boxes.

## 3. Results chapter
For every figure the program produced:
1. say how it was produced (which function, which settings),
2. the figure with a numbered caption,
3. a small table of the key numbers (parsed from stdout or recomputed),
4. a `res` box: what we see (with numbers and units) -> why (link to equations / mechanisms) -> what it
   means for the real system, and a `what` or `model` box if useful.
If simulation and theory are compared, state the agreement explicitly - it validates the code.

## 4. Tone, honesty and common failures
- Friendly and direct; short sentences; define a term the first time; no filler.
- Never invent numbers. If a value is not in the run output, compute it (e.g. load saved data, call the
  program's functions) or omit it.
- Don't overstate: "the PID settles in 1.03 s in this simulation (ideal sensor, no noise)".
- Say when results are noisy (few Monte Carlo runs) or step-size dependent.
- Common failures to avoid: explaining only *what* a line does but not *why*; skipping "obvious" lines
  that a beginner would not understand (slicing, reshape, broadcasting, `self`); results without
  numbers; figures without explanation; generic exercises; missing units.

## 5. Sizing
Rough guide: ~1 page per 15-25 lines of code for the block chapter, plus 15-25 pages for the other
chapters. A 100-line program -> ~25-35 pages; a 600-line program -> ~60 pages. For programs over
~1500 lines, explain at module/function level and give line-by-line tables only for the core blocks
(say so in the scope page).
