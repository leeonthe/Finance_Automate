# Top K Longest Subset-Sum Combinations With Requirements

**Difficulty:** Hard

**Tags:**  Pseudo-Polynomial, Dynamic Programming, Backtracking, String Parsing, Subset Combinatorics

---

## Introduction

Reconciling monthly autopayment charges against a large volume of credit-card transactions has long been a bottleneck for our finance team. Each period, our finance team receive a single autopayment posting—for example, \$73,948.09—but our ledger contains dozens of individual entries (purchases, refunds, and pending disputes) that must collectively match this amount. Manually inspecting hundreds of line items to find the exact combination of debits and credits is both time-consuming and error-prone.

## Real-World Application: Credit-Card Autopayment Reconciliation

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
* After stripping `$` and commas, values fit in a 32-bit signed integer (in cents)
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

---

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

**Pseudo-Polynomial DP to the Rescue**

Instead of O(2^n), we:

* **Scale** each transaction and the target into integer “cents” (so all values are ints).
* **Build a bitset DP** (`suffix_dp[i]`) of size:

  ```text
  Range = (sum of positives) - (sum of negatives)
  ```

  marking which sums are reachable using items **i..n-1** in O(n×Range) time.
* **Prune** any backtracking branch whose remaining items can’t reach the needed sum.

This turns subset-sum decision into a **pseudo-polynomial** O(n T) algorithm, where T is the target in cents (e.g. 7,240,953 ¢). In practice, with n≈50 and T≲10^7, that’s just a few hundred million bit-operations—entirely feasible.

**Why “Top K Longest” Helps**

Even after pruning, there may be many valid subsets. We actually want to:

* **Delete** as many matching transactions as possible each month
* **Roll over** the leftover transactions (e.g. refunds, chargebacks) into next month’s reconciliation

So we ask for the **top K longest** subsets (those that consume the most transactions). By removing those, we minimize the number of un-matched transactions we carry forward.

**Handling Carry-Forwards with “Must-Include”**

Some transactions must **not** be reconciled yet (e.g. pending disputes). We list them in a **MUST INCLUDE** set—these values are forced into every subset. In effect, they become part of the target-sum equation rather than optional matches.

**Mathematical Summary**

* **Total subsets** of n items:

  ```text
  |P({1,…,n})| = 2^n
  ```

  Exponential in n.

* **DP reachability:**

  ```text
  O(n × T)
  ```

  where T = target in cents. This is pseudo-polynomial, much faster for moderate T.

* **Pruned enumeration:** only explores branches that DP proves could reach the target—often reducing 2^n to a small fraction.

* **Top-K stop:** backtracking halts as soon as K matches are found.

---

### Approach

1. **Parse strings → integer cents**: strip `$`/commas, `float()`, then `int(round(...*100))`.
2. **Validate `mustInclude`**: ensure each required value exists sufficiently in `numbers`.
3. **Build suffix-DP bitsets** for reachability on suffixes `i..n-1`.
4. **Backtrack with pruning**: recursively include/exclude each index, but skip any branch whose remaining suffix-DP bitset says target unreachable.
5. **Collect & sort** all valid combos by length descending; take top K.
6. **Format** as list of dicts with `used`, `unused`, `length`, and `sum`.

---

### Code

```python
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
```

---

### ✅ Why Use Pseudo-Polynomial Optimization?

In the worst case, checking all subsets requires brute-force enumeration of
**2ⁿ subsets**—totally infeasible even for modest sizes (n ≈ 30–50).

However, this algorithm dramatically improves performance using a **pseudo-polynomial time dynamic programming (DP)** strategy. Here's what that means:

* Instead of exploring all possible subsets, we **track which sums are even possible** using a bitset-based DP table (called `suffix_dp`).
* This DP is **not exponential in `n`**, but rather **O(n × T)**, where `T` is the target sum in cents.
* That’s called **pseudo-polynomial time**—because the runtime depends on the **numeric value** of `T`, not its bit-length.

#### ✅ Why this matters in practice:

| Approach       | Time Complexity | Practical Feasibility          |
| -------------- | --------------- | ------------------------------ |
| Brute force    | O(n × 2ⁿ)       | Infeasible beyond n=25         |
| Pseudo-poly DP | O(n × T)        | Fast when T is moderate (<10⁷) |

For example:

* Even with 50 transactions and a target of \$72,409.53 (i.e. 7,240,953 cents),
* The algorithm only performs **hundreds of millions of bit-operations** instead of quadrillions of subset checks.

### 💡 How It Works

1. **Bitset DP** builds a compact summary of what sums are possible using each suffix of the input.
2. **Backtracking** only explores paths that the DP proves can potentially reach the target.
3. **"Must-include" enforcement** ensures required values are always used in valid combinations.
4. **Top-K early stopping** ensures we never generate more than necessary.

---

### 🔍 What is Pseudo-Polynomial?

A pseudo-polynomial time algorithm is one whose runtime depends on the **numeric value** of the input (like the target sum `T`), rather than its **bit-length**.
In contrast to true polynomial time (which depends only on the size of the input), pseudo-polynomial algorithms can be fast in practice when input numbers are not too large.

→ [What is pseudo-polynomial time? (Stack Overflow)](https://stackoverflow.com/questions/19647658/what-is-pseudopolynomial-time-how-does-it-differ-from-polynomial-time)

---

### Correctness Proof

**Definitions**

Let \$S = \[n\_1, \dots, n\_n]\$ be the multiset of input values (in cents).
Let \$M\$ be the multiset of must-include values.
Let \$T\$ be the target sum (in cents).
A combination of size \$r\$ is any \$r\$-element subset of indices \${i\_1, \dots, i\_r}\subseteq{1,\dots,n}\$.
Denote \$\Sigma(C)=\sum\_{i\in C}n\_i\$.
We say \$C\$ is **valid** iff (a) \$M\subseteq C\$ (multiplicity) and (b) \$\Sigma(C)=T\$.

---

#### Theorem 1 (Exhaustive Reachability via DP)

For each \$i\$, `suffix_dp[i]` has a 1-bit at position `offset+x` **iff** some subset of items \$i..n-1\$ can sum to \$x\$.  ∎

#### Theorem 2 (Pruning Soundness)

At call `dfs(idx,current_sum)`, if `suffix_dp[idx]` has no 1-bit at `offset+(T-current_sum)`, **no** suffix subset can complete to target. Pruning never discards a valid combo.  ∎

#### Theorem 3 (Completeness & Ordering)

* **Exhaustiveness**: DFS visits every prefix unless pruned.
* **Validity**: Only records combos summing to \$T\$ with all required values.
* **Ordering**: Sort by length descending ensures top-K longest.  ∎



---

### Complexity

* **DP building:** \$O(nT)\$ bit-ops
* **DFS w/ pruning:** visits \$O(nT)\$ reachable states
* **Overall:** Pseudo-polynomial \$O(nT)\$ vs brute \$O(n2^n)\$
* **Space:** \$O(nT)\$ bits + \$O(n)\$ recursion

---
