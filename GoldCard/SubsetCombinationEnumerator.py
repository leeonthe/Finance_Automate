#!/usr/bin/env python3
import re
import sys
import itertools
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


def top_k_longest(target_str, must_include_strs, number_strs, k=3, index_offset=8):
    # parse target
    tgt = parse_number(target_str)
    if tgt is None:
        print("Invalid target value.")
        return
    target = int(round(tgt * 100))

    # parse must_include
    must_cents = []
    for s in must_include_strs:
        c = to_cents(s)
        if c is None:
            print(f"Must-include value '{s}' is invalid.")
            return
        must_cents.append(c)
    must_counter = Counter(must_cents)

    # parse inputs
    nums, orig = [], []
    for s in number_strs:
        c = to_cents(s)
        if c is not None:
            nums.append(c)
            orig.append(s.strip())
    n = len(nums)
    if n == 0:
        print("No input values provided.")
        return

    # verify must_include values exist
    all_nums_counter = Counter(nums)
    for val, req in must_counter.items():
        if all_nums_counter[val] < req:
            print(f"Must-include value {val/100:.2f} not matched enough times in input.")
            return

    print(f"Total input values: {n}")

    found = 0
    # search by descending length
    for r in range(n, 0, -1):
        for combo in itertools.combinations(range(n), r):
            # check must_include presence
            combo_counter = Counter(nums[i] for i in combo)
            if any(combo_counter[val] < cnt for val, cnt in must_counter.items()):
                continue
            # sum check
            if sum(nums[i] for i in combo) == target:
                found += 1
                print(f"\nCombination #{found} (length={r}):")
                # used indices and values
                for i in combo:
                    print(f"  idx {i+index_offset}: {orig[i]}")
                # unused indices and values
                unused = set(range(n)) - set(combo)
                print("Unused:")
                for i in sorted(unused):
                    print(f"  idx {i+index_offset}: {orig[i]}")
                print(f"Sum: {tgt:,.2f}")
                if found >= k:
                    return
    if found == 0:
        print("No combinations found matching criteria.")


def main():
    # get target
    print("Enter target sum (e.g. 72,409.53 or -1,329.70):")
    target = input().strip()
    # get must include
    print("Enter MUST INCLUDE values one per line (‘done’ when finished):")
    musts = []
    while True:
        l = input().strip()
        if l.lower() == 'done':
            break
        if l:
            musts.append(l)
    # get inputs
    print("Enter available values one per line (‘done’ when finished):")
    lines = []
    while True:
        l = input().strip()
        if l.lower() == 'done':
            break
        if l:
            lines.append(l)
    top_k_longest(target, musts, lines, k=3, index_offset=8)

if __name__ == '__main__':
    main()
