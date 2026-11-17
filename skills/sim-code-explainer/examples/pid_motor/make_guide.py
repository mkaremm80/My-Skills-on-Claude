import json
import os
import re
import sys

SKILL = os.environ.get("SCE_SKILL_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from guide_lib import *                      # noqa
from diagram_kit import pipeline, loop_flow, boxes_row  # noqa

CODE_FILE = "pid_motor_marked.py"
RUN_DIR = "run_out"
FIG = f"{RUN_DIR}/figures"
ANALYSIS = json.load(open("pid_motor.analysis.json"))
RUN = json.load(open(f"{RUN_DIR}/run_report.json"))
STDOUT = open(f"{RUN_DIR}/stdout.txt").read()
load_source(CODE_FILE)
B = SRC["blocks"]

# ---------------- numbers from the actual run
M = {}
for name, rise, ov, st, ss in re.findall(r"^(P only|PI|PID)\s+rise=([\d.na]+)s overshoot=([\d.]+)% settling=([\d.na]+)s ss_error=([-\d.]+)",
                                         STDOUT, re.M):
    M[name] = dict(rise=float(rise), ov=float(ov), st=float(st), ss=float(ss))
SWEEP = [(int(k), float(o), float(s)) for k, o, s in re.findall(r"Kp=\s*(\d+): overshoot=([\d.]+)%  settling=([\d.na]+)s", STDOUT)]

# ---------------- extra verification numbers computed with the program's own functions
sys.path.insert(0, RUN["work_dir"])
import importlib.util
spec = importlib.util.spec_from_file_location("pm", CODE_FILE)
pm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)
w_ss_theory = 100 / (100 + pm.R * pm.b / pm.K + pm.K)
w_dist_theory = (100 - pm.R * 0.05 / pm.K) / (100 + pm.R * pm.b / pm.K + pm.K)
t, w_p, u_p = pm.simulate(100, 0, 0, disturbance_time=1.5)
t, w_pid, u_pid = pm.simulate(100, 200, 10)
sat_steps = int((abs(u_pid) >= pm.V_MAX - 1e-9).sum())
dip = {n: min(pm.simulate(*g, disturbance_time=1.5)[1][1500:]) for n, g in
       {"P only": (100, 0, 0), "PI": (100, 200, 0), "PID": (100, 200, 10)}.items()}

# ---------------- diagrams
os.makedirs("build/diag", exist_ok=True)
pipeline([("CONTROLLER (class PID)", [("Setpoint\n1 rad/s", ""), ("Error e = r - w", ""), ("PID law\n+ saturation", "update")]),
          ("PLANT (DC motor)", [("Voltage v", ""), ("Electrical eq.\ncurrent i", "motor_step"), ("Mechanical eq.\nspeed w", "motor_step")]),
          ("MEASUREMENT", [("Speed w(t)", "simulate"), ("Metrics", "step_metrics"), ("Plots", "")])],
         "build/diag/pipeline.png")
loop_flow(["t = 0, state = 0", "error = setpoint - speed", "u = PID(error)", "Euler step of the motor",
           "store speed", "t += DT; t < T_END ?"], "build/diag/loop.png", back=(5, 1), back_label="YES -> next time step")
boxes_row([("P - Proportional", "reacts to the error NOW\nbigger error -> bigger push"),
           ("I - Integral", "remembers the PAST error\nremoves the steady-state error"),
           ("D - Derivative", "predicts the FUTURE\nbrakes when the error falls fast")], "build/diag/pid_cards.png")

set_meta(title="DC Motor PID Speed Control",
         subtitle="A Python simulation explained from zero:\nmodel, controller, step response and tuning.",
         tags=["DC motor model", "Discrete PID", "Anti-windup", "Euler integration", "Rise / overshoot / settling",
               "Disturbance rejection"],
         cover_image="build/diag/pipeline.png",
         companion="Companion files: pid_motor_marked.py  •  pid_motor.ipynb (Google Colab)  •  figures/")

story = start_story()
story += scope_page(
    included=["DC motor electrical + mechanical model (2 states)", "Discrete PID with saturation and anti-windup",
              "Step response, load-torque disturbance, Kp sweep", "Rise time, overshoot, settling time, steady-state error"],
    excluded=["Sensor noise, quantisation, encoder resolution", "Delays of a real digital controller",
              "Friction other than viscous, motor non-linearities", "Formal tuning methods (Ziegler-Nichols, loop shaping)"],
    statement="This report explains a short Python program that simulates the **speed control of a small DC motor** with "
              "a **PID controller**, and measures how well each controller version tracks a speed setpoint of 1 rad/s.",
    note="All results come from an **ideal simulation** (perfect speed measurement, Euler integration with "
         "DT = 1 ms, supply limited to ±24 V). They show trends and trade-offs, not the exact behaviour of a "
         "specific real motor.")
