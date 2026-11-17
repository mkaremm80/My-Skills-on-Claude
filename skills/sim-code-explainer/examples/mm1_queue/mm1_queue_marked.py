# ==== [BLOCK 0] Imports and settings ====
"""Event-driven simulation of an M/M/1 queue (one server, Poisson arrivals, exponential service).
Compares the simulated waiting times with queueing theory for several loads."""
import heapq
from dataclasses import dataclass, field
import numpy as np
import matplotlib.pyplot as plt

SEED = 7
N_CUSTOMERS = 50_000     # customers per simulation run
MU = 1.0                 # service rate [customers per second]


# ==== [BLOCK 1] The Event record (what happens, and when) ====
@dataclass(order=True)
class Event:
    time: float
    kind: str = field(compare=False)          # "arrival" or "departure"
    customer: int = field(compare=False)


# ==== [BLOCK 2] Random arrivals and service times ====
def simulate_mm1(lam, mu, n_customers, rng):
    """Return arrival, service-start and departure times of every customer."""
    arrivals = np.cumsum(rng.exponential(1 / lam, n_customers))
    services = rng.exponential(1 / mu, n_customers)
    start = np.zeros(n_customers)
    depart = np.zeros(n_customers)
    # ==== [BLOCK 3] The event loop: arrivals and departures ====
    events = [Event(arrivals[0], "arrival", 0)]
    queue = []                                # customers waiting (FIFO)
    busy = False
    next_customer = 1
    while events:
        ev = heapq.heappop(events)            # earliest event first
        if ev.kind == "arrival":
            if next_customer < n_customers:
                heapq.heappush(events, Event(arrivals[next_customer], "arrival", next_customer))
                next_customer += 1
            if busy:
                queue.append(ev.customer)
            else:
                busy = True
                start[ev.customer] = ev.time
                depart[ev.customer] = ev.time + services[ev.customer]
                heapq.heappush(events, Event(depart[ev.customer], "departure", ev.customer))
        else:                                 # departure: serve the next waiting customer
            if queue:
                c = queue.pop(0)
                start[c] = ev.time
                depart[c] = ev.time + services[c]
                heapq.heappush(events, Event(depart[c], "departure", c))
            else:
                busy = False
    return arrivals, start, depart


# ==== [BLOCK 4] Queueing theory formulas ====
def theory_mm1(lam, mu):
    rho = lam / mu
    return dict(rho=rho, Wq=rho / (mu - lam), W=1 / (mu - lam), Lq=rho ** 2 / (1 - rho))


# ==== [BLOCK 5] Experiment 1: waiting time versus load ====
if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    loads = [0.3, 0.5, 0.7, 0.8, 0.9, 0.95]
    sim_wq, th_wq = [], []
    for rho in loads:
        lam = rho * MU
        a, s, d = simulate_mm1(lam, MU, N_CUSTOMERS, rng)
        wq = np.mean(s - a)
        sim_wq.append(wq)
        th_wq.append(theory_mm1(lam, MU)["Wq"])
        print(f"rho={rho:.2f}  Wq sim={wq:7.3f} s  theory={th_wq[-1]:7.3f} s  error={100*(wq/th_wq[-1]-1):+5.1f}%")

    plt.figure(figsize=(7, 4.5))
    plt.plot(loads, th_wq, "k-", label="theory  Wq = rho / (mu - lambda)")
    plt.plot(loads, sim_wq, "o", ms=7, label="simulation")
    plt.xlabel("load rho = lambda / mu"); plt.ylabel("mean waiting time in queue [s]")
    plt.title("M/M/1 queue: waiting time explodes as rho -> 1"); plt.legend(); plt.grid(True)
    plt.show()

    # ==== [BLOCK 6] Experiment 2: distribution of the time in the system ====
    # distribution of the time spent in the system at rho = 0.8
    a, s, d = simulate_mm1(0.8, MU, N_CUSTOMERS, rng)
    sojourn = d - a
    x = np.linspace(0, 30, 200)
    plt.figure(figsize=(7, 4.5))
    plt.hist(sojourn, bins=80, density=True, alpha=0.6, label="simulation")
    plt.plot(x, (MU - 0.8) * np.exp(-(MU - 0.8) * x), "r-", lw=2, label="theory: exponential(mu - lambda)")
    plt.xlabel("time in system [s]"); plt.ylabel("probability density"); plt.xlim(0, 30)
    plt.title("Time in system at rho = 0.8"); plt.legend(); plt.grid(True)
    plt.show()
    print(f"rho=0.80 mean sojourn sim={sojourn.mean():.3f} s theory={theory_mm1(0.8, MU)['W']:.3f} s; "
          f"95th percentile sim={np.percentile(sojourn, 95):.2f} s theory={np.log(20) / (MU - 0.8):.2f} s")
