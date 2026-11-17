# ==== [BLOCK 0] Imports ====
"""DC motor speed control with a discrete PID controller.
Simulates the closed loop, measures step-response metrics and compares controller tunings."""
import numpy as np
import matplotlib.pyplot as plt

# ==== [BLOCK 1] Motor parameters (the physical plant) ====
# motor parameters (small DC motor)
J = 0.01      # rotor inertia [kg m^2]
b = 0.1       # viscous friction [N m s]
K = 0.01      # motor constant [N m / A] = back-emf constant [V s]
R = 1.0       # armature resistance [ohm]
L = 0.5       # armature inductance [H]

# ==== [BLOCK 2] Simulation settings ====
DT = 1e-3     # simulation time step [s]
T_END = 3.0   # simulated time [s]
V_MAX = 24.0  # supply voltage limit [V]


# ==== [BLOCK 3] The PID controller (class with memory) ====
class PID:
    """Discrete PID controller with output saturation and anti-windup."""

    def __init__(self, kp, ki, kd, dt, u_max=None):
        self.kp, self.ki, self.kd, self.dt = kp, ki, kd, dt
        self.u_max = u_max
        self.integral = 0.0
        self.prev_error = 0.0

    def update(self, error):
        self.integral += error * self.dt
        derivative = (error - self.prev_error) / self.dt
        self.prev_error = error
        u = self.kp * error + self.ki * self.integral + self.kd * derivative
        if self.u_max is not None and abs(u) > self.u_max:
            self.integral -= error * self.dt          # anti-windup: undo the last integration
            u = np.clip(u, -self.u_max, self.u_max)
        return u


# ==== [BLOCK 4] Motor model: one Euler step ====
def motor_step(state, v, load_torque=0.0):
    """One Euler step of the motor equations. state = [speed w, current i]."""
    w, i = state
    dw = (K * i - b * w - load_torque) / J
    di = (v - R * i - K * w) / L
    return np.array([w + DT * dw, i + DT * di])


# ==== [BLOCK 5] Closed-loop simulation over time ====
def simulate(kp, ki, kd, setpoint=1.0, disturbance_time=None, u_max=V_MAX):
    n = int(T_END / DT)
    t = np.arange(n) * DT
    w = np.zeros(n)
    u = np.zeros(n)
    state = np.zeros(2)
    ctrl = PID(kp, ki, kd, DT, u_max)
    for k in range(n):
        load = 0.05 if (disturbance_time is not None and t[k] >= disturbance_time) else 0.0
        u[k] = ctrl.update(setpoint - state[0])
        state = motor_step(state, u[k], load)
        w[k] = state[0]
    return t, w, u


# ==== [BLOCK 6] Step-response metrics ====
def step_metrics(t, y, setpoint=1.0):
    """Rise time (10-90 %), overshoot [%], 2 % settling time and steady-state error."""
    try:
        t10 = t[np.argmax(y >= 0.1 * setpoint)]
        t90 = t[np.argmax(y >= 0.9 * setpoint)]
        rise = t90 - t10 if y.max() >= 0.9 * setpoint else np.nan
    except ValueError:
        rise = np.nan
    overshoot = max(0.0, (y.max() - setpoint) / setpoint * 100)
    outside = np.where(np.abs(y - setpoint) > 0.02 * setpoint)[0]
    settling = t[outside[-1]] if len(outside) and outside[-1] < len(t) - 1 else (0.0 if not len(outside) else np.nan)
    ss_error = setpoint - y[-1]
    return dict(rise=rise, overshoot=overshoot, settling=settling, ss_error=ss_error)


# ==== [BLOCK 7] Experiment 1: P vs PI vs PID step responses ====
if __name__ == "__main__":
    tunings = {"P only": (100, 0, 0), "PI": (100, 200, 0), "PID": (100, 200, 10)}
    plt.figure(figsize=(8, 4.5))
    for name, (kp, ki, kd) in tunings.items():
        t, w, u = simulate(kp, ki, kd)
        m = step_metrics(t, w)
        print(f"{name:7s} rise={m['rise']:.3f}s overshoot={m['overshoot']:.1f}% "
              f"settling={m['settling']:.3f}s ss_error={m['ss_error']:.4f}")
        plt.plot(t, w, label=name)
    plt.axhline(1.0, color="k", ls=":", lw=1)
    plt.xlabel("time [s]"); plt.ylabel("speed [rad/s]"); plt.title("Step response of the motor speed")
    plt.legend(); plt.grid(True)
    plt.savefig("step_responses.png", dpi=120)
    plt.show()

    # ==== [BLOCK 8] Experiment 2: disturbance rejection ====
    # disturbance rejection: a load torque appears at t = 1.5 s
    plt.figure(figsize=(8, 4.5))
    for name, (kp, ki, kd) in tunings.items():
        t, w, u = simulate(kp, ki, kd, disturbance_time=1.5)
        plt.plot(t, w, label=name)
    plt.axvline(1.5, color="r", ls="--", lw=1, label="load applied")
    plt.xlabel("time [s]"); plt.ylabel("speed [rad/s]"); plt.title("Disturbance rejection")
    plt.legend(); plt.grid(True)
    plt.show()

    # ==== [BLOCK 9] Experiment 3: sweeping the proportional gain Kp ====
    # effect of the proportional gain
    kps = [20, 50, 100, 200, 400]
    results = [step_metrics(*simulate(kp, 200, 10)[:2]) for kp in kps]
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(kps, [r["overshoot"] for r in results], "o-")
    ax[0].set_xlabel("Kp"); ax[0].set_ylabel("overshoot [%]"); ax[0].grid(True)
    ax[1].plot(kps, [r["settling"] for r in results], "s-", color="C1")
    ax[1].set_xlabel("Kp"); ax[1].set_ylabel("settling time [s]"); ax[1].grid(True)
    fig.suptitle("PID with Ki=200, Kd=10: sweeping Kp")
    plt.show()
    for kp, r in zip(kps, results):
        print(f"Kp={kp:4d}: overshoot={r['overshoot']:.1f}%  settling={r['settling']:.3f}s")
