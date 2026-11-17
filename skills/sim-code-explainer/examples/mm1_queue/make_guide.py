import json
import os
import re
import sys
import importlib.util

SKILL = os.environ.get("SCE_SKILL_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from guide_lib import *                      # noqa
from diagram_kit import pipeline, loop_flow  # noqa
import numpy as np

CODE_FILE = "mm1_queue_marked.py"
RUN_DIR = "run_out"
FIG = f"{RUN_DIR}/figures"
ANALYSIS = json.load(open("mm1_queue.analysis.json"))
RUN = json.load(open(f"{RUN_DIR}/run_report.json"))
STDOUT = open(f"{RUN_DIR}/stdout.txt").read()
load_source(CODE_FILE)
B = SRC["blocks"]

rows_run = [(float(r), float(s), float(t), float(e)) for r, s, t, e in
            re.findall(r"rho=([\d.]+)\s+Wq sim=\s*([\d.]+) s\s+theory=\s*([\d.]+) s\s+error=\s*([+-][\d.]+)%", STDOUT)]
soj = re.search(r"mean sojourn sim=([\d.]+) s theory=([\d.]+) s; 95th percentile sim=([\d.]+) s theory=([\d.]+) s", STDOUT).groups()

# verification: spread of the estimate at rho = 0.9 over 5 seeds (uses the program's own function)
spec = importlib.util.spec_from_file_location("q", CODE_FILE)
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
spread = []
for seed in range(5):
    a, s, d = q.simulate_mm1(0.9, 1.0, q.N_CUSTOMERS, np.random.default_rng(100 + seed))
    spread.append(np.mean(s - a))

os.makedirs("build/diag", exist_ok=True)
pipeline([("RANDOM INPUTS", [("Inter-arrival\ntimes ~ Exp(λ)", "rng.exponential"), ("Service\ntimes ~ Exp(μ)", "rng.exponential")]),
          ("EVENT-DRIVEN SIMULATION", [("Event list\n(heap)", "heapq"), ("Arrival /\ndeparture logic", "simulate_mm1"), ("FIFO queue", "")]),
          ("MEASUREMENT", [("Waiting times\nWq = start - arrival", ""), ("Compare with\ntheory", "theory_mm1")])],
         "build/diag/pipeline.png")
loop_flow(["pop the earliest event", "arrival? schedule next arrival", "server busy? join queue : start service",
           "departure? serve next in queue", "event list empty?", "return all times"], "build/diag/loop.png",
          back=(4, 0), back_label="NO -> next event")

set_meta(title="M/M/1 Queue Simulation",
         subtitle="An event-driven simulation in Python explained from zero,\nchecked against queueing theory.",
         tags=["Poisson arrivals", "Exponential service", "Event list (heap)", "Waiting time", "Little / M/M/1 theory"],
         cover_image="build/diag/pipeline.png",
         companion="Companion files: mm1_queue_marked.py  •  mm1_queue.ipynb (Google Colab)  •  figures/")

story = start_story()
story += scope_page(
    included=["Single-server FIFO queue with Poisson arrivals and exponential service (M/M/1)",
              "Event-driven simulation with a priority queue", "Mean waiting time vs load, distribution of time in system",
              "Comparison with closed-form M/M/1 theory"],
    excluded=["Several servers, priorities, finite buffers", "Warm-up period removal and confidence intervals",
              "Other distributions (M/G/1, G/G/1)", "Real traffic data"],
    statement="This report explains a Python program that simulates customers arriving at a single server, waiting in a "
              "queue and being served, and checks the simulated waiting times against **queueing theory**.",
    note="Each value comes from **one run of 50 000 customers** without warm-up removal. Near full load (ρ ≥ 0.9) "
         "a single run is noisy: the estimate can be 10 % or more away from the theory (see Chapter 6).")
story += legend_page()
story += toc_page()

story += python_chapter(ANALYSIS["feature_ids"], num=1, uses={
    "dataclasses": f"`@dataclass(order=True) class Event` (line {find_line('class Event')}) describes one event; `order=True` lets the heap sort events by time.",
    "random": "`rng.exponential(1 / lam, n)` draws all inter-arrival times at once.",
    "containers": f"`queue = []` (line {find_line('queue = []')}) is the waiting line; `append` adds at the back, `pop(0)` removes the front.",
})
story += section("1.x  The heapq module: an always-sorted to-do list")
story += para("A **heap** is a list kept in a special order so that the smallest element can be taken out quickly. "
              "`heapq.heappush(h, x)` inserts, `heapq.heappop(h)` removes and returns the smallest. Event simulators use "
              "it as the **event list**: the next event to happen is always the one with the smallest time.")
story += snippet('''
import heapq
h = []
heapq.heappush(h, 5.0); heapq.heappush(h, 1.5); heapq.heappush(h, 3.2)
heapq.heappop(h)     # 1.5  (always the smallest)
heapq.heappop(h)     # 3.2''')

story += chapter(2, "The Ideas Behind Queues", "why waiting lines behave so non-linearly")
story += section("2.1  Customers, servers and randomness")
story += para("A queue forms whenever customers (packets, people, jobs) arrive at a server faster than it can serve them "
              "— even if only *occasionally* faster. Arrivals are random: the program uses a **Poisson process** "
              "(independent, exponential gaps with mean 1/λ) and exponential service times (mean 1/μ). "
              "In Kendall's notation this is the **M/M/1** queue: Markovian arrivals / Markovian service / 1 server.")
story += section("2.2  The load ρ")
story += para("The single most important number is the **load** ρ = λ/μ: the fraction of time the server is busy. "
              "ρ must stay below 1, otherwise the queue grows forever.")
story += box("idea", "Randomness is what creates waiting. A perfectly regular server at 90 % load would never queue anyone; "
                     "a random one makes the average customer wait 9 service times (Eq. 3.2).")
story += section("2.3  Event-driven simulation")
story += para("Nothing changes in a queue between two events (an arrival or a departure). So instead of advancing time in small "
              "fixed steps, the simulator **jumps from event to event** — exact and very fast.")

story += chapter(3, "The System Model", "the equations the simulation is checked against")
story += figure("build/diag/pipeline.png", 1.0, "Figure 3.1 – Structure of the program.")
story += eq_box([r"$\rho = \frac{\lambda}{\mu} < 1$"], "(3.1)")
story += eq_box([r"$W_q = \frac{\rho}{\mu - \lambda},\qquad W = W_q + \frac{1}{\mu} = \frac{1}{\mu-\lambda},\qquad L_q = \frac{\rho^2}{1-\rho}$"], "(3.2)")
story += para("W<sub>q</sub> = mean waiting time in the queue, W = mean time in the system (waiting + service), "
              "L<sub>q</sub> = mean number of customers waiting. For M/M/1 the time in the system is itself exponential:")
story += eq_box([r"$P(T > x) = e^{-(\mu-\lambda)x}\quad\Rightarrow\quad x_{95\%} = \frac{\ln 20}{\mu - \lambda}$"], "(3.3)")
story += table([["Eq.", "What", "Function", "Lines"],
                ["(3.1)–(3.2)", "theory", "`theory_mm1`", f"{B[4]['start']}–{B[4]['end']}"],
                ["–", "event-driven model of the queue", "`simulate_mm1`", f"{B[2]['start']}–{B[3]['end']}"],
                ["(3.3)", "sojourn-time distribution", "main, Experiment 2", f"{B[6]['start']}–{B[6]['end']}"]],
               [2.6 * cm, 5.4 * cm, 4.4 * cm, PAGE_W - 12.4 * cm])

story += chapter(4, "The Code, Block by Block", "every group of related lines: what, why, and what if")
story += explain_block(0, "Load the libraries and set the three global parameters.",
    [("import heapq", "Priority queue used as the event list."),
     ("from dataclasses import dataclass, field", "Tools to declare the `Event` record compactly."),
     ("SEED = 7", "Seed of the random generator: same results every run."),
     ("N_CUSTOMERS = 50_000", "Customers per run. `_` is just a digit separator (50 000)."),
     ("MU = 1.0", "Service rate: 1 customer per second on average (mean service 1 s).")],
    boxes=[("what", "More customers → more precise averages (error ~ 1/√N, but much worse near ρ = 1), longer run.")])
story += explain_block(1, "A small record type for one event: when it happens, what it is, and which customer.",
    [("@dataclass(order=True)", "Generate `__init__` and comparison operators automatically."),
     ("time: float", "The only field used for ordering: events compare by time."),
     ('kind: str = field(compare=False)', "\"arrival\" or \"departure\", ignored when comparing."),
     ("customer: int = field(compare=False)", "Index of the customer concerned.")],
    boxes=[("idea", "The heap needs to know which event comes first; `order=True` + `compare=False` makes “first” mean "
                    "“smallest time”.")])
story += explain_block(2, "Draw all random times in advance and prepare the result arrays.",
    [("def simulate_mm1", "Inputs: arrival rate λ, service rate μ, number of customers, random generator."),
     ("arrivals = np.cumsum(rng.exponential(1 / lam", "Exponential gaps with mean 1/λ; the running sum gives the arrival instants."),
     ("services = rng.exponential(1 / mu", "Each customer's service duration."),
     ("start = np.zeros(n_customers)", "When each customer's service starts (filled by the loop)."),
     ("depart = np.zeros(n_customers)", "When each customer leaves.")],
    boxes=[("model", "Exponential gaps = Poisson arrivals: the “M” in M/M/1."),
           ("py", "`np.cumsum([2, 1, 3])` = `[2, 3, 6]` (running total).")])
story += explain_block(3, "Process events in time order until none are left; this is the queue itself.",
    [('events = [Event(arrivals[0], "arrival", 0)]', "Start with the first arrival in the event list."),
     ("queue = []", "Customers waiting, in arrival order."),
     ("busy = False", "Is the server serving someone?"),
     ("while events", "Loop as long as something is scheduled."),
     ("ev = heapq.heappop(events)", "Take the earliest event: simulated time jumps to `ev.time`."),
     ('if ev.kind == "arrival"', "Arrival handling:"),
     ("heapq.heappush(events, Event(arrivals[next_customer]", "… schedule the next customer's arrival (one at a time keeps the heap small)."),
     ("queue.append(ev.customer)", "Server busy → join the back of the queue."),
     ("start[ev.customer] = ev.time", "Server free → service starts immediately: zero wait."),
     ("depart[ev.customer] = ev.time + services", "Departure time = start + service duration…"),
     ('heapq.heappush(events, Event(depart[ev.customer]', "… scheduled as a future event."),
     ("if queue:", "Departure handling: someone waiting?"),
     ("c = queue.pop(0)", "Take the first in line (FIFO)."),
     ("start[c] = ev.time", "Their service starts the moment the previous customer leaves."),
     ("busy = False", "Nobody waiting: the server becomes idle."),
     ("return arrivals, start, depart", "Waiting time of customer k is `start[k] - arrivals[k]`.")],
    boxes=[("idea", "Only two kinds of events change the state, so the whole queue fits in ~25 lines."),
           ("warn", "`list.pop(0)` shifts the whole list, so it gets slow when the queue is very long (ρ → 1). "
                    "`collections.deque.popleft()` does the same in constant time.")])
story += explain_block(4, "The closed-form M/M/1 results of Eqs. (3.1)–(3.2).",
    [("rho = lam / mu", "Load (3.1)."), ("return dict(rho=rho", "W<sub>q</sub>, W, L<sub>q</sub> of (3.2).")])
story += explain_block(5, "For six loads: simulate, measure the mean waiting time, compare with theory, plot.",
    [("rng = np.random.default_rng(SEED)", "One generator for all runs (reproducible)."),
     ("loads = [0.3, 0.5, 0.7, 0.8, 0.9, 0.95]", "The loads tested."),
     ("lam = rho * MU", "Arrival rate giving that load."),
     ("wq = np.mean(s - a)", "Mean of (service start − arrival) over 50 000 customers."),
     ('print(f"rho={rho:.2f}', "Print simulation, theory and relative error (quoted in Chapter 7).")])
story += explain_block(6, "At ρ = 0.8, compare the histogram of the time in the system with the exponential law (3.3).",
    [("sojourn = d - a", "Time in system = departure − arrival, for every customer."),
     ("plt.hist(sojourn, bins=80, density=True", "Histogram normalised to a probability density."),
     ("plt.plot(x, (MU - 0.8) * np.exp(", "Theoretical density (μ−λ)e<super>−(μ−λ)x</super>."),
     ("np.percentile(sojourn, 95)", "95 % of customers spend less than this time in the system.")])

story += chapter(5, "The Control Panel", "every variable and its effect")
story += table([["Variable", "Meaning", "Default", "Effect of increasing it"],
                ["`SEED`", "random seed", "7", "different random realisation, same statistics"],
                ["`N_CUSTOMERS`", "customers per run", "50 000", "smaller statistical error, longer run"],
                ["`MU`", "service rate [1/s]", "1.0", "faster server: all times scale down by 1/μ"],
                ["`loads`", "values of ρ tested", "0.3–0.95", "waiting grows like ρ/(1−ρ): explodes near 1"],
                ["`lam`", "arrival rate λ = ρμ", "–", "higher load, longer queues; λ ≥ μ is unstable"]],
               [3 * cm, 4 * cm, 2.2 * cm, PAGE_W - 9.2 * cm])

story += chapter(6, "How the Simulation Works", "events, not time steps")
story += figure("build/diag/loop.png", 1.0, "Figure 6.1 – The event loop of `simulate_mm1`.")
story += para(f"The full run (7 simulations, 350 000 customers) took {RUN['seconds']} s. Each run is one long sample "
              "path; averages over it estimate the steady-state means.")
story += box("warn", [f"**How reliable is one run near full load?** Five extra runs at ρ = 0.9 with different seeds gave "
                      f"W<sub>q</sub> = {', '.join(f'{v:.1f}' for v in spread)} s (theory 9.0 s): a spread of "
                      f"{min(spread):.1f}–{max(spread):.1f} s. Near ρ = 1 consecutive waiting times are strongly "
                      "correlated, so 50 000 customers carry much less information than 50 000 independent samples.",
                      "Proper practice: discard a warm-up period, run several independent replications and report a "
                      "confidence interval (outside the scope of this program)."])

story += chapter(7, "Experiments and Results", "reading every figure")
story += section("7.1  Waiting time versus load")
story += figure(f"{FIG}/auto_01.png", 0.8, "Figure 7.1 – Mean waiting time: theory (line) and simulation (markers).")
story += table([["ρ", "simulated W<sub>q</sub>", "theory W<sub>q</sub>", "error"]] +
               [[f"{r:.2f}", f"{s:.3f} s", f"{t:.3f} s", f"{e:+.1f} %"] for r, s, t, e in rows_run],
               [2.5 * cm, 4.5 * cm, 4.5 * cm, PAGE_W - 11.5 * cm])
story += box("res", ["Simulation and Eq. (3.2) agree within a few percent up to ρ = 0.8: the event logic is correct.",
                     f"The waiting time is **not proportional** to the load: from ρ = 0.5 to 0.95 the load grows 1.9× but "
                     f"W<sub>q</sub> grows {rows_run[-1][2] / rows_run[1][2]:.0f}× (theory). Running a server close to 100 % "
                     "busy is very costly for the customers.",
                     f"At ρ = 0.9 the error is {rows_run[4][3]:+.1f} %: not a bug but statistical noise of a single correlated "
                     "run (Chapter 6)."])
story += section("7.2  Distribution of the time in the system", need=12 * cm)
story += figure(f"{FIG}/auto_02.png", 0.8, "Figure 7.2 – Histogram of the time in the system at ρ = 0.8 and the exponential law.")
story += box("res", [f"Mean time in system: simulation {soj[0]} s, theory {soj[1]} s. 95th percentile: simulation {soj[2]} s, "
                     f"theory {soj[3]} s (Eq. 3.3).",
                     "The distribution has a long tail: most customers are quick, but 5 % spend about 3× the mean. "
                     "Service-level targets are therefore usually stated as percentiles, not means."])

story += chapter(8, "Summary", "")
story += bullets(["An event-driven simulator reproduces M/M/1 theory with a few lines of Python.",
                  "Waiting explodes as ρ → 1 (W<sub>q</sub> = ρ/(μ−λ)).",
                  "Near full load single runs are noisy: use replications and confidence intervals."])
story += box("note", "Results are single runs of 50 000 customers without warm-up removal.", title="SCOPE")
story += chapter(9, "Hands-On Exercises", "predict first, then run and check")
for i, (title, task, expect) in enumerate([
        ("Seeds", "Re-run Experiment 1 with `SEED = 1`.", "Small changes at low load, larger ones at ρ ≥ 0.9."),
        ("Faster server", "Set `MU = 2.0`.", "All times halve; ρ values (and the shape of Figure 7.1) stay the same."),
        ("Overload", "Add ρ = 1.05 to `loads`.", "The theory formula gives a negative value (meaningless); the simulated wait keeps growing with N_CUSTOMERS."),
        ("deque", "Replace the list by `collections.deque` and `pop(0)` by `popleft()`.", "Identical results, faster at high load.")], 1):
    story += box("try", [f"**Task:** {task}", f"**What you should see:** {expect}"], title=f"EXERCISE {i}: {title.upper()}")
story += chapter(10, "Glossary")
story += table([["Term", "Meaning"], ["M/M/1", "Poisson arrivals, exponential service, one server."],
                ["Load ρ", "Fraction of time the server is busy, λ/μ."], ["FIFO", "First in, first out."],
                ["Event list", "Time-ordered list of future events (here a heap)."],
                ["Sojourn time", "Total time in the system: waiting + service."]], [3.6 * cm, PAGE_W - 3.6 * cm])
build_pdf(story, "MM1_Queue_Guide.pdf")
