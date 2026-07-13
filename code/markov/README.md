# HMM & Markov Chains

Markov-chain and Hidden Markov Model methods for **sequence and text analysis** —
transition-matrix estimation, decoding and scoring.

## Core objects

Transition matrix $A$ (and, for HMMs, emission matrix $B$):

$$ A_{ij} = P(q_{t+1} = j \mid q_t = i), \qquad \sum_j A_{ij} = 1 $$

Sequence likelihood via the **forward** recursion:

$$ \alpha_t(j) = \Big(\sum_i \alpha_{t-1}(i)\,A_{ij}\Big)\,b_j(o_t) $$

and the most likely hidden path via **Viterbi**:

$$ \delta_t(j) = \max_i\,\delta_{t-1}(i)\,A_{ij}\,b_j(o_t) $$

## Files

- `markov_analysis.py` — estimation, decoding & scoring (extracted from the notebook)
