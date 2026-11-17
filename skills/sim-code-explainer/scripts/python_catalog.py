"""Beginner explanations of Python features. code_parser.py detects which ids a program uses;
guide_lib.python_chapter() turns the detected ones into the 'Python from Zero' chapter (in ORDER).
Add entries freely: id -> dict(title, text, code, tip). Text uses guide_lib.md() markup."""

ORDER = ["basics", "strings", "containers", "dicts", "control", "comprehensions", "functions", "kwargs",
         "lambda", "classes", "dataclasses", "imports", "exceptions", "with_files", "main_guard",
         "numpy", "numpy_broadcast", "numpy_linalg", "numpy_fft", "random", "complex", "bitwise",
         "pandas", "scipy", "matplotlib", "enumerate_zip", "generators", "assert", "typing"]

CATALOG = {
    "basics": dict(
        title="Variables, numbers and comments",
        text="A **variable** is a name that stores a value. `=` means *store the value on the right into the name "
             "on the left* (it is not a mathematical equation). Everything after `#` is a **comment** that Python "
             "ignores — comments are written for humans, so read them.",
        code='''
N = 512              # an integer (int)
fc = 3.5e9           # a float in scientific notation: 3.5 x 10^9
ratio = 7 / 2        # 3.5   (/ always gives a float)
q = 7 // 2           # 3     (integer division)
r = 7 % 2            # 1     (remainder, "modulo")
p = 2 ** 10          # 1024  (power)
print(N, fc, ratio)  # show values''',
        tip=["Names are case-sensitive: `N` and `n` are different variables. UPPERCASE names are, by convention, "
             "constants (fixed parameters).", "`True` / `False` are the two boolean values; comparisons such as "
             "`a > b` or `a == b` produce them."]),
    "strings": dict(
        title="Text and f-strings",
        text="Text is written between quotes. An **f-string** (`f\"...\"`) can contain `{expressions}` that Python "
             "replaces by their values; the part after a colon controls the format.",
        code='''
name = "PID"
gain = 1.23456
print(f"{name} gain = {gain:.2f}")     # -> PID gain = 1.23
print(f"{0.000123:.1e}")               # -> 1.2e-04 (scientific)
print(f"{'left':<10}|")                # pad to 10 characters''',
        tip=None),
    "containers": dict(
        title="Lists, tuples and slicing",
        text="A **list** `[...]` is an ordered, changeable collection; a **tuple** `(...)` is the same but cannot be "
             "changed. Python counts positions from **0**.",
        code='''
v = [10, 20, 30, 40]
v[0]       # 10   first element
v[-1]      # 40   last element
v[1:3]     # [20, 30]  from index 1 up to, NOT including, 3
v.append(50)          # add at the end
len(v)     # 5
t = (2, 11)           # tuple''',
        tip=["**Index 0 is the first element**, and the end of a slice is excluded: `v[0:3]` has 3 elements. "
             "These two rules cause most beginner bugs."]),
    "dicts": dict(
        title="Dictionaries: named settings",
        text="A **dictionary** maps keys to values. Simulation programs often keep all their parameters in one "
             "dictionary so that every function can read them from one place.",
        code='''
cfg = {"Kp": 2.0, "Ki": 0.5}     # key: value
cfg["Kp"]                        # 2.0
cfg["Kd"] = 0.1                  # add a key
cfg.get("Tf", 1.0)               # value of "Tf" or 1.0 if missing
for key, value in cfg.items():
    print(key, value)''',
        tip=None),
    "control": dict(
        title="Decisions and loops: if, for, while",
        text="`if` runs code only when a condition is true; `for` repeats code for every element of a sequence; "
             "`while` repeats as long as a condition stays true. The lines that belong to them are **indented** "
             "by 4 spaces — Python has no `{ }` or `end`.",
        code='''
for k in range(3):        # k = 0, 1, 2
    if k == 0:
        print("first")
    elif k == 1:
        print("second")
    else:
        print("other")

t = 0.0
while t < 1.0:            # repeat until t reaches 1
    t += 0.25             # same as t = t + 0.25''',
        tip=["`range(n)` gives 0 … n−1; `range(a, b, step)` counts from a up to b (excluded).",
             "`break` leaves a loop immediately; `continue` jumps to the next round."]),
    "comprehensions": dict(
        title="List comprehensions",
        text="A **comprehension** builds a list (or dict) in one line: `[expression for x in sequence if condition]`.",
        code='''
squares = [k**2 for k in range(5)]              # [0, 1, 4, 9, 16]
even    = [k for k in range(10) if k % 2 == 0]  # [0, 2, 4, 6, 8]
table   = {k: k**2 for k in range(3)}           # {0: 0, 1: 1, 2: 4}''',
        tip=None),
    "functions": dict(
        title="Functions",
        text="A **function** is a named, reusable piece of code: it takes inputs (**parameters**) and **returns** an "
             "output. A simulator is usually a set of small functions that call each other.",
        code='''
def db_to_linear(x_db):              # define
    """Convert dB to a linear ratio."""  # docstring = description
    return 10 ** (x_db / 10)         # output

db_to_linear(20)                     # call -> 100.0

def step(x, dt=0.01):                # dt has a default value
    return x + dt''',
        tip=["The indented body runs only when the function is **called**.",
             "Variables created inside a function exist only inside it (local variables).",
             "A function can be defined inside another one: a private helper."]),
    "kwargs": dict(
        title="Keyword arguments and **kwargs",
        text="Arguments can be passed by name (`f(dt=0.1)`). `**kwargs` in a definition collects any named "
             "arguments into a dictionary — handy for “defaults + overrides” configuration functions. "
             "`*args` collects extra positional arguments into a tuple.",
        code='''
def make_config(**changes):
    cfg = dict(Kp=1.0, Ki=0.0)       # defaults
    cfg.update(changes)              # overrides
    return cfg

make_config(Ki=0.5)                  # {"Kp": 1.0, "Ki": 0.5}''',
        tip=None),
    "lambda": dict(
        title="Small anonymous functions: lambda",
        text="`lambda x: expression` creates a tiny function without a name, often passed to another function "
             "(e.g. a sorting key or an ODE right-hand side).",
        code='''
f = lambda t: 2 * t + 1
f(3)                                   # 7
sorted(["bb", "a", "ccc"], key=lambda s: len(s))''',
        tip=None),
    "classes": dict(
        title="Classes and objects",
        text="A **class** is a blueprint that bundles data (**attributes**) and functions that act on it "
             "(**methods**). An **object** is one instance built from the blueprint. `self` is the object itself; "
             "`__init__` runs when the object is created.",
        code='''
class Tank:
    def __init__(self, level=0.0):   # constructor
        self.level = level           # attribute

    def fill(self, q, dt):           # method
        self.level += q * dt
        return self.level

t = Tank()            # create an object
t.fill(2.0, 0.5)      # -> 1.0''',
        tip=["Use objects when something has a **state** that changes over time (a queue, a controller's "
             "integral, a battery's charge) — the state lives in the attributes."]),
    "dataclasses": dict(
        title="Dataclasses",
        text="`@dataclass` writes the `__init__` for you: just list the fields and their default values. It is a "
             "clean way to hold parameters.",
        code='''
from dataclasses import dataclass

@dataclass
class Params:
    Kp: float = 2.0
    Ki: float = 0.5

p = Params(Ki=1.0)    # p.Kp == 2.0, p.Ki == 1.0''',
        tip=None),
    "imports": dict(
        title="Modules: import",
        text="Python's power comes from **libraries**. `import numpy as np` loads NumPy under the short name `np`; "
             "`from x import y` takes only `y` from module `x`.",
        code='''
import numpy as np                 # numerical arrays
import matplotlib.pyplot as plt    # plots
from math import pi, sqrt          # two items from the math module''',
        tip=None),
    "exceptions": dict(
        title="Handling errors: try / except",
        text="Code inside `try` runs normally; if an error (**exception**) happens, Python jumps to `except` "
             "instead of stopping the program. `raise` creates an error on purpose.",
        code='''
try:
    x = 1 / 0
except ZeroDivisionError:
    x = float("inf")

if dt <= 0:
    raise ValueError("dt must be positive")''',
        tip=None),
    "with_files": dict(
        title="Files and the with statement",
        text="`with open(...) as f:` opens a file and closes it automatically at the end of the block, even if "
             "an error occurs.",
        code='''
with open("results.txt", "w") as f:   # "w" = write, "r" = read, "a" = append
    f.write("BER = 1e-3\\n")''',
        tip=None),
    "main_guard": dict(
        title="if __name__ == \"__main__\"",
        text="The block under this line runs only when the file is executed directly (`python file.py`), not when "
             "another program imports its functions. It usually holds the “main program”.",
        code='''
def simulate():
    ...

if __name__ == "__main__":
    simulate()''',
        tip=None),
    "numpy": dict(
        title="NumPy arrays — maths on many numbers at once",
        text="A NumPy **array** is a grid of numbers (1-D vector, 2-D matrix, or more). Its **shape** gives the size "
             "along each **axis**. Operations act on all elements at once (**vectorisation**), which is ~100× "
             "faster than a Python loop.",
        code='''
import numpy as np
a = np.zeros((3, 4))        # 3 rows x 4 columns of 0.0
a.shape                     # (3, 4)
t = np.arange(0, 1, 0.25)   # [0, 0.25, 0.5, 0.75]
x = np.linspace(0, 1, 5)    # 5 equally spaced points from 0 to 1
y = np.sin(2*np.pi*t)       # applied to every element
a[0, :]                     # first row;  a[:, 1] = second column
a.sum(axis=0)               # sum down the columns -> shape (4,)
a.reshape(4, 3)             # same numbers, new shape
np.mean(y), np.max(y), np.abs(y), np.sqrt(4)''',
        tip=["`axis=0` works *down the rows* (one result per column), `axis=1` *along each row*.",
             "`np.zeros(5)` is **real**: storing complex numbers in it silently drops the imaginary part; use "
             "`dtype=complex` when needed."]),
    "numpy_broadcast": dict(
        title="NumPy broadcasting and fancy indexing",
        text="When two arrays of different shapes are combined, NumPy stretches axes of length 1 automatically "
             "(**broadcasting**). `x[None, :]` or `x[:, None]` adds such an axis. Indexing with a list or a boolean "
             "array selects many elements at once.",
        code='''
col = np.array([[1], [2], [3]])   # shape (3, 1)
row = np.array([10, 20])          # shape (2,)
col * row                         # shape (3, 2): every combination
v = np.array([5, 6, 7, 8])
v[[0, 3]]                         # [5, 8]   list of indices
v[v > 6]                          # [7, 8]   boolean mask''',
        tip=None),
    "numpy_linalg": dict(
        title="Linear algebra: @, inverse, solve",
        text="`A @ B` is matrix multiplication. `np.linalg.solve(A, b)` solves A x = b (better than computing the "
             "inverse). `np.linalg.eig`, `det`, `inv` are also available. On arrays with more than 2 axes, `@` "
             "multiplies the last two axes for every index of the leading ones.",
        code='''
A = np.array([[2, 1], [1, 3]])
b = np.array([1, 2])
x = np.linalg.solve(A, b)        # solution of A x = b
A @ x                            # gives back b
A.T, np.conj(A)                  # transpose, complex conjugate''',
        tip=None),
    "numpy_fft": dict(
        title="Fourier transforms with np.fft",
        text="`np.fft.fft(x)` converts a signal from time to frequency, `np.fft.ifft` goes back. `axis=` chooses "
             "the axis; `norm=\"ortho\"` keeps the energy unchanged. `np.fft.fftshift` puts frequency 0 in the middle "
             "for plotting.",
        code='''
x = np.cos(2*np.pi*5*np.arange(64)/64)   # 5 cycles in 64 samples
X = np.fft.fft(x)                        # peaks at bins 5 and 64-5
x_back = np.fft.ifft(X)                  # original signal''',
        tip=None),
    "random": dict(
        title="Random numbers",
        text="Simulations need randomness (noise, arrivals, random data). A generator created with a fixed "
             "**seed** produces the same numbers every run, so results are **reproducible**.",
        code='''
rng = np.random.default_rng(seed=1)
rng.integers(0, 2, 8)          # 8 random bits
rng.standard_normal(3)         # Gaussian, mean 0, variance 1
rng.uniform(0, 1, 3)           # uniform between 0 and 1
rng.exponential(2.0, 3)        # exponential with mean 2''',
        tip=["Change the seed to see the natural statistical spread of the results; a conclusion that changes "
             "with the seed is not a conclusion."]),
    "complex": dict(
        title="Complex numbers",
        text="Python writes the imaginary unit as `j`: `3 + 4j`. `abs(z)` is the magnitude, `z.real` / `z.imag` "
             "the parts, `np.angle(z)` the phase, `np.conj(z)` the conjugate.",
        code='''
z = 3 + 4j
abs(z), z.real, z.imag     # 5.0, 3.0, 4.0
np.exp(1j*np.pi/2)         # ~ 0 + 1j  (a rotation by 90 degrees)''',
        tip=None),
    "bitwise": dict(
        title="Bitwise operators",
        text="These act on the binary digits of integers: `a >> 1` shift right (÷2), `1 << 3` shift left "
             "(×8), `a ^ b` XOR, `a & 1` AND (keeps the last bit), `a | b` OR.",
        code='''
6 >> 1     # 3   (110 -> 011)
1 << 3     # 8
6 ^ 3      # 5   (110 XOR 011 = 101)
6 & 1      # 0''',
        tip=None),
    "pandas": dict(
        title="pandas DataFrames: tables of data",
        text="A **DataFrame** is a table with named columns, like a spreadsheet. It is used to load CSV files, "
             "compute statistics and export results.",
        code='''
import pandas as pd
df = pd.DataFrame({"snr": [0, 5, 10], "ber": [0.1, 0.02, 0.001]})
df["ber"].min()              # one column
df[df.snr > 3]               # rows that satisfy a condition
df.to_csv("results.csv", index=False)''',
        tip=None),
    "scipy": dict(
        title="SciPy: ready-made scientific tools",
        text="SciPy adds special functions (`scipy.special`), ODE solvers (`scipy.integrate.solve_ivp`), signal "
             "processing (`scipy.signal`), optimisation (`scipy.optimize`) and statistics (`scipy.stats`).",
        code='''
from scipy.integrate import solve_ivp
sol = solve_ivp(lambda t, y: -2*y, (0, 5), [1.0], max_step=0.01)
sol.t, sol.y[0]              # time points and solution of dy/dt = -2y''',
        tip=None),
    "matplotlib": dict(
        title="Plotting with Matplotlib",
        text="`matplotlib.pyplot` (imported as `plt`) draws the figures. A typical plot: create a figure, plot "
             "data, label the axes, add a legend, save and show.",
        code='''
plt.figure(figsize=(7, 4))                  # width, height in inches
plt.plot(t, y, "o-", label="response")      # o = markers, - = line
plt.semilogy(x, ber)                        # logarithmic y axis
plt.xlabel("time [s]"); plt.ylabel("y")
plt.legend(); plt.grid(True)
plt.savefig("figures/response.png")
plt.show()
fig, ax = plt.subplots(1, 2)                # two plots side by side: ax[0], ax[1]''',
        tip=["Format strings: `-` solid, `--` dashed, `:` dotted, `o` circles, `s` squares; colours like `\"r\"`, "
             "`\"C0\"`."]),
    "enumerate_zip": dict(
        title="enumerate and zip",
        text="`enumerate(seq)` gives (index, element) pairs; `zip(a, b)` walks through two sequences together.",
        code='''
for i, M in enumerate([4, 16, 64]):
    print(i, M)          # 0 4 / 1 16 / 2 64
for x, c in zip([1, 2], ["red", "blue"]):
    print(x, c)''',
        tip=None),
    "generators": dict(
        title="Generators: yield",
        text="A function with `yield` produces values one at a time instead of returning a whole list. Simulation "
             "libraries such as SimPy use generators to describe processes that wait and resume.",
        code='''
def countdown(n):
    while n > 0:
        yield n
        n -= 1
list(countdown(3))      # [3, 2, 1]''',
        tip=None),
    "assert": dict(
        title="assert: built-in self-checks",
        text="`assert condition, \"message\"` stops the program if the condition is false. Simulators use it to "
             "check assumptions (e.g. a probability between 0 and 1).",
        code='''
assert 0 <= p <= 1, "p must be a probability"''',
        tip=None),
    "typing": dict(
        title="Type hints",
        text="Annotations such as `def f(x: float) -> float:` document the expected types. Python does not enforce "
             "them; they are for readers and tools.",
        code='''
def gain_db(x: float) -> float:
    return 20 * np.log10(x)''',
        tip=None),
}
