# Markov Decision Process

A grid-world data structure built from scratch in **C++** (doubly-linked cells) — the backbone
for a **value-iteration** MDP solver.

## Value iteration

The optimal value function satisfies the Bellman optimality equation

$$ V^*(s) = \max_a \sum_{s'} P(s'\mid s,a)\,\big[\, r(s,a,s') + \gamma\,V^*(s') \,\big] $$

iterated until convergence; the greedy policy is then extracted as

$$ \pi^*(s) = \arg\max_a \sum_{s'} P(s'\mid s,a)\,\big[\, r(s,a,s') + \gamma\,V^*(s') \,\big] $$

## Files

- `main.cpp` — linked-cell grid world (`Celule` nodes with Up/Down/Left/Right links)