story += legend_page()
story += section("Running the code in Google Colab", toc=False)
story += bullets(["Open **colab.research.google.com** → **File → Upload notebook** → `pid_motor.ipynb`.",
                  f"Click **Runtime → Run all**. The whole program runs in about {RUN['seconds']:.0f} s; nothing to install.",
                  "Change a gain (e.g. `Kd`) in the last cell and re-run it to see the effect."])
story += toc_page()

story += python_chapter(ANALYSIS["feature_ids"], num=1, uses={
    "classes": f"`class PID` (line {find_line('class PID')}) keeps the integral and the previous error between two "
               "calls of `update()` — a controller needs memory.",
    "functions": "`motor_step`, `simulate` and `step_metrics` are the three building blocks of the program.",
    "numpy": "`np.zeros(n)` pre-allocates the speed and voltage histories; `np.argmax`, `np.where`, `np.clip` compute metrics.",
    "dicts": "`tunings` maps a controller name to its three gains; `step_metrics` returns a dict of four metrics.",
    "exceptions": f"`step_metrics` uses `try/except` (line {find_line('try:')}) as a safety net when computing the rise time.",
    "main_guard": f"Everything from line {find_line('if __name__')} on is the main program: the three experiments.",
    "comprehensions": f"Line {find_line('results = [step_metrics')} runs five simulations in one line.",
})

# ================================================================== 2 ideas
story += chapter(2, "The Ideas Behind Feedback Control", "motors, errors and the three PID actions")
story += section("2.1  The problem: making a motor spin at the right speed")
story += para("A DC motor turns electrical power into rotation. Apply a voltage and it speeds up until friction and "
              "the back-EMF balance the input. But how many volts give exactly 1 rad/s? That depends on the load, the "
              "temperature, the wear of the bearings… Setting the voltage once (**open-loop control**) is fragile.")
story += box("idea", "**Feedback**: measure the speed, compare it with the wanted speed (**setpoint**), and let the "
                     "difference — the **error** — decide the voltage. If the motor is too slow, push harder; "
                     "too fast, push less. This automatically compensates for unknown loads.")
story += section("2.2  The three actions of a PID controller")
story += figure("build/diag/pid_cards.png", 1.0, "Figure 2.1 – The three PID actions in one sentence each.")
story += bullets([
    "**P (proportional)**: u = K<sub>p</sub>·e. Simple and fast, but with a pure P controller a small error must "
    "remain, because without error there is no voltage (Experiment 1 shows 9 % error).",
    "**I (integral)**: u = K<sub>i</sub>·∫e dt. Keeps growing as long as any error exists, so it pushes the "
    "steady-state error to zero. Too much I causes overshoot and oscillation (Experiment 3).",
    "**D (derivative)**: u = K<sub>d</sub>·de/dt. Reacts to how fast the error changes — a brake that damps "
    "oscillations, but amplifies noise and gives a voltage “kick” when the setpoint jumps."])
story += section("2.3  How we judge a response")
story += table([["Metric", "Definition used in the code", "Good value"],
                ["Rise time", "time from 10 % to 90 % of the setpoint", "short"],
                ["Overshoot", "how far the peak goes above the setpoint, in %", "small (0–10 %)"],
                ["Settling time", "last time the speed is outside ±2 % of the setpoint", "short"],
                ["Steady-state error", "setpoint minus the final speed", "≈ 0"]],
               [3.4 * cm, 9 * cm, PAGE_W - 12.4 * cm])
story += section("2.4  Saturation and integrator windup")
story += para("A real supply cannot give infinite voltage; here it is limited to ±24 V (`V_MAX`). While the "
              "controller output is clipped, the integral keeps accumulating error it cannot act on (**windup**) and "
              "later causes a big overshoot. The code prevents this with **anti-windup**: when the output saturates, "
              "the last integration step is undone.")

# ================================================================== 3 model
story += chapter(3, "The System Model", "every equation, mapped to the code")
story += figure("build/diag/pipeline.png", 1.0, "Figure 3.1 – The closed loop: controller → motor → measured speed → controller.")
story += section("3.1  The DC motor")
story += para("Two physical laws describe the motor: Newton's law for the rotor and Kirchhoff's voltage law for the "
              "armature circuit. The two are coupled by the motor constant K (torque per ampere = back-EMF per rad/s).")
