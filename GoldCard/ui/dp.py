import streamlit as st
import sys
import pandas as pd
from collections import Counter

# allow deep recursion
sys.setrecursionlimit(10_000)

def parse_number(num_str):
    s = num_str.strip()
    clean = s.replace('$', '').replace(',', '')
    try:
        return float(clean)
    except ValueError:
        return None

def to_cents(num_str):
    v = parse_number(num_str)
    return None if v is None else int(round(v * 100))

# --- Streamlit UI setup ---
st.set_page_config(page_title="Subset Sum Finder", layout="wide")
st.title("Subset Sum Finder")
st.markdown("Find the longest subsets of monetary values that exactly match a target sum, with optional required entries.")

with st.sidebar:
    st.header("Inputs")
    target = st.text_input("Target sum e.g. 72,409.53")
    must_input = st.text_area("Must-include values (one per line)", height=150)
    values_input = st.text_area("Available values (one per line)", height=200)
    k = st.number_input("Number of combinations (K)", min_value=1, max_value=20, value=3)
    index_offset = st.number_input("Index offset", min_value=0, max_value=20, value=8)
    run = st.button("🔍 Find Combinations")

if run:
    tgt = parse_number(target)
    if tgt is None:
        st.error("Invalid target value.")
        st.stop()

    must_list = [l for l in must_input.splitlines() if l.strip()]
    vals_list = [l for l in values_input.splitlines() if l.strip()]

    # build must-include counter
    must_cents = []
    for s in must_list:
        c = to_cents(s)
        if c is None:
            st.error(f"Must-include '{s}' is invalid.")
            st.stop()
        must_cents.append(c)
    must_counter = Counter(must_cents)

    # parse values
    nums, orig = [], []
    for s in vals_list:
        c = to_cents(s)
        if c is not None:
            nums.append(c)
            orig.append(s.strip())
    n = len(nums)
    if n == 0:
        st.warning("No input values provided.")
        st.stop()

    # verify must-include availability
    pool = Counter(nums)
    for v, req in must_counter.items():
        if pool[v] < req:
            st.error(f"Must-include value {v/100:.2f} not in inputs enough times.")
            st.stop()

    # Prepare placeholders
    st.subheader("Results")
    rows = (k + 1) // 2
    placeholders = [[st.empty() for _ in range(2)] for _ in range(rows)]

    # Build suffix DP bitsets for pruning
    min_sum = sum(v for v in nums if v < 0)
    max_sum = sum(v for v in nums if v > 0)
    offset = -min_sum
    size = max_sum - min_sum
    mask = (1 << (size + 1)) - 1

    suffix_dp = [0] * (n + 1)
    suffix_dp[n] = 1 << offset
    for i in range(n - 1, -1, -1):
        p = suffix_dp[i + 1]
        v = nums[i]
        if v >= 0:
            suffix_dp[i] = p | ((p << v) & mask)
        else:
            suffix_dp[i] = p | (p >> -v)

    target_c = int(round(tgt * 100))
    found = [0]  # use a list so dfs can increment it

    # --- DFS with pruning and immediate display ---
    def dfs(idx: int, current_sum: int, combo: list[int]):
        # stop if we've already found k
        if found[0] >= k:
            return

        # record combo if it matches target exactly
        if current_sum == target_c:
            cc = Counter(nums[i] for i in combo)
            if all(cc[v] >= cnt for v, cnt in must_counter.items()):
                # display immediately
                row_idx, col_idx = divmod(found[0], 2)
                ph = placeholders[row_idx][col_idx]
                with ph.container():
                    st.subheader(f"Combination #{found[0]+1} (length={len(combo)})")
                    used_col, unused_col = st.columns(2)
                    with used_col:
                        st.markdown("**Used:**")
                        df_used = pd.DataFrame([
                            {'idx': i + index_offset, 'value': orig[i]} for i in combo
                        ])
                        st.dataframe(df_used, hide_index=True)
                    with unused_col:
                        st.markdown("**Unused:**")
                        unused_idxs = sorted(set(range(n)) - set(combo))
                        df_unused = pd.DataFrame([
                            {'idx': i + index_offset, 'value': orig[i]} for i in unused_idxs
                        ])
                        st.dataframe(df_unused, hide_index=True)
                    st.metric(label="Sum", value=f"{tgt:,.2f}")
                found[0] += 1
            return

        # prune if no items left or unreachable sum
        if idx == n:
            return
        rem = target_c - current_sum
        pos = rem + offset
        if pos < 0 or pos > size or ((suffix_dp[idx] >> pos) & 1) == 0:
            return

        # include nums[idx]
        combo.append(idx)
        dfs(idx + 1, current_sum + nums[idx], combo)
        combo.pop()

        # exclude nums[idx]
        dfs(idx + 1, current_sum, combo)

    # run DFS under spinner
    with st.spinner("Working..."):
        dfs(0, 0, [])

    if found[0] == 0:
        st.info("No combinations found matching criteria.")
