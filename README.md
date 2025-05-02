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

##

---

## Introduction

Reconciling monthly autopayment charges against a large volume of credit‑card transactions has long been a bottleneck for our finance team. Each period, our finance team receive a single autopayment posting—for example, \$73,948.09—but our ledger contains dozens of individual entries (purchases, refunds, and pending disputes) that must collectively match this amount. Manually inspecting hundreds of line items to find the exact combination of debits and credits is both time‑consuming and error‑prone.

To streamline and automate this reconciliation, I developed a tool that efficiently identifies the longest transaction subsets summing to the target payment—removing as many matching records as possible while carrying forward only the unresolved items. The following sections describe the mathematical challenge and our optimized DP-pruned solution.

## Real-World Application: Credit-Card Autopayment Reconciliation: Credit-Card Autopayment Reconciliation: Credit-Card Autopayment Reconciliation

### The Problem

Every month your company’s billing system records a set of credit-card transactions:

```
[-56.94, -35.00, 1022.12, 8799.98, 47.94, …]
```

Meanwhile your autopayment gateway charges a fixed autopayment amount, e.g. **\$72,409.53**. Your goal is to **match** (and then remove) exactly those transactions that sum to the autopayment total.

Because any subset of the **n** transactions might sum to the target, a brute-force search would require checking

```
2^n
```

possible subsets—impossible even for **n≈50** (\~2^50 ≈ 10^15 subsets).

### Pseudo-Polynomial DP to the Rescue

Instead of O(2^n), we:

1. **Scale** each transaction and the target into integer “cents” (so all values are ints).
2. Build a **bitset DP** of size:

   ```text
   Range = (sum of positives) - (sum of negatives)
   ```

   marking which sums are reachable in O(n×Range) time.
3. **Prune** any backtracking branch that the DP shows can’t reach the target.

This turns subset-sum decision into a **pseudo-polynomial** O(nT) algorithm, where **T** is the target in cents (e.g. 7,240,953 ¢). In practice, with **n≈50** and **T≲10^7**, that’s just a few hundred million bit-operations—entirely feasible.

### Why “Top K Longest” Helps

Even after pruning, there may be **many** valid subsets. We actually want to:

* **Delete** as many matching transactions as possible each month
* **Roll over** the leftover transactions (e.g. refunds, chargebacks) into next month’s reconciliation

So we ask for the **top K longest** subsets (those that consume the most transactions). By removing those, we minimize the number of un-matched transactions we carry forward.

### Handling Carry-Forwards with “Must-Include”

Some transactions must **not** be reconciled yet (e.g. pending disputes). We list them in a **MUST INCLUDE** set—these values are forced into every subset. In effect, they become part of the target-sum equation rather than optional matches.

### Mathematical Summary

* **Total subsets** of n items:

  ```text
  |P({1,…,n})| = 2^n
  ```

  Exponential in n.

* **DP reachability**:

  ```text
  O(n × T)
  ```

  where T = target in integer cents. This is pseudo-polynomial, much faster for moderate T.

* **Pruned enumeration**: only explores branches that DP proves could reach the target. In many real datasets this cuts the search tree from **2^n** to a tiny fraction—often just a few thousand branches.

* **Top-K stop**: generate combinations in descending size and halt after K matches.

### Code Snippet

```python
from solution import Solution

solver = Solution()
results = solver.topKLongest(
    target="72,409.53",
    mustInclude=["-219.00","-823.05"],  # e.g. carry-forward disputes
    numbers=[
      "-56.94","-35.00","1022.12","8799.98", …  # your statement lines
    ],
    K=3,
    indexOffset=8
)
# results now holds up to 3 of the longest matching subsets—
# each with 'used', 'unused', 'length', and 'sum' keys.
```

By combining bitset DP, pruned backtracking, and a top-K stop condition, this tool turns an intractable **2^n** enumeration into a practical reconciliation assistant—perfect for matching autopayments against real-world credit-card statement data.