story += eq_box([r"$J\,\frac{d\omega}{dt} = K\,i - b\,\omega - T_L$"], "(3.1)")
story += eq_box([r"$L\,\frac{di}{dt} = v - R\,i - K\,\omega$"], "(3.2)")
story += para("ω = speed [rad/s], i = current [A], v = applied voltage [V], T<sub>L</sub> = load torque [N·m]. "
              "The two **states** of the motor are ω and i; the code stores them as `state = [w, i]`.")
story += section("3.2  Euler integration")
story += eq_box([r"$\omega_{k+1} = \omega_k + \Delta t\,\dot{\omega}_k,\qquad i_{k+1} = i_k + \Delta t\,\dot{i}_k$"], "(3.3)")
story += para("The computer cannot solve the differential equations exactly; it advances them in small steps "
              "Δt = `DT` = 1 ms using the slope at the current point (**forward Euler**).")
story += section("3.3  The discrete PID law")
story += eq_box([r"$e_k = r - \omega_k,\qquad I_k = I_{k-1} + e_k\,\Delta t,\qquad D_k = \frac{e_k - e_{k-1}}{\Delta t}$"], "(3.4)")
story += eq_box([r"$u_k = \mathrm{clip}\left(K_p e_k + K_i I_k + K_d D_k,\ -V_{max},\ V_{max}\right)$"], "(3.5)")
story += section("3.4  Useful closed-form results")
story += para("With a **P controller only**, the steady state (all derivatives zero) of (3.1)–(3.2) with "
              "v = K<sub>p</sub>(r − ω) gives:")
story += eq_box([r"$\omega_{ss} = \frac{K_p\,r - R\,T_L/K}{K_p + R\,b/K + K}$"], "(3.6)")
story += para(f"For K<sub>p</sub> = 100, r = 1 and no load: ω<sub>ss</sub> = {w_ss_theory:.4f} rad/s, i.e. an error of "
              f"{1 - w_ss_theory:.4f}. With the load T<sub>L</sub> = 0.05 N·m: ω<sub>ss</sub> = {w_dist_theory:.4f} rad/s. "
              "We will compare these with the simulation.")
story += para("The open-loop motor has two time constants. The characteristic polynomial (Js + b)(Ls + R) + K<super>2</super> "
              "has roots at about s = −2 and s = −10 1/s, i.e. time constants of 0.5 s and 0.1 s — "
              "500 and 100 times larger than DT, so Euler with 1 ms is accurate here.")
story += section("3.5  Map: equation → function → lines")
story += table([["Eq.", "What", "Function", "Lines"],
                ["(3.1)–(3.2)", "motor physics", "`motor_step`", f"{B[4]['start']}–{B[4]['end']}"],
                ["(3.3)", "Euler step", "`motor_step` (last line)", str(find_line("return np.array([w + DT"))],
                ["(3.4)–(3.5)", "PID + saturation + anti-windup", "`PID.update`", f"{find_line('def update')}–{B[3]['end']}"],
                ["loop", "time stepping", "`simulate`", f"{B[5]['start']}–{B[5]['end']}"],
                ["metrics", "rise, overshoot, settling", "`step_metrics`", f"{B[6]['start']}–{B[6]['end']}"]],
               [2.6 * cm, 5 * cm, 5 * cm, PAGE_W - 12.6 * cm])
story += section("3.6  Assumptions (what is idealised)")
story += bullets(["Perfect, noise-free speed measurement at every step.", "The controller computes instantly (no sampling delay).",
                  "Linear motor with viscous friction only; constant parameters.", "Forward Euler integration with DT = 1 ms.",
                  "The load torque appears as an ideal step at t = 1.5 s (Experiment 2)."])

# ================================================================== 4 code
story += chapter(4, "The Code, Block by Block", "every group of related lines: what, why, and what if")
story += table([["Block", "Role"]] + [[str(n), B[n]["title"]] for n in sorted(B)], [1.6 * cm, PAGE_W - 1.6 * cm])

story += explain_block(0, "Describe the program and load the two libraries it needs.",
    [('"""DC motor speed control', "A **docstring**: a text description of the whole file (Python ignores it when running)."),
     ("import numpy as np", "NumPy for arrays and maths (`np.zeros`, `np.clip`, `np.argmax`, …)."),
     ("import matplotlib.pyplot as plt", "Matplotlib for the figures.")])

