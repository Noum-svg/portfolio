# Tropical Virus PhyloTree

Transform viral RNA/DNA sequences into an **optimized phylogenetic tree** by learning a
*tropical* correction of a sequence-distance matrix, then running Neighbor-Joining.
Ships a **React** dashboard, a **FastAPI** service, a **Streamlit** app and one-command
**Docker** deployment.

## The math

Learn a symmetric, zero-diagonal correction $\omega$ and form the corrected distance matrix

$$ X = D + \omega $$

where $D$ is the initial sequence-distance matrix. $\omega$ is optimized to reduce the
**tropical four-point violations** of $X$; Neighbor-Joining then reconstructs the tree.

The sequence distance blends a normalized Hamming term $H$ and a length penalty $P$:

$$ d(s_i, s_j) = \alpha\,H(s_i, s_j) + (1-\alpha)\,P(s_i, s_j), \qquad \alpha = 0.9 $$

## Modules

- `main.py` — CLI entry point running the full pipeline
- `distances.py` — sequence distance & distance matrix
- `tropical_grassmannian.py` — tropical four-point violation objective
- `tropical_gradient_descent.py` — optimizes the correction $\omega$
- `phylogeny.py` — Neighbor-Joining tree reconstruction
- `train.py` · `evaluate.py` · `data_loader.py` — pipeline glue

## Stack

`python` · `tropical-geometry` · `fastapi` · `react` · `docker` · `streamlit`
