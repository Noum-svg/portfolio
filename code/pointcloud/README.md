# 3D Point-Cloud Nets

Graph neural networks (**ECC** and **MoNet**) classifying 3D point clouds (CAP3D / ShapeNet),
extended with **Federated Learning** (FedAvg IID / non-IID, VFL) and **knowledge distillation**
to compress the model roughly 4×.

## Distillation loss

The student network minimizes a blend of a hard-label term and a soft-teacher term:

$$ \mathcal{L} = \alpha\,\mathrm{CE}(y, p_s) + (1-\alpha)\,\tau^2\,\mathrm{KL}\!\big(p_t^{(\tau)} \,\|\, p_s^{(\tau)}\big) $$

where $\tau$ is the softmax temperature and $p^{(\tau)} = \mathrm{softmax}(z/\tau)$.

## Pipeline

- **C1** — centralized baseline
- **C2** — FedAvg (IID / non-IID by semantic domain), VFL (geometry / appearance)
- **C4** — distillation (teacher = C1, student ≥ 4× smaller)

## Files

- `cap3d_pipeline.py` — full pipeline (extracted from the Colab notebook)