story += explain_block(1, "The physical constants of the motor — the **plant** the controller must drive.",
    [("J = 0.01", "Rotor inertia: how hard it is to change the speed. Larger J → slower response."),
     ("b = 0.1", "Viscous friction: torque that opposes the speed, proportional to it."),
     ("K = 0.01", "Motor constant: torque per ampere and, equally, back-EMF voltage per rad/s."),
     ("R = 1.0", "Armature resistance: voltage lost as heat, R·i."),
     ("L = 0.5", "Armature inductance: makes the current change gradually (electrical time constant L/R = 0.5 s).")],
    boxes=[("model", "These five symbols are exactly J, b, K, R, L of Eqs. (3.1)–(3.2)."),
           ("what", ["Doubling `J` makes the motor twice as sluggish mechanically: slower rise, and the same gains give "
                     "more overshoot.", "A larger `K` gives more torque per ampere *and* more back-EMF; with the P controller "
                     "the steady-state error (3.6) changes through the term R·b/K."]),
           ("py", "These are module-level **constants** (UPPERCASE by convention, though `b` breaks it): every function in "
                  "the file can read them.")])

story += explain_block(2, "Numerical and hardware settings of the simulation.",
    [("DT = 1e-3", "Time step of the Euler integration and the controller sampling period: 1 ms."),
     ("T_END = 3.0", "Length of every simulation: 3 s."),
     ("V_MAX = 24.0", "Supply limit: the controller output is clipped to ±24 V.")],
    boxes=[("what", ["`DT` too large (e.g. 0.05 s) → Euler becomes inaccurate and can even go unstable; the derivative "
                     "term also becomes cruder. Smaller `DT` → more accurate but slower to simulate (3 000 steps now).",
                     "`V_MAX` smaller → the motor accelerates more slowly (saturated longer) and anti-windup matters more."])])

story += explain_block(3, "A class that holds the controller's gains and **memory**, and computes the voltage from the error.",
    [("class PID", "Defines a new type of object called `PID`."),
     ("def __init__", "Constructor: runs once when `PID(...)` is called."),
     ("self.kp, self.ki, self.kd, self.dt", "Store the three gains and the sampling time inside the object."),
     ("self.u_max = u_max", "Output limit (`None` = no limit)."),
     ("self.integral = 0.0", "Memory 1: running sum of error × dt (the I term)."),
     ("self.prev_error = 0.0", "Memory 2: last error, needed for the derivative."),
     ("def update(self, error)", "Called once per time step with the new error; returns the voltage."),
     ("self.integral += error * self.dt", "Rectangle-rule integration of the error (Eq. 3.4)."),
     ("derivative = (error - self.prev_error)", "Backward difference: change of error per second."),
     ("self.prev_error = error", "Remember this error for the next call."),
     ("u = self.kp * error", "The PID law (Eq. 3.5) before saturation."),
     ("if self.u_max is not None and abs(u)", "Is the requested voltage beyond the supply limit?"),
     ("self.integral -= error * self.dt", "**Anti-windup**: cancel the integration just done, so the integral does not grow while saturated."),
     ("u = np.clip(u, -self.u_max", "Limit the output to ±V<sub>max</sub>."),
     ("return u", "The voltage applied to the motor in this step.")],
    boxes=[("py", ["`self` is the object itself; `self.integral` is a variable that lives inside the object and survives "
                   "between calls. A plain function would forget it after each call.",
                   "`a, b = 1, 2` assigns several variables in one line (tuple unpacking)."]),
           ("idea", "The controller needs **state** (integral, previous error). A class bundles that state with the code "
                    "that uses it, and lets us create one fresh controller per simulation."),
           ("warn", [f"**Derivative kick:** at t = 0 the error jumps from 0 to 1, so D = K<sub>d</sub>·1/0.001 = 10 000 V "
                     f"is requested. It is clipped to 24 V. Real controllers often differentiate the measurement instead of "
                     f"the error to avoid this.", f"In the PID run the output is saturated for {sat_steps} of the 3 000 steps "
                     f"({sat_steps * 1e-3:.2f} s): the start of every response is limited by the supply, not by the gains."])])

