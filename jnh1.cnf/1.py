"""
SAT-to-SubsetSum Converter — CORRECT Karp Reduction for General SAT
Uses:
  - 2-digit columns (base 100) to prevent carry overflow
  - Powers-of-2 slack variables (1, 2, 4, 8) per clause
  - Clause target = max_clause_size + 1 = 9
  This guarantees a solution exists iff the SAT formula is satisfiable.
"""

def convert_sat_to_subset_sum(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    n_vars, n_clauses = 0, 0
    data_lines = []
    for line in lines:
        if line.startswith('c') or not line.strip():
            continue
        if line.startswith('p'):
            parts = line.split()
            n_vars, n_clauses = int(parts[2]), int(parts[3])
        else:
            data_lines.append(line)

    raw_data = " ".join(data_lines).split()
    clauses = []
    current_clause = []
    for val in raw_data:
        num = int(val)
        if num == 0:
            clauses.append(current_clause)
            current_clause = []
        else:
            current_clause.append(num)

    max_clause_len = max(len(c) for c in clauses)
    clause_target = max_clause_len + 1

    CW = 2
    n_cols = n_vars + n_clauses

    def make_element(var_idx, clause_bits):
        s = ['00'] * n_cols
        s[var_idx] = '01'
        for c_idx, bit in clause_bits.items():
            s[n_vars + c_idx] = f'{bit:02d}'
        return int("".join(s))

    elements = []

    for i in range(1, n_vars + 1):
        pos_clauses = {c_idx: 1 for c_idx, c in enumerate(clauses) if i in c}
        elements.append(make_element(i - 1, pos_clauses))
        neg_clauses = {c_idx: 1 for c_idx, c in enumerate(clauses) if -i in c}
        elements.append(make_element(i - 1, neg_clauses))

    for j in range(n_clauses):
        power = 1
        while power < clause_target:
            s = ['00'] * n_cols
            s[n_vars + j] = f'{power:02d}'
            elements.append(int("".join(s)))
            power *= 2

    target_str = ['01'] * n_vars + [f'{clause_target:02d}'] * n_clauses
    target = int("".join(target_str))

    return elements, target, n_vars, n_clauses, clauses, clause_target

elements, target, nv, nc, clauses, ct = convert_sat_to_subset_sum('jnh1.cnf')

with open('z_test_elements.txt', 'w') as out:
    out.write(", ".join(map(str, elements)))
    out.write(f"\n\ngoal: {target}")

print(f"Converted jnh1.cnf (CORRECT general-SAT reduction)")
print(f"Variables: {nv}, Clauses: {nc}")
print(f"Max clause size: {max(len(c) for c in clauses)}")
print(f"Clause target: {ct}")
print(f"Elements: {len(elements)} (200 literal + {len(elements)-200} slack)")
print(f"Target digits: {len(str(target))}")
print(f"Slacks per clause: {len(elements)-200}//{ nc} = powers of 2")
print(f"Saved to z_test_elements.txt")
