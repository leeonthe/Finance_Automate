import itertools
from collections import Counter
from typing import List, Dict, Any, Optional

def parse_number(s: str) -> Optional[float]:
    clean = s.replace('$', '').replace(',', '').strip()
    try:
        return float(clean)
    except ValueError:
        return None

def to_cents(s: str) -> Optional[int]:
    v = parse_number(s)
    return None if v is None else int(round(v * 100))

def top_k_longest(
    target: str,
    must_include: List[str],
    numbers: List[str],
    K: int,
    index_offset: int
) -> List[Dict[str, Any]]:
    # 1. Parse target
    t = parse_number(target)
    if t is None:
        return []
    target_c = int(round(t * 100))

    # 2. Parse must-include values
    req = Counter()
    for s in must_include:
        c = to_cents(s)
        if c is None:
            return []
        req[c] += 1

    # 3. Parse available numbers
    nums: List[int] = []
    orig: List[str] = []
    for s in numbers:
        c = to_cents(s)
        if c is not None:
            nums.append(c)
            orig.append(s)
    n = len(nums)
    if n == 0:
        return []

    # 4. Verify must-include availability
    pool = Counter(nums)
    for v, cnt in req.items():
        if pool[v] < cnt:
            return []

    # 5. Build suffix DP bitsets for pruning
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

    # 6. Backtracking with DP pruning
    results: List[List[int]] = []

    def dfs(idx: int, current_sum: int, combo: List[int]):
        # Hit exact target: record if must-include satisfied
        if current_sum == target_c:
            cc = Counter(nums[i] for i in combo)
            if all(cc[v] >= cnt for v, cnt in req.items()):
                results.append(combo.copy())
            return
        # Exhausted items
        if idx == n:
            return
        # Prune impossible suffix
        rem = target_c - current_sum
        pos = rem + offset
        if pos < 0 or pos > size or ((suffix_dp[idx] >> pos) & 1) == 0:
            return
        # Include
        combo.append(idx)
        dfs(idx + 1, current_sum + nums[idx], combo)
        combo.pop()
        # Exclude
        dfs(idx + 1, current_sum, combo)

    dfs(0, 0, [])

    # 7. Select top K by length descending
    results.sort(key=lambda c: len(c), reverse=True)
    topk = results[:K]

    # 8. Format output
    output: List[Dict[str, Any]] = []
    for combo in topk:
        used = [i + index_offset for i in combo]
        unused = [i + index_offset for i in range(n) if i not in combo]
        output.append({
            "used": used,
            "unused": unused,
            "length": len(combo),
            "sum": t
        })

    return output