story += explain_block(4, "Advance the motor by one time step: compute the two derivatives from the physics, then take an Euler step.",
    [("def motor_step(state, v, load_torque=0.0)", "Inputs: current state [w, i], applied voltage v, optional load torque."),
     ("w, i = state", "Unpack the 2-element array into speed and current."),
     ("dw = (K * i - b * w - load_torque) / J", "Eq. (3.1) solved for dω/dt: motor torque minus friction minus load, divided by inertia."),
     ("di = (v - R * i - K * w) / L", "Eq. (3.2) solved for di/dt: supply minus resistive drop minus back-EMF, divided by inductance."),
     ("return np.array([w + DT * dw", "Forward Euler (Eq. 3.3): new = old + DT × slope.")],
    boxes=[("model", "This function **is** the plant model. Replacing it (e.g. with a temperature or a tank model) would "
                     "let the same PID class control a different system."),
           ("warn", "Units matter: J in kg·m<super>2</super>, b in N·m·s, K in N·m/A. Mixing e.g. "
                    "rpm and rad/s here would silently give wrong dynamics.")])

story += explain_block(5, "Run the closed loop for T_END seconds and record speed and voltage at every step.",
    [("def simulate(kp, ki, kd", "Gains, setpoint, optional disturbance time and voltage limit."),
     ("n = int(T_END / DT)", "Number of steps: 3.0 / 0.001 = 3 000."),
     ("t = np.arange(n) * DT", "Time axis 0, 0.001, …, 2.999 s."),
     ("w = np.zeros(n)", "Pre-allocated speed history."),
     ("u = np.zeros(n)", "Pre-allocated voltage history."),
     ("state = np.zeros(2)", "Motor starts at rest: w = 0, i = 0."),
     ("ctrl = PID(kp, ki, kd, DT, u_max)", "A fresh controller (integral = 0) for this run."),
     ("for k in range(n)", "The time loop (Figure 6.1)."),
     ("load = 0.05 if", "Conditional expression: load torque 0.05 N·m after `disturbance_time`, else 0."),
     ("u[k] = ctrl.update(setpoint - state[0])", "Measure speed, compute error, get the voltage."),
     ("state = motor_step(state, u[k], load)", "Apply the voltage to the motor for one step."),
     ("w[k] = state[0]", "Record the new speed."),
     ("return t, w, u", "Three arrays returned together (a tuple).")],
    boxes=[("py", "`x if condition else y` is a one-line `if`. `return t, w, u` returns a tuple, unpacked by the caller "
                  "with `t, w, u = simulate(...)`."),
           ("idea", "Controller and plant alternate exactly like in a real digital control system: sample → compute "
                    "→ actuate → wait DT.")])

story += explain_block(6, "Turn a speed curve into four numbers that describe its quality.",
    [("t10 = t[np.argmax(y >= 0.1 * setpoint)]", "`y >= 0.1` is a boolean array; `argmax` finds the first True: time of reaching 10 %."),
     ("t90 = t[np.argmax(y >= 0.9 * setpoint)]", "Same for 90 %."),
     ("rise = t90 - t10 if", "Rise time, or NaN (“not a number”) if 90 % is never reached."),
     ("except ValueError", "Safety net; not triggered in these runs."),
     ("overshoot = max(0.0", "Peak above the setpoint in %, never negative."),
     ("outside = np.where(np.abs(y - setpoint) > 0.02", "Indices where the speed is outside the ±2 % band."),
     ("settling = t[outside[-1]]", "Settling time = last time outside the band; NaN if still outside at the end; 0 if never outside."),
     ("ss_error = setpoint - y[-1]", "Error at the last sample (t = 3 s) ≈ steady-state error."),
     ("return dict(rise=rise", "All four metrics in a dictionary.")],
    boxes=[("warn", ["Overshoot is measured relative to the **setpoint**, not to the final value. The P-only response "
                     f"peaks at about 1.0 and settles at {w_ss_theory:.2f}: it overshoots its own final value by ~10 %, "
                     "but the metric reports 0 %. Keep this definition in mind when reading Table 7.1.",
                     "If the response never enters the ±2 % band (P only), the settling time is NaN and is printed as `nan`."]),
           ("py", "`np.where(condition)[0]` returns the indices where the condition is true; `outside[-1]` is the last one.")])

story += explain_block(7, "Experiment 1: simulate P, PI and PID with the same Kp, print the metrics and plot the three step responses.",
    [('if __name__ == "__main__"', "The main program starts here."),
     ('tunings = {"P only": (100, 0, 0)', "Dictionary name → (Kp, Ki, Kd)."),
     ("for name, (kp, ki, kd) in tunings.items()", "Loop over the dictionary, unpacking each tuple of gains."),
     ("t, w, u = simulate(kp, ki, kd)", "One 3-second closed-loop run."),
     ("m = step_metrics(t, w)", "Four quality numbers."),
     ('print(f"{name:7s}', "Print them (these lines are quoted in Chapter 7)."),
     ("plt.plot(t, w, label=name)", "Add the curve to the figure."),
     ('plt.savefig("step_responses.png"', "Save the figure to a file, then show it.")])
