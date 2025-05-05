import streamlit as st
import re
import sys
import itertools
import pandas as pd
from collections import Counter

# allow deep recursion
sys.setrecursionlimit(10_000)


def parse_number(num_str):
    """
    Parse a numeric string as float (leading '-' allowed).
    Strips out '$' and commas.
    """
    s = num_str.strip()
    clean = s.replace('$', '').replace(',', '')
    try:
        return float(clean)
    except ValueError:
        return None


def to_cents(num_str):
    """
    Convert a numeric string to integer cents, or None if invalid.
    """
    v = parse_number(num_str)
    return None if v is None else int(round(v * 100))

# --- Streamlit UI ---
st.set_page_config(
    page_title="Subset Sum Finder",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔢 Subset Sum Finder")
st.markdown("Find the longest subsets of monetary values that exactly match a target sum, with optional required entries.")

# Sidebar inputs
with st.sidebar:
    st.header("Inputs")
    target = st.text_input("Target sum e.g. 72,409.53")
    must_input = st.text_area(
        "Must-include values (one per line)",
        placeholder="Enter values, e.g.\n123.45\n-56.78\nor leave it blank",
        height=150
    )
    values_input = st.text_area(
        "Available values (one per line)",
        placeholder="Enter values, e.g.\n100.00\n200.00\n-50.00",
        height=200
    )
    k = st.number_input("Number of combinations (K)", min_value=1, max_value=20, value=3)
    index_offset = st.number_input("Index offset", min_value=0, max_value=20, value=8)
    run = st.button("🔍 Find Combinations")

# Main results area
if run:
    # Parse and validate inputs
    tgt = parse_number(target)
    if tgt is None:
        st.error("Invalid target value.")
    else:
        must_list = [line for line in must_input.splitlines() if line.strip()]
        values_list = [line for line in values_input.splitlines() if line.strip()]
        # Convert to cents
        must_cents = []
        for s in must_list:
            c = to_cents(s)
            if c is None:
                st.error(f"Must-include '{s}' is invalid.")
                st.stop()
            must_cents.append(c)
        nums, orig = [], []
        for s in values_list:
            c = to_cents(s)
            if c is not None:
                nums.append(c)
                orig.append(s.strip())
        n = len(nums)
        if n == 0:
            st.warning("No input values provided.")
            st.stop()
        must_counter = Counter(must_cents)
        all_nums_counter = Counter(nums)
        for val, req in must_counter.items():
            if all_nums_counter[val] < req:
                st.error(f"Must-include value {val/100:.2f} not in inputs enough times.")
                st.stop()

        # Prepare placeholders for streaming results
        st.subheader("Results")
        rows = (k + 1) // 2
        placeholders = [[st.empty() for _ in range(2)] for _ in range(rows)]

        # Brute-force search with on-the-fly display
        target = int(round(tgt * 100))
        found = 0
        with st.spinner("Searching for combinations..."):
            for r in range(n, 0, -1):
                if found >= k:
                    break
                for combo in itertools.combinations(range(n), r):
                    # must-include check
                    combo_counter = Counter(nums[i] for i in combo)
                    if any(combo_counter[val] < cnt for val, cnt in must_counter.items()):
                        continue
                    # sum check
                    if sum(nums[i] for i in combo) == target:
                        row_idx = found // 2
                        col_idx = found % 2
                        ph = placeholders[row_idx][col_idx]
                        with ph.container():
                            st.subheader(f"Combination #{found+1} (length={r})")
                            used_col, unused_col = st.columns(2)
                            # Used table without default index
                            with used_col:
                                st.markdown("**Used:**")
                                df_used = pd.DataFrame([
                                    {'idx': i + index_offset, 'value': orig[i]} for i in combo
                                ])
                                st.dataframe(df_used, hide_index=True)
                            # Unused table without default index
                            with unused_col:
                                st.markdown("**Unused:**")
                                unused = sorted(set(range(n)) - set(combo))
                                df_unused = pd.DataFrame([
                                    {'idx': i + index_offset, 'value': orig[i]} for i in unused
                                ])
                                st.dataframe(df_unused, hide_index=True)
                            st.metric(label="Sum", value=f"{tgt:,.2f}")
                        found += 1
                        if found >= k:
                            break
        if found == 0:
            st.info("No combinations found matching criteria.")
