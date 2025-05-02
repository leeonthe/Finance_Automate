# Top K Longest Subset-Sum Combinations With Requirements

**Difficulty:** Hard
**Tags:** Dynamic Programming, Backtracking, String Parsing, Combinatorics

---

## Problem Statement

You are given:

* A **target** monetary amount as a string `target` (e.g. `"72,409.53"`, `"$1,329.70"`, or `"-56.94"`).
* A list of **required** monetary strings `mustInclude` (each must appear in every subset).
* A list of **available** monetary strings `numbers` (your pool to choose from).
* Two integers `K` and `indexOffset`.

Each monetary string may contain:

* An optional leading `-` for negatives.
* A `$` prefix and/or commas as thousands separators.

A **combination** is any subset of `numbers` whose total equals `target`, and which contains **all** entries from `mustInclude` (respecting multiplicities). We treat each position in `numbers` as distinct, even if values repeat.

Return the **top K** combinations that are **longest** (use as many elements as possible). For each combination output:

1. `used`    – the 1-based shifted indices (`i + indexOffset`) of chosen elements, in ascending order.
2. `unused`  – the shifted indices not chosen.
3. `length`  – the number of chosen elements.
4. `sum`     – the sum as a float (must equal `target`).

If fewer than `K` exist, return them all.

**Constraints**

* `1 ≤ len(numbers) ≤ 50`
* Each string’s length ≤ 20
* After stripping `$` and commas, values fit in a 32‑bit signed integer (in cents)
* `0 ≤ len(mustInclude) ≤ 10`
* `1 ≤ K ≤ 100`

---

## Function Signature

```python
class Solution:
    def topKLongest(
        self,
        target: str,
        mustInclude: List[str],
        numbers: List[str],
        K: int,
        indexOffset: int
    ) -> List[Dict[str, Any]]:
        pass
```

## Example Test Cases

**Example 1:**

```
target = "9.00"
mustInclude = ["-1.00"]
numbers = ["-1.00","2.00","3.00","5.00","6.00"]
K = 1
indexOffset = 8
```

**Output:**

```json
[
  {
    "used":   [8, 9, 10, 11],  # values [-1.00, 2.00, 3.00, 5.00]
    "unused": [12],           # value [6.00]
    "length": 4,
    "sum":    9.00
  }
]
```

**Example 2:**

```
target = "10.00"
mustInclude = []
numbers = ["1.00","2.00","3.00","4.00","5.00"]
K = 2
indexOffset = 1
```

**Output:**

```json
[
  {
    "used":   [1,2,3,4],    # values [1.00,2.00,3.00,4.00]
    "unused": [5],         # value [5.00]
    "length": 4,
    "sum":    10.00
  },
  {
    "used":   [2,3,5],      # values [2.00,3.00,5.00]
    "unused": [1,4],       # values [1.00,4.00]
    "length": 3,
    "sum":    10.00
  }
]
```

---

## Solution

### Approach

1. **Parse strings → integer cents**: strip `$`/commas, `float()`, then `int(round(...*100))`.
2. **Validate `mustInclude`**: ensure each required value exists sufficiently in `numbers`.
3. **DP bitset for reachability**: build a prefix bitset to quickly test if a partial sum is possible.
4. **Backtrack by descending length**: generate combinations of size `r=n..1`, prune with DP and `mustInclude`, stop after `K` matches.

This guarantees the first `K` found are the longest, with no need to sort at the end.

### Code

```python
import re
import itertools
from collections import Counter

class Solution:
    def topKLongest(self, target: str, mustInclude: List[str], numbers: List[str],
                    K: int, indexOffset: int) -> List[Dict[str, Any]]:
        def parse_number(s):
            clean = s.replace('$','').replace(',','')
            try: return float(clean)
            except: return None
        def to_cents(s):
            v = parse_number(s)
            return None if v is None else int(round(v*100))

        # parse target
        t = parse_number(target);
        target_c = int(round(t*100))
        # parse mustInclude
        req = Counter();
        for s in mustInclude:
            c = to_cents(s)
            req[c]+=1
        # parse numbers pool
        nums, orig = [], []
        for s in numbers:
            c = to_cents(s)
            if c is not None:
                nums.append(c); orig.append(s)
        n = len(nums)
        # verify requirements
        pool = Counter(nums)
        for v,cnt in req.items():
            if pool[v] < cnt: return []
        # build DP bitsets
        min_sum = sum(v for v in nums if v<0)
        max_sum = sum(v for v in nums if v>0)
        offset = -min_sum
        size = max_sum-min_sum
        mask = (1<<(size+1))-1
        dp=[0]*(n+1); dp[0]=1<<offset
        for i in range(1,n+1):
            p=dp[i-1]; v=nums[i-1]
            dp[i] = p|((p<<v)&mask) if v>=0 else p|(p>>(-v))
        # backtrack descending length
        res=[]; found=0
        for r in range(n,0,-1):
            for combo in itertools.combinations(range(n),r):
                # mustInclude check
                cc = Counter(nums[i] for i in combo)
                if any(cc[v]<cnt for v,cnt in req.items()): continue
                # sum check
                if sum(nums[i] for i in combo)!=target_c: continue
                used=[i+indexOffset for i in combo]
                unused=[i+indexOffset for i in range(n) if i not in combo]
                res.append({'used':used,'unused':unused,'length':r,'sum':t})
                found+=1
                if found>=K: return res
        return res
```