story += explain_block(8, "Experiment 2: the same three controllers, but a load torque of 0.05 N·m is suddenly applied at t = 1.5 s.",
    [("t, w, u = simulate(kp, ki, kd, disturbance_time=1.5)", "Only change: the disturbance time."),
     ('plt.axvline(1.5', "Red dashed line marking the moment the load appears.")])
story += explain_block(9, "Experiment 3: keep Ki = 200, Kd = 10 and sweep Kp from 20 to 400; plot overshoot and settling time.",
    [("kps = [20, 50, 100, 200, 400]", "The five values of Kp tested."),
     ("results = [step_metrics(*simulate(kp, 200, 10)[:2])", "List comprehension: for each Kp simulate, keep (t, w) with `[:2]`, unpack them with `*` into `step_metrics`."),
     ("fig, ax = plt.subplots(1, 2", "Two plots side by side."),
     ('ax[0].plot(kps, [r["overshoot"]', "Overshoot vs Kp."),
     ('ax[1].plot(kps, [r["settling"]', "Settling time vs Kp (NaN points are not drawn)."),
     ('print(f"Kp={kp:4d}', "Print the sweep table.")],
    boxes=[("py", "`f(*args)` unpacks a tuple into separate arguments: `step_metrics(*(t, w))` = `step_metrics(t, w)`.")])

# ================================================================== 5 control panel
story += chapter(5, "The Control Panel", "every variable, what it means, and what changing it does")
story += table([["Variable", "Meaning", "Default", "Range", "Effect of increasing it"],
                ["`J`", "rotor inertia [kg·m²]", "0.01", "0.001–1", "slower, more sluggish response; more overshoot for the same gains"],
                ["`b`", "viscous friction [N·m·s]", "0.1", "0–1", "more damping; larger P-only steady-state error (term R·b/K)"],
                ["`K`", "motor constant [N·m/A]", "0.01", "0.005–0.1", "more torque per amp and more back-EMF; changes loop gain"],
                ["`R`", "armature resistance [Ω]", "1.0", "0.1–10", "less current per volt: weaker drive, larger P-only error"],
                ["`L`", "armature inductance [H]", "0.5", "0.001–1", "slower current build-up (time constant L/R)"],
                ["`DT`", "time step [s]", "0.001", "1e-4–0.01", "less accurate/stable integration, coarser derivative"],
                ["`T_END`", "simulated time [s]", "3.0", "1–20", "longer runs; settling can be observed for slow tunings"],
                ["`V_MAX`", "supply limit [V]", "24", "5–100", "faster start (less saturation); more aggressive control possible"],
                ["`kp`", "proportional gain", "100", "10–500", "faster, smaller P-only error; with I: less overshoot here (Exp. 3)"],
                ["`ki`", "integral gain", "200", "0–1000", "removes steady-state error faster; too large → overshoot/oscillation"],
                ["`kd`", "derivative gain", "10", "0–50", "more damping (less overshoot), slower rise, bigger derivative kick"],
                ["`setpoint`", "wanted speed [rad/s]", "1.0", "any", "larger steps saturate the supply longer"],
                ["`disturbance_time`", "load step time [s]", "None", "0–T_END", "when the 0.05 N·m load appears"]],
               [2.6 * cm, 3.6 * cm, 1.5 * cm, 2.1 * cm, PAGE_W - 9.8 * cm], font_size=8)
story += section("5.2  The big trade-offs")
story += table([["If you want…", "turn this knob", "and you pay with…"],
                ["zero steady-state error", "add `ki`", "possible overshoot, windup risk"],
                ["less overshoot", "add `kd` or (here) raise `kp`", "slower rise / bigger voltage kick, noise sensitivity"],
                ["faster response", "raise `V_MAX` or the gains", "bigger actuator, more stress, less margin"],
                ["more accurate simulation", "smaller `DT`", "longer run time"]],
               [4.6 * cm, 5 * cm, PAGE_W - 9.6 * cm])

# ================================================================== 6 simulation
story += chapter(6, "How the Simulation Works", "from one time step to a response curve")
story += figure("build/diag/loop.png", 1.0, "Figure 6.1 – The time loop inside `simulate()`.")
story += para("The simulation is a **time-stepping** loop: 3 000 steps of 1 ms. In each step the controller reads the "
              "speed, computes a voltage, and the motor equations are advanced by one Euler step. No randomness is "
              "involved, so every run gives exactly the same curve (a **deterministic** simulation).")
