import streamlit as st
import pandas as pd
from collections import Counter
from ortools.sat.python import cp_model

# --- helpers ---
def parse_number(s: str):
    s = s.strip().replace('$','').replace(',','')
    try:    return float(s)
    except: return None

def to_cents(s: str):
    v = parse_number(s)
    return None if v is None else int(round(v * 100))

# --- UI ---
st.set_page_config(page_title="Subset Sum Finder", layout="wide")
st.title("Subset Sum Finder")
st.markdown("Find the longest subsets that sum exactly to your target.")

with st.sidebar:
    target       = st.text_input("Target sum (e.g. 72,409.53)")
    must_input   = st.text_area("Must-include (one per line)", height=150)
    values_input = st.text_area("Available (one per line)",    height=200)
    K            = st.number_input("Top K combos to show", 1, 50, 3)
    idx_off      = st.number_input("Index offset",          0, 20, 8)
    run          = st.button("🔍 Find Combinations")

if not run:
    st.stop()

# --- parse & validate ---
tgt = parse_number(target)
if tgt is None:
    st.error("Invalid target."); st.stop()
target_c = int(round(tgt * 100))

must_vals = [to_cents(x) for x in must_input.splitlines() if x.strip()]
if any(v is None for v in must_vals):
    st.error("Bad must-include entries."); st.stop()
must_ctr = Counter(must_vals)

vals = [(to_cents(x), x.strip())
        for x in values_input.splitlines() if x.strip()]
nums = [v for v,_ in vals]
orig = [s for _,s in vals]
n    = len(nums)
if n == 0:
    st.warning("No values provided."); st.stop()

# check must-include availability
pool = Counter(nums)
for v,count in must_ctr.items():
    if pool[v] < count:
        st.error(f"Need {count}×{v/100:.2f}, but only {pool[v]} available.")
        st.stop()

# placeholders
st.subheader("Results")
rows = (K + 1) // 2
placeholders = [[st.empty() for _ in range(2)] for _ in range(rows)]

# --- 1) Build & solve optimization model ---
opt_model = cp_model.CpModel()
x = [opt_model.NewBoolVar(f"x{i}") for i in range(n)]

# sum==target
opt_model.Add(sum(nums[i] * x[i] for i in range(n)) == target_c)
# must-include
for v,req in must_ctr.items():
    idxs = [i for i,val in enumerate(nums) if val == v]
    opt_model.Add(sum(x[i] for i in idxs) >= req)

# maximize count
opt_model.Maximize(sum(x))

opt_solver = cp_model.CpSolver()
status = opt_solver.Solve(opt_model)
if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    st.info("No solution meets target.")
    st.stop()

max_len = int(opt_solver.ObjectiveValue())

# --- 2) Build enumeration (SAT) model with sum==max_len constraint ---
enum_model = cp_model.CpModel()
y = [enum_model.NewBoolVar(f"y{i}") for i in range(n)]

# same sum & must-include constraints
enum_model.Add(sum(nums[i] * y[i] for i in range(n)) == target_c)
for v,req in must_ctr.items():
    idxs = [i for i,val in enumerate(nums) if val == v]
    enum_model.Add(sum(y[i] for i in idxs) >= req)

# *fix* the cardinality
enum_model.Add(sum(y) == max_len)

# --- 3) Enumerate top-K solutions ---
class CB(cp_model.CpSolverSolutionCallback):
    def __init__(self, vars_, K):
        super().__init__()
        self._vars = vars_
        self._K    = K
        self.count = 0

    def OnSolutionCallback(self):
        if self.count >= self._K:
            self.StopSearch()
            return
        combo = [i for i in range(n) if self.Value(self._vars[i])]
        r, c = divmod(self.count, 2)
        ph = placeholders[r][c]
        with ph.container():
            st.subheader(f"Combination #{self.count+1} (len={max_len})")
            uc, uu = st.columns(2)
            with uc:
                st.markdown("**Used:**")
                df = pd.DataFrame([{'idx': i+idx_off, 'value': orig[i]} for i in combo])
                st.dataframe(df, hide_index=True)
            with uu:
                st.markdown("**Unused:**")
                rest = sorted(set(range(n)) - set(combo))
                df2 = pd.DataFrame([{'idx': i+idx_off, 'value': orig[i]} for i in rest])
                st.dataframe(df2, hide_index=True)
            st.metric("Sum", f"{tgt:,.2f}")
        self.count += 1

enum_solver = cp_model.CpSolver()
with st.spinner("Enumerating top-K…"):
    enum_solver.SearchForAllSolutions(enum_model, CB(y, K))