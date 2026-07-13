# 3D Bin Packing

Container / truck-loading optimizer for the **3D Bin Packing Problem** — pack a set of boxes
into containers while minimizing wasted volume, using **simplex**, **heuristics**,
**metaheuristics** and a **reinforcement-learning** policy. Built during an end-of-studies
internship (PFE) at Smart Automation, Tangier.

## The problem

Given boxes $i$ with volume $v_i$ and containers of capacity $V$, minimize the number of
containers used:

$$ \min \sum_{k} y_k \quad\text{s.t.}\quad \sum_i v_i\,x_{ik} \le V\,y_k,\qquad \sum_k x_{ik} = 1 $$

with $x_{ik}\in\{0,1\}$ (box $i$ placed in container $k$) and $y_k\in\{0,1\}$ (container $k$ used),
subject to 3D non-overlap and orientation constraints.

## Files

- `optimization.py` — main optimizer / objective
- `reinforcement_learning.py` — RL packing policy
- `simplexe_algo.py` — simplex routine
- `OP.py`, `unite_de_charge.py`, `ER.py`, `uc.py` — load-unit modelling