story += box("idea", ["**Is DT small enough?** The fastest motor time constant is 0.1 s = 100×DT, so the Euler error is "
                      "small. A quick check you can do yourself: halve `DT` and verify that the metrics barely change.",
                      f"**Run time:** the whole program (11 simulations) took {RUN['seconds']} s here; a pure-Python loop of "
                      "3 000 steps is fast enough, no vectorisation needed."])
story += box("res", f"**Validation against theory:** Eq. (3.6) predicts a P-only steady state of {w_ss_theory:.4f} rad/s "
                    f"(error {1 - w_ss_theory:.4f}); the simulation gives an error of {M['P only']['ss']:.4f}. With the load, "
                    f"the theory gives {w_dist_theory:.4f} rad/s and the simulation ends at {w_p[-1]:.4f} rad/s. "
                    "The motor model and the integration are correct.")

# ================================================================== 7 results
story += chapter(7, "Experiments and Results", "running the program and reading every figure")
story += section("7.1  Experiment 1: P vs PI vs PID")
story += figure(f"{FIG}/step_responses.png", 0.82, "Figure 7.1 – Step responses of the motor speed (setpoint 1 rad/s).")
rows = [["Controller", "Kp, Ki, Kd", "Rise time", "Overshoot", "Settling (2 %)", "Steady-state error"]]
for n, g in [("P only", "100, 0, 0"), ("PI", "100, 200, 0"), ("PID", "100, 200, 10")]:
    m = M[n]
    rows.append([n, g, f"{m['rise']:.3f} s", f"{m['ov']:.1f} %", "never" if m["st"] != m["st"] else f"{m['st']:.3f} s",
                 f"{m['ss']:.4f}"])
story += table(rows, [2.3 * cm, 2.6 * cm, 2.2 * cm, 2.2 * cm, 2.8 * cm, PAGE_W - 12.1 * cm])
story += box("res", [f"**P only** settles at {1 - M['P only']['ss']:.3f} rad/s: a {100 * M['P only']['ss']:.1f} % error "
                     "that never disappears (Eq. 3.6) — so it never enters the ±2 % band.",
                     f"**PI** removes the error ({M['PI']['ss']:.4f} at 3 s) thanks to the integral, with a small "
                     f"{M['PI']['ov']:.1f} % overshoot and an oscillation that settles in {M['PI']['st']:.2f} s.",
                     f"**PID** is the smoothest: the D term damps the oscillation (settling {M['PID']['st']:.2f} s) at the cost "
                     f"of a slightly longer rise time ({M['PID']['rise']:.2f} s vs {M['PI']['rise']:.2f} s).",
                     "The first ~0.3 s are almost identical for all three: the voltage is saturated at 24 V, so the "
                     "motor accelerates as fast as the supply allows whatever the gains."])
story += section("7.2  Experiment 2: disturbance rejection", need=12 * cm)
story += figure(f"{FIG}/auto_01.png", 0.82, "Figure 7.2 – A 0.05 N·m load torque is applied at t = 1.5 s.")
story += table([["Controller", "lowest speed after the load", "final speed (t = 3 s)"]] +
               [[n, f"{dip[n]:.3f} rad/s", f"{pm.simulate(*g, disturbance_time=1.5)[1][-1]:.3f} rad/s"] for n, g in
                {"P only": (100, 0, 0), "PI": (100, 200, 0), "PID": (100, 200, 10)}.items()],
               [3.5 * cm, 6.5 * cm, PAGE_W - 10 * cm])
story += box("res", [f"With **P only** the speed drops to a new, lower level ({w_p[-1]:.3f} rad/s, matching Eq. (3.6)): "
                     "a proportional controller needs a larger error to produce the extra torque.",
                     "**PI and PID** bring the speed back to 1 rad/s: the integral grows until it supplies the extra voltage "
                     "the load requires. The D term reduces the dip and the oscillation.",
                     "This is the main reason almost every industrial controller has an I term."])
story += section("7.3  Experiment 3: sweeping Kp (Ki = 200, Kd = 10)", need=12 * cm)
story += figure(f"{FIG}/auto_02.png", 0.95, "Figure 7.3 – Overshoot (left) and settling time (right) versus Kp.")
story += table([["Kp", "overshoot", "settling time"]] + [[str(k), f"{o:.1f} %", "never (within 3 s)" if s != s else f"{s:.3f} s"]
                                                         for k, o, s in SWEEP], [3 * cm, 4 * cm, PAGE_W - 7 * cm])
story += box("res", ["Counter-intuitive at first: here **more Kp means less overshoot**. With Ki fixed at 200, a small Kp "
                     "leaves the integral in charge, and integral action alone is oscillatory (it keeps pushing until the "
                     "error changes sign). A larger Kp reacts earlier, so the integral accumulates less.",
                     "Settling time falls from ~2 s to ~0.7 s as Kp grows. In a real system Kp cannot grow forever: sensor "
                     "noise is amplified by Kp and the actuator saturates more — effects this ideal simulation does not include."])

# ================================================================== 8-10
story += chapter(8, "Summary", "what the simulation teaches")
story += bullets(["**Feedback works:** measuring the speed and reacting to the error makes the motor follow the setpoint and resist loads.",
                  "**P alone leaves an error** whose size is predicted exactly by Eq. (3.6); **I removes it**; **D damps** the response.",
                  "**Saturation shapes the start** of every response; anti-windup keeps the integral sensible while saturated.",
                  "**Gains interact:** the effect of Kp depends on Ki and Kd (Experiment 3) — tuning is a trade-off, not a single knob."])
story += box("note", "All conclusions come from an ideal, noise-free simulation with DT = 1 ms and a 24 V supply limit.", title="SCOPE")
story += chapter(9, "Hands-On Exercises", "predict first, then run and check")
ex = [("Remove the voltage limit", "Call `simulate(100, 200, 10, u_max=None)` and look at `u`.",
       "Rise time drops from 0.33 s to 0.13 s and settling to 0.25 s — but the first voltage sample is about 10 100 V "
       "(the derivative kick), physically impossible for this motor."),
      ("Heavier rotor", "Set `J = 0.05` and re-run Experiment 1.",
       "PI overshoot grows from 1.0 % to 8.1 % and settling to 2.9 s; PID gives 4.9 % and 1.6 s: the gains need retuning."),
      ("Check the time step", "Set `DT = 1e-4` (and keep everything else).",
       "PID metrics change only in the 3rd decimal (rise 0.330 s, overshoot 2.64 %): DT = 1 ms was accurate enough."),
      ("Coarser time step", "Set `DT = 0.02` (20× larger).",
       "Surprisingly small change (overshoot 2.4 % instead of 2.6 %): the motor time constants (0.1 s and 0.5 s) are still "
       "5–25× larger than DT. Keep increasing DT to find where the simulation breaks down."),
      ("Tune for no overshoot", "Find Kp, Ki, Kd that give 0 % overshoot and settling below 0.8 s.",
       "Experiment 3 points the way: Kp = 400 with Ki = 200, Kd = 10 already gives 0.1 % and 0.72 s."),
      ("Switch anti-windup off", "Comment out the anti-windup line (line " + str(find_line("self.integral -= error")) +
       ") and run `simulate(100, 1000, 0)`.",
       "Overshoot jumps from 7.2 % (with anti-windup) to about 70 %: the integral winds up while the voltage is saturated."),
      ("Noisy sensor", "Add `+ np.random.normal(0, 0.01)` to the measured speed in `simulate`.",
       "The D term amplifies the noise (10 × 0.01 / 0.001 = 100 V of jitter), so the voltage chatters between the limits.")]
for i, (title, task, expect) in enumerate(ex, 1):
    story += box("try", [f"**Task:** {task}", f"**What you should see:** {expect}"], title=f"EXERCISE {i}: {title.upper()}")
story += chapter(10, "Glossary")
story += table([["Term", "Meaning"],
                ["Anti-windup", "Stopping the integral from growing while the actuator is saturated."],
                ["Back-EMF", "Voltage generated by the spinning motor, K·ω, opposing the supply."],
                ["Closed loop", "Control that uses the measured output (feedback)."],
                ["Derivative kick", "Huge D output when the setpoint (and hence the error) jumps."],
                ["Euler method", "Numerical integration: new = old + step × slope."],
                ["Overshoot", "How far the response goes beyond the setpoint, in %."],
                ["PID", "Proportional-Integral-Derivative controller."],
                ["Plant", "The system being controlled (here the motor)."],
                ["Saturation", "The actuator output reaching its physical limit (±24 V)."],
                ["Setpoint", "The desired value of the controlled variable."],
                ["Settling time", "Time after which the response stays within ±2 % of the setpoint."],
                ["Steady-state error", "Error remaining after the transients have died out."]], [3.6 * cm, PAGE_W - 3.6 * cm])

build_pdf(story, "DC_Motor_PID_Guide.pdf")
