# ============================================================
# Cell 1
# ============================================================
!pip install -q plyfile

# ============================================================
# Cell 2
# ============================================================
import os, glob, copy, json, types, urllib.request, zipfile, hashlib
from pathlib import Path
from typing import Callable, Any
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
from plyfile import PlyData
import matplotlib.pyplot as plt
from IPython.display import display
print('torch', torch.__version__, '| CUDA:', torch.cuda.is_available())

# ============================================================
# Cell 3
# ============================================================
os.makedirs('data/ply_files', exist_ok=True)
PLY = 'data/ply_files'

# Parametres du sous-ensemble
QUICK_MODE        = True  # False = experience complete (plus longue)
NUM_SYNSETS       = 8     # nombre de categories
SAMPLES_PER_CLASS = 8 if QUICK_MODE else 40

CSV_URL = 'https://gist.githubusercontent.com/Noum-svg/0e543b52909711839ac3baf1a1533157/raw/labeled_dataset.csv'
urllib.request.urlretrieve(CSV_URL, 'labeled_dataset.csv')
df_all = pd.read_csv('labeled_dataset.csv')          # colonnes: filename, label
df_all['syn'] = df_all['filename'].str.split('_').str[0]
synsets = sorted(df_all['syn'].unique())[:NUM_SYNSETS]
df_sel = df_all[df_all['syn'].isin(synsets)].reset_index(drop=True)
df_sub = (df_sel.sample(frac=1, random_state=42)
          .groupby('label', group_keys=False).head(SAMPLES_PER_CLASS).reset_index(drop=True))
target_ids = {os.path.splitext(f)[0] for f in df_sub['filename']}
print(f'{df_sub["label"].nunique()} classes | {len(target_ids)} nuages a telecharger')

HF_ZIP = 'https://huggingface.co/datasets/tiange/Cap3D/resolve/main/PointCloud_zips_ShapeNet/compressed_pcs_00.zip'
class HTTPFile:
    def __init__(self, url):
        self.url = url; self.offset = 0
        req = urllib.request.Request(url, method='HEAD'); req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req) as r: self.size = int(r.headers['Content-Length'])
    def seek(self, o, w=0): self.offset = o if w == 0 else (self.offset + o if w == 1 else self.size + o)
    def tell(self):     return self.offset
    def seekable(self): return True
    def readable(self): return True
    def writable(self): return False
    def read(self, n=-1):
        if n < 0: n = self.size - self.offset
        if n == 0: return b''
        a, b = self.offset, self.offset + n - 1
        req = urllib.request.Request(self.url); req.add_header('Range', f'bytes={a}-{b}'); req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req) as r: d = r.read()
        self.offset += len(d); return d

print('Connexion a l archive (27 Go, lecture partielle)...')
with zipfile.ZipFile(HTTPFile(HF_ZIP)) as z:
    n = 0
    for info in z.infolist():
        fid = os.path.splitext(os.path.basename(info.filename))[0]
        if fid in target_ids:
            out = os.path.join(PLY, f'{fid}.ply')
            if not os.path.exists(out):
                with open(out, 'wb') as fo: fo.write(z.read(info))
                n += 1
                if n % 20 == 0: print(f'  {n}/{len(target_ids)} telecharges...')
print('Telechargement termine :', len(os.listdir(PLY)), 'fichiers PLY')

# ============================================================
# Cell 4
# ============================================================
df = df_sub[df_sub['filename'].apply(lambda f: os.path.exists(os.path.join(PLY, os.path.splitext(f)[0] + '.ply')))].reset_index(drop=True)
# Split manuel par classe (stratifie, sans fuite, reproductible) : 70% train / 15% val / 15% test
df['split'] = 'train'
for lab, grp in df.groupby('label'):
    idx = grp.sample(frac=1, random_state=42).index.tolist()
    n = len(idx)
    if n < 3:
        raise ValueError(f'La classe {lab!r} contient seulement {n} objets; il en faut au moins 3')
    nva = max(1, int(round(n * 0.15)))
    nte = max(1, int(round(n * 0.15)))
    ntr = n - nva - nte
    for j, ix in enumerate(idx):
        df.loc[ix, 'split'] = 'train' if j < ntr else ('val' if j < ntr + nva else 'test')
CSV = 'subset_splits.csv'
df[['filename', 'label', 'split']].to_csv(CSV, index=False)
NUM_CLASSES = df['label'].nunique()
print('Sous-ensemble final :', len(df), 'objets |', NUM_CLASSES, 'classes')
print('Repartition :', df['split'].value_counts().to_dict())
display(df.groupby(['label', 'split']).size().unstack(fill_value=0))

# ============================================================
# Cell 5
# ============================================================
"""CAP3D ShapeNet Dataset: PLY loading, sampling and train-only augmentation."""


import hashlib
import os
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset


FILE_COLUMNS = ("path", "filepath", "file_path", "filename", "file_name", "ply_file", "model_id", "id")
LABEL_COLUMNS = ("label_index", "label", "class", "category", "category_name", "class_name", "synset")

# Cache mémoire des nuages PLY bruts (avant échantillonnage/normalisation/augmentation).
# En fédéré, chaque PLY est relu des centaines de fois (rondes x époques locales) :
# le cache évite les relectures disque répétées. Active par défaut, désactivable via
# la variable d'environnement CAP3D_DISABLE_CACHE=1.
_RAW_CACHE: dict[str, np.ndarray] = {}
_CACHE_ENABLED = os.environ.get("CAP3D_DISABLE_CACHE", "") not in ("1", "true", "True")


def _find_column(columns: list[str], candidates: tuple[str, ...], kind: str) -> str:
    lookup = {str(column).strip().lower(): str(column) for column in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    raise ValueError(f"Colonne {kind} introuvable. Colonnes disponibles: {columns}")


def load_ply(path: str | Path, max_raw_points: int = 16384) -> np.ndarray:
    """Load at most max_raw_points XYZ-RGB vertices from a PLY file."""
    try:
        from plyfile import PlyData
    except ImportError as exc:
        raise ImportError(
            "La dépendance 'plyfile' est requise. Exécuter: "
            "python -m pip install -r requirements.txt"
        ) from exc
    ply_path = Path(path)
    if not ply_path.exists():
        raise FileNotFoundError(f"Fichier PLY absent: {ply_path}")
    vertex = PlyData.read(str(ply_path))["vertex"].data
    names = set(vertex.dtype.names or ())
    if not {"x", "y", "z"}.issubset(names):
        raise ValueError(f"Le fichier {ply_path} ne contient pas x, y, z")

    count = min(len(vertex), int(max_raw_points))
    xyz = np.column_stack(
        [vertex["x"][:count], vertex["y"][:count], vertex["z"][:count]]
    ).astype(np.float32)
    if {"red", "green", "blue"}.issubset(names):
        rgb = np.column_stack(
            [vertex["red"][:count], vertex["green"][:count], vertex["blue"][:count]]
        ).astype(np.float32)
    elif {"r", "g", "b"}.issubset(names):
        rgb = np.column_stack(
            [vertex["r"][:count], vertex["g"][:count], vertex["b"][:count]]
        ).astype(np.float32)
    else:
        rgb = np.zeros_like(xyz)
    if rgb.size and float(rgb.max()) > 1.0:
        rgb /= 255.0
    points = np.concatenate([xyz, np.clip(rgb, 0.0, 1.0)], axis=1)
    if not np.isfinite(points).all():
        raise ValueError(f"Valeurs non finies dans {ply_path}")
    return points


def normalize_xyz(points: np.ndarray) -> np.ndarray:
    output = points.astype(np.float32, copy=True)
    xyz = output[:, :3]
    xyz -= xyz.mean(axis=0, keepdims=True)
    radius = float(np.linalg.norm(xyz, axis=1).max())
    if radius > 0:
        xyz /= radius
    output[:, :3] = xyz
    return output


def sample_points(
    points: np.ndarray,
    n_points: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if len(points) == 0:
        raise ValueError("Nuage de points vide")
    indices = rng.choice(
        len(points),
        size=int(n_points),
        replace=len(points) < int(n_points),
    )
    return points[indices]


class PointCloudAugmenter:
    """Stochastic augmentations used only by the training dataset."""

    def __call__(self, points: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        output = points.copy()
        if rng.random() < 0.95:
            angle = float(rng.uniform(0.0, 2.0 * np.pi))
            rotation = np.array(
                [
                    [np.cos(angle), -np.sin(angle), 0.0],
                    [np.sin(angle), np.cos(angle), 0.0],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float32,
            )
            output[:, :3] = output[:, :3] @ rotation.T
        if rng.random() < 0.90:
            output[:, :3] *= float(rng.uniform(0.8, 1.25))
        if rng.random() < 0.80:
            jitter = np.clip(
                rng.normal(0.0, 0.01, output[:, :3].shape),
                -0.03,
                0.03,
            )
            output[:, :3] += jitter.astype(np.float32)
        if rng.random() < 0.50:
            output[:, 3:6] = np.clip(
                output[:, 3:6] + rng.normal(0.0, 0.02, output[:, 3:6].shape),
                0.0,
                1.0,
            )
        if rng.random() < 0.50:
            ratio = float(rng.uniform(0.0, 0.10))
            mask = rng.random(len(output)) < ratio
            if mask.any():
                output[mask] = output[0]
        return output


class ShapeNetCap3DDataset(Dataset):
    """Returns `(pos, colors, label)` for the legacy training scripts."""

    def __init__(
        self,
        csv_path: str | Path,
        ply_dir: str | Path,
        split: str | None = None,
        n_points: int = 1024,
        augment: bool = False,
        seed: int = 42,
        transform: Callable[[np.ndarray, np.random.Generator], np.ndarray] | None = None,
    ):
        self.csv_path = Path(csv_path)
        self.ply_dir = Path(ply_dir)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV absent: {self.csv_path}")
        if not self.ply_dir.exists():
            raise FileNotFoundError(f"Dossier PLY absent: {self.ply_dir}")

        frame = pd.read_csv(self.csv_path)
        self.file_column = _find_column(frame.columns.tolist(), FILE_COLUMNS, "fichier")
        self.label_column = _find_column(frame.columns.tolist(), LABEL_COLUMNS, "classe")
        if split is not None:
            if "split" not in frame.columns:
                raise ValueError("Le CSV doit contenir une colonne 'split'")
            frame = frame[frame["split"].astype(str).str.lower() == split.lower()]
        if frame.empty:
            raise ValueError(f"Aucun exemple pour split={split!r}")

        if self.label_column == "label_index":
            frame["_target"] = frame[self.label_column].astype(int)
            self.class_names = [
                str(value)
                for value in sorted(frame["_target"].unique().tolist())
            ]
        else:
            labels = frame[self.label_column].astype(str)
            classes = sorted(labels.unique().tolist())
            mapping = {label: index for index, label in enumerate(classes)}
            frame["_target"] = labels.map(mapping).astype(int)
            self.class_names = classes

        self.frame = frame.reset_index(drop=True)
        self.n_points = int(n_points)
        self.augment = bool(augment)
        self.seed = int(seed)
        self.transform = transform or PointCloudAugmenter()

    def __len__(self) -> int:
        return len(self.frame)

    def _resolve_path(self, raw_value: str) -> Path:
        raw_path = Path(str(raw_value))
        candidates = [raw_path, self.ply_dir / raw_path]
        if raw_path.suffix.lower() != ".ply":
            candidates.append(self.ply_dir / f"{raw_path}.ply")
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        raise FileNotFoundError(f"PLY introuvable pour {raw_value!r}")

    def _rng(self, index: int) -> np.random.Generator:
        if self.augment:
            seed = int(torch.randint(0, 2**31 - 1, (1,)).item())
        else:
            token = f"{self.seed}:{self.frame.iloc[index][self.file_column]}".encode()
            seed = int.from_bytes(hashlib.sha256(token).digest()[:8], "little")
        return np.random.default_rng(seed)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        row = self.frame.iloc[index]
        rng = self._rng(index)
        resolved = self._resolve_path(row[self.file_column])
        if _CACHE_ENABLED:
            key = str(resolved)
            raw = _RAW_CACHE.get(key)
            if raw is None:
                raw = load_ply(resolved)
                _RAW_CACHE[key] = raw
        else:
            raw = load_ply(resolved)
        points = normalize_xyz(sample_points(raw, self.n_points, rng))
        if self.augment:
            points = self.transform(points, rng)
        pos = torch.from_numpy(points[:, :3].astype(np.float32))
        colors = torch.from_numpy(points[:, 3:6].astype(np.float32))
        label = torch.tensor(int(row["_target"]), dtype=torch.long)
        return pos, colors, label


class ShapeNetVFLDataset(ShapeNetCap3DDataset):
    """Semantic alias for vertical federated experiments."""

# ============================================================
# Cell 6
# ============================================================
"""Graph primitives shared by ECC and MoNet."""


import torch
from torch import nn


def knn_indices(coordinates: torch.Tensor, k: int) -> torch.Tensor:
    if coordinates.ndim != 3 or coordinates.shape[1] != 3:
        raise ValueError("coordinates doit avoir la forme [B, 3, N]")
    n_points = coordinates.shape[2]
    if n_points < 2:
        raise ValueError("Au moins deux points sont nécessaires")
    effective_k = min(int(k), n_points - 1)
    with torch.no_grad():
        distances = torch.cdist(
            coordinates.detach().transpose(1, 2),
            coordinates.detach().transpose(1, 2),
        )
        return distances.topk(effective_k + 1, largest=False).indices[:, :, 1:]


def gather_neighbors(features: torch.Tensor, indices: torch.Tensor) -> torch.Tensor:
    batch, channels, n_points = features.shape
    k = indices.shape[-1]
    offsets = torch.arange(batch, device=features.device).view(batch, 1, 1) * n_points
    flat_indices = (indices + offsets).reshape(-1)
    flat = features.transpose(1, 2).contiguous().reshape(batch * n_points, channels)
    neighbors = flat[flat_indices].reshape(batch, n_points, k, channels)
    return neighbors.permute(0, 3, 1, 2).contiguous()


def edge_coordinates(coordinates: torch.Tensor, indices: torch.Tensor) -> torch.Tensor:
    neighbors = gather_neighbors(coordinates, indices)
    centers = coordinates.unsqueeze(-1).expand_as(neighbors)
    relative = neighbors - centers
    radius = torch.linalg.vector_norm(relative, dim=1, keepdim=True)
    return torch.cat([relative, radius], dim=1)


def combine_inputs(
    pos: torch.Tensor,
    colors: torch.Tensor | None,
    in_channels: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    if pos.ndim != 3 or pos.shape[-1] != 3:
        raise ValueError("pos doit avoir la forme [B, N, 3]")
    coordinates = pos.transpose(1, 2).contiguous()
    if int(in_channels) == 3:
        features = coordinates
    elif int(in_channels) == 6:
        if colors is None or colors.shape != pos.shape:
            raise ValueError("colors doit avoir la forme [B, N, 3]")
        features = torch.cat([pos, colors], dim=-1).transpose(1, 2).contiguous()
    else:
        raise ValueError("in_channels doit valoir 3 ou 6")
    return features, coordinates


class EdgeConditionedConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        hidden = max(16, out_channels // 2)
        self.messages = nn.Conv2d(in_channels, out_channels, 1, bias=False)
        self.filters = nn.Sequential(
            nn.Conv2d(4, hidden, 1),
            nn.ReLU(),
            nn.Conv2d(hidden, out_channels, 1),
            nn.Sigmoid(),
        )
        self.root = nn.Conv1d(in_channels, out_channels, 1, bias=False)
        self.norm = nn.BatchNorm1d(out_channels)

    def forward(
        self,
        features: torch.Tensor,
        coordinates: torch.Tensor,
        indices: torch.Tensor,
    ) -> torch.Tensor:
        neighbors = gather_neighbors(features, indices)
        filters = self.filters(edge_coordinates(coordinates, indices))
        output = (self.messages(neighbors) * filters).mean(dim=-1)
        return torch.relu(self.norm(output + self.root(features)))


class MoNetConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernels: int):
        super().__init__()
        self.kernels = int(kernels)
        self.means = nn.Parameter(torch.empty(self.kernels, 4))
        self.log_scales = nn.Parameter(torch.zeros(self.kernels, 4))
        self.weights = nn.Parameter(
            torch.empty(self.kernels, out_channels, in_channels)
        )
        self.root = nn.Conv1d(in_channels, out_channels, 1, bias=False)
        self.norm = nn.BatchNorm1d(out_channels)
        nn.init.uniform_(self.means, -0.5, 0.5)
        nn.init.xavier_uniform_(self.weights)

    def forward(
        self,
        features: torch.Tensor,
        coordinates: torch.Tensor,
        indices: torch.Tensor,
    ) -> torch.Tensor:
        neighbors = gather_neighbors(features, indices)
        pseudo = edge_coordinates(coordinates, indices)
        centered = pseudo.unsqueeze(1) - self.means.view(1, self.kernels, 4, 1, 1)
        scales = self.log_scales.exp().clamp_min(1e-4).view(
            1, self.kernels, 4, 1, 1
        )
        gaussian = torch.exp(-0.5 * ((centered / scales) ** 2).sum(dim=2))
        gaussian = gaussian / gaussian.sum(dim=-1, keepdim=True).clamp_min(1e-9)
        patches = torch.einsum("bmnk,bcnk->bmcn", gaussian, neighbors)
        messages = torch.einsum("bmcn,moc->bon", patches, self.weights)
        return torch.relu(self.norm(messages + self.root(features)))


"""ECC teacher and compressed student."""


import torch
from torch import nn



class _ECCBase(nn.Module):
    def __init__(
        self,
        num_classes: int,
        in_channels: int,
        widths: tuple[int, ...],
        embedding_dim: int,
        k: int,
        dropout: float,
    ):
        super().__init__()
        self.in_channels = int(in_channels)
        self.k = int(k)
        blocks = []
        current = self.in_channels
        for width in widths:
            blocks.append(EdgeConditionedConv(current, width))
            current = width
        self.blocks = nn.ModuleList(blocks)
        self.embedding_dim = int(embedding_dim)
        self.embedding_head = nn.Sequential(
            nn.Linear(current * 2, self.embedding_dim, bias=False),
            nn.BatchNorm1d(self.embedding_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        hidden = max(32, self.embedding_dim // 2)
        self.classifier = nn.Sequential(
            nn.Linear(self.embedding_dim, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, num_classes),
        )

    def get_embedding(
        self,
        pos: torch.Tensor,
        colors: torch.Tensor | None = None,
    ) -> torch.Tensor:
        features, coordinates = combine_inputs(pos, colors, self.in_channels)
        indices = knn_indices(coordinates, self.k)
        for block in self.blocks:
            features = block(features, coordinates, indices)
        pooled = torch.cat(
            [features.max(dim=2).values, features.mean(dim=2)],
            dim=1,
        )
        return self.embedding_head(pooled)

    def forward(
        self,
        pos: torch.Tensor,
        colors: torch.Tensor | None = None,
    ) -> torch.Tensor:
        return self.classifier(self.get_embedding(pos, colors))


class ECC(_ECCBase):
    def __init__(
        self,
        num_classes: int = 51,
        in_channels: int = 6,
        k: int = 16,
        dropout: float = 0.3,
    ):
        super().__init__(
            num_classes,
            in_channels,
            (64, 128, 256),
            256,
            k,
            dropout,
        )


class ECCStudent(_ECCBase):
    def __init__(
        self,
        num_classes: int = 51,
        in_channels: int = 6,
        k: int = 12,
        dropout: float = 0.2,
    ):
        super().__init__(
            num_classes,
            in_channels,
            (16, 32, 64),
            48,
            k,
            dropout,
        )


"""MoNet teacher and compressed student."""


import torch
from torch import nn



class _MoNetBase(nn.Module):
    def __init__(
        self,
        num_classes: int,
        in_channels: int,
        widths: tuple[int, ...],
        embedding_dim: int,
        k: int,
        kernels: int,
        dropout: float,
    ):
        super().__init__()
        self.in_channels = int(in_channels)
        self.k = int(k)
        blocks = []
        current = self.in_channels
        for width in widths:
            blocks.append(MoNetConv(current, width, kernels))
            current = width
        self.blocks = nn.ModuleList(blocks)
        self.embedding_dim = int(embedding_dim)
        self.embedding_head = nn.Sequential(
            nn.Linear(current * 2, self.embedding_dim, bias=False),
            nn.BatchNorm1d(self.embedding_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        hidden = max(32, self.embedding_dim // 2)
        self.classifier = nn.Sequential(
            nn.Linear(self.embedding_dim, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, num_classes),
        )

    def get_embedding(
        self,
        pos: torch.Tensor,
        colors: torch.Tensor | None = None,
    ) -> torch.Tensor:
        features, coordinates = combine_inputs(pos, colors, self.in_channels)
        indices = knn_indices(coordinates, self.k)
        for block in self.blocks:
            features = block(features, coordinates, indices)
        pooled = torch.cat(
            [features.max(dim=2).values, features.mean(dim=2)],
            dim=1,
        )
        return self.embedding_head(pooled)

    def forward(
        self,
        pos: torch.Tensor,
        colors: torch.Tensor | None = None,
    ) -> torch.Tensor:
        return self.classifier(self.get_embedding(pos, colors))


class MoNet(_MoNetBase):
    def __init__(
        self,
        num_classes: int = 51,
        in_channels: int = 6,
        k: int = 16,
        kernels: int = 8,
        dropout: float = 0.3,
    ):
        super().__init__(
            num_classes,
            in_channels,
            (48, 96, 192),
            256,
            k,
            kernels,
            dropout,
        )


class MoNetStudent(_MoNetBase):
    def __init__(
        self,
        num_classes: int = 51,
        in_channels: int = 6,
        k: int = 12,
        kernels: int = 4,
        dropout: float = 0.2,
    ):
        super().__init__(
            num_classes,
            in_channels,
            (12, 24, 48),
            48,
            k,
            kernels,
            dropout,
        )


"""Server fusion head used by vertical federated learning."""


import torch
from torch import nn


class VFLServerModel(nn.Module):
    def __init__(
        self,
        embedding_dim_a: int,
        embedding_dim_b: int,
        num_classes: int,
        hidden_dim: int = 256,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Linear(embedding_dim_a + embedding_dim_b, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, embedding_a: torch.Tensor, embedding_b: torch.Tensor) -> torch.Tensor:
        return self.classifier(torch.cat([embedding_a, embedding_b], dim=1))


"""ECC/MoNet model factory."""


from torch import nn



MODEL_NAMES = ("ecc", "ecc_student", "monet", "monet_student")


def build_model(
    name: str,
    num_classes: int = 51,
    in_channels: int = 6,
    **kwargs,
) -> nn.Module:
    normalized = str(name).lower().replace("-", "_")
    factories = {
        "ecc": ECC,
        "ecc_student": ECCStudent,
        "monet": MoNet,
        "monet_student": MoNetStudent,
    }
    if normalized not in factories:
        raise ValueError(f"Modèle inconnu {name!r}. Choix: {MODEL_NAMES}")
    return factories[normalized](
        num_classes=num_classes,
        in_channels=in_channels,
        **kwargs,
    )


def count_parameters(model: nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


__all__ = [
    "ECC",
    "ECCStudent",
    "MoNet",
    "MoNetStudent",
    "VFLServerModel",
    "MODEL_NAMES",
    "build_model",
    "count_parameters",
]

# ============================================================
# Cell 7
# ============================================================
"""Shared training, evaluation and reproducibility helpers."""


import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import confusion_matrix
from torch import nn
from torch.utils.data import DataLoader


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def resolve_device(name: str = "auto") -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(name)


def forward_batch(
    model: nn.Module,
    pos: torch.Tensor,
    colors: torch.Tensor,
    device: torch.device,
) -> torch.Tensor:
    return model(pos.to(device), colors.to(device))


def train_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    label_smoothing: float = 0.1,
) -> float:
    model.train()
    loss_fn = nn.CrossEntropyLoss(label_smoothing=float(label_smoothing))
    total = 0.0
    seen = 0
    for pos, colors, labels in loader:
        labels = labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        loss = loss_fn(forward_batch(model, pos, colors, device), labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        total += float(loss.item()) * len(labels)
        seen += len(labels)
    if seen == 0:
        raise ValueError("DataLoader d'entraînement vide")
    return total / seen


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    num_classes: int,
) -> dict[str, Any]:
    model.eval()
    loss_fn = nn.CrossEntropyLoss()
    total = 0.0
    labels_all: list[np.ndarray] = []
    predictions_all: list[np.ndarray] = []
    for pos, colors, labels in loader:
        labels = labels.to(device)
        logits = forward_batch(model, pos, colors, device)
        total += float(loss_fn(logits, labels).item()) * len(labels)
        labels_all.append(labels.cpu().numpy())
        predictions_all.append(logits.argmax(dim=1).cpu().numpy())
    if not labels_all:
        raise ValueError("DataLoader d'évaluation vide")
    truth = np.concatenate(labels_all)
    predictions = np.concatenate(predictions_all)
    matrix = confusion_matrix(truth, predictions, labels=np.arange(num_classes))
    support = matrix.sum(axis=1)
    per_class = np.divide(
        np.diag(matrix),
        support,
        out=np.full(num_classes, np.nan, dtype=float),
        where=support > 0,
    )
    return {
        "loss": total / len(truth),
        "accuracy": float(np.mean(truth == predictions)),
        "mean_class_accuracy": float(np.nanmean(per_class)),
        "per_class_accuracy": per_class.tolist(),
        "support": support.tolist(),
        "confusion_matrix": matrix.tolist(),
    }


def save_json(path: str | Path, payload: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

# ============================================================
# Cell 8
# ============================================================
pos = torch.randn(2, 256, 3); col = torch.rand(2, 256, 3)
for name in ('ecc', 'monet'):
    t = build_model(name, num_classes=NUM_CLASSES); s = build_model(f'{name}_student', num_classes=NUM_CLASSES)
    tp, sp = count_parameters(t), count_parameters(s)
    print(f'{name.upper():6s} sortie={tuple(t(pos, col).shape)} | teacher={tp:,} | student={sp:,} | ratio={tp/sp:.1f}x')

# ============================================================
# Cell 9
# ============================================================
"""Partie 1: centralized baseline training for ECC or MoNet."""


import argparse
import copy
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import DataLoader





@dataclass
class TrainingConfig:
    model_name: str = "ecc"
    csv_path: str = "data/subset_splits.csv"
    ply_dir: str = "data/ply_files"
    num_classes: int = 51
    n_points: int = 1024
    epochs: int = 100
    batch_size: int = 16
    num_workers: int = 4
    lr: float = 1e-3
    weight_decay: float = 1e-4
    patience: int = 20
    output_dir: str = "results/baseline"
    seed: int = 42
    device: str = "auto"


def train(config: TrainingConfig) -> tuple[torch.nn.Module, pd.DataFrame]:
    if config.model_name not in ("ecc", "monet"):
        raise ValueError("La baseline accepte seulement 'ecc' ou 'monet'")
    set_seed(config.seed)
    device = resolve_device(config.device)
    train_dataset = ShapeNetCap3DDataset(
        config.csv_path,
        config.ply_dir,
        split="train",
        n_points=config.n_points,
        augment=True,
        seed=config.seed,
    )
    val_dataset = ShapeNetCap3DDataset(
        config.csv_path,
        config.ply_dir,
        split="val",
        n_points=config.n_points,
        augment=False,
        seed=config.seed,
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=config.num_workers,
        drop_last=len(train_dataset) > config.batch_size,
        pin_memory=device.type == "cuda",
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=device.type == "cuda",
    )

    model = build_model(
        config.model_name,
        num_classes=config.num_classes,
        in_channels=6,
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.lr,
        weight_decay=config.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=max(1, config.epochs),
    )
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_json(output_dir / f"{config.model_name}_config.json", asdict(config))

    best_accuracy = -1.0
    best_state = copy.deepcopy(model.state_dict())
    stale_epochs = 0
    history = []
    print(
        f"Device={device} | modèle={config.model_name} | "
        f"paramètres={count_parameters(model):,}"
    )
    for epoch in range(1, config.epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, device)
        metrics = evaluate(model, val_loader, device, config.num_classes)
        row = {
            "epoch": epoch,
            "learning_rate": optimizer.param_groups[0]["lr"],
            "train_loss": train_loss,
            "val_loss": metrics["loss"],
            "val_accuracy": metrics["accuracy"],
            "val_mean_class_accuracy": metrics["mean_class_accuracy"],
        }
        history.append(row)
        torch.save(model.state_dict(), output_dir / f"{config.model_name}_last.pt")
        if metrics["accuracy"] > best_accuracy:
            best_accuracy = float(metrics["accuracy"])
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
            torch.save(best_state, output_dir / f"{config.model_name}_best.pt")
            save_json(
                output_dir / f"{config.model_name}_best_metrics.json",
                metrics,
            )
        else:
            stale_epochs += 1
        scheduler.step()
        print(
            f"Epoch {epoch:03d}/{config.epochs} "
            f"train_loss={train_loss:.4f} "
            f"val_acc={metrics['accuracy']:.4f} "
            f"val_mca={metrics['mean_class_accuracy']:.4f}"
        )
        pd.DataFrame(history).to_csv(
            output_dir / f"{config.model_name}_metrics.csv",
            index=False,
        )
        if stale_epochs >= config.patience:
            print(f"Early stopping après {epoch} époques")
            break
    model.load_state_dict(best_state)
    return model, pd.DataFrame(history)

# ============================================================
# Cell 10
# ============================================================
"""Partie 2A: manual horizontal federated learning with FedAvg."""


import argparse
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Subset





DOMAIN_CLASSES = {
    "furniture": {"table", "chair", "bed", "sofa", "bench", "bookshelf", "file_cabinet", "cabinet"},
    "transport": {"car", "airplane", "train", "bus", "motorbike", "bicycle", "watercraft", "rocket"},
    "technology": {"laptop", "telephone", "camera", "earphone", "keyboard", "display", "printer", "microphone", "remote"},
    "domestic": {"bottle", "bowl", "mug", "can", "knife", "jar", "basket", "rifle", "pistol", "lamp", "faucet", "stove", "washer", "dishwasher", "trash_bin", "mailbox", "birdhouse", "bag", "cap", "guitar", "piano"},
}


def normalize_label(label: str) -> str:
    return str(label).strip().lower().replace("-", "_").replace(" ", "_")


def partition_iid(labels: list[int], clients: int, seed: int) -> dict[str, list[int]]:
    rng = np.random.default_rng(seed)
    values = np.asarray(labels)
    result = {f"client_{index + 1}": [] for index in range(clients)}
    for label in sorted(set(values.tolist())):
        indices = np.flatnonzero(values == label)
        rng.shuffle(indices)
        for position, index in enumerate(indices):
            result[f"client_{position % clients + 1}"].append(int(index))
    return result


def partition_non_iid(raw_labels: list[str]) -> dict[str, list[int]]:
    clients = {name: [] for name in DOMAIN_CLASSES}
    owner = {
        label: client
        for client, classes in DOMAIN_CLASSES.items()
        for label in classes
    }
    unknown: dict[str, list[int]] = {}
    for index, raw_label in enumerate(raw_labels):
        label = normalize_label(raw_label)
        if label in owner:
            clients[owner[label]].append(index)
        else:
            unknown.setdefault(label, []).append(index)
    for label in sorted(unknown):
        smallest = min(clients, key=lambda name: len(clients[name]))
        clients[smallest].extend(unknown[label])
    return clients


def fedavg(
    states: list[dict[str, torch.Tensor]],
    sizes: list[int],
) -> dict[str, torch.Tensor]:
    if not states or len(states) != len(sizes):
        raise ValueError("États clients invalides")
    total = float(sum(sizes))
    largest = int(np.argmax(sizes))
    result = {}
    for key in states[0]:
        reference = states[0][key]
        if reference.is_floating_point() or reference.is_complex():
            accumulator = torch.zeros_like(reference)
            for state, size in zip(states, sizes):
                accumulator.add_(state[key], alpha=float(size) / total)
            result[key] = accumulator
        else:
            result[key] = states[largest][key].clone()
    return result


def local_train(
    global_model: torch.nn.Module,
    dataset: ShapeNetCap3DDataset,
    indices: list[int],
    batch_size: int,
    local_epochs: int,
    lr: float,
    device: torch.device,
) -> tuple[dict[str, torch.Tensor], int]:
    local_model = copy.deepcopy(global_model).to(device)
    loader = DataLoader(
        Subset(dataset, indices),
        batch_size=batch_size,
        shuffle=True,
        drop_last=len(indices) >= batch_size,
    )
    optimizer = torch.optim.Adam(local_model.parameters(), lr=lr)
    for _ in range(local_epochs):
        train_epoch(local_model, loader, optimizer, device)
    state = {
        key: tensor.detach().cpu().clone()
        for key, tensor in local_model.state_dict().items()
    }
    return state, len(indices)


def run_hfl(args: argparse.Namespace) -> None:
    set_seed(args.seed)
    device = resolve_device(args.device)
    train_dataset = ShapeNetCap3DDataset(
        args.csv_path,
        args.ply_dir,
        "train",
        args.n_points,
        True,
        args.seed,
    )
    val_dataset = ShapeNetCap3DDataset(
        args.csv_path,
        args.ply_dir,
        "val",
        args.n_points,
        False,
        args.seed,
    )
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    frame = train_dataset.frame
    if args.mode == "iid":
        partitions = partition_iid(
            frame["_target"].astype(int).tolist(),
            args.clients,
            args.seed,
        )
    else:
        label_column = "label" if "label" in frame.columns else train_dataset.label_column
        partitions = partition_non_iid(frame[label_column].astype(str).tolist())
    partitions = {name: indices for name, indices in partitions.items() if indices}

    global_model = build_model(
        args.model,
        num_classes=args.num_classes,
        in_channels=6,
    )
    rng = np.random.default_rng(args.seed)
    output_dir = Path(args.output_dir) / f"{args.model}_{args.mode}"
    output_dir.mkdir(parents=True, exist_ok=True)
    history = []
    best_accuracy = -1.0

    for round_index in range(1, args.rounds + 1):
        client_names = list(partitions)
        active_count = max(1, int(np.ceil(len(client_names) * args.participation)))
        active = rng.choice(client_names, size=active_count, replace=False).tolist()
        states = []
        sizes = []
        for client_name in active:
            state, size = local_train(
                copy.deepcopy(global_model),
                train_dataset,
                partitions[client_name],
                args.batch_size,
                args.local_epochs,
                args.lr,
                device,
            )
            states.append(state)
            sizes.append(size)
        global_model.load_state_dict(fedavg(states, sizes))
        metrics = evaluate(
            global_model.to(device),
            val_loader,
            device,
            args.num_classes,
        )
        row = {
            "round": round_index,
            "loss": metrics["loss"],
            "accuracy": metrics["accuracy"],
            "mean_class_accuracy": metrics["mean_class_accuracy"],
            "active_clients": ",".join(active),
            "absent_clients": ",".join(
                name for name in client_names if name not in active
            ),
            "client_sizes": json.dumps(sizes),
        }
        history.append(row)
        torch.save(global_model.state_dict(), output_dir / "last.pt")
        if metrics["accuracy"] > best_accuracy:
            best_accuracy = metrics["accuracy"]
            torch.save(global_model.state_dict(), output_dir / "best.pt")
            save_json(output_dir / "best_metrics.json", metrics)
        pd.DataFrame(history).to_csv(output_dir / "metrics.csv", index=False)
        print(
            f"Round {round_index:03d}/{args.rounds} "
            f"acc={metrics['accuracy']:.4f} "
            f"mca={metrics['mean_class_accuracy']:.4f} "
            f"clients={active}"
        )

# ============================================================
# Cell 11
# ============================================================
"""Partie 2B: vertical FL with private XYZ/RGB encoders and server fusion."""


import argparse
import copy
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import confusion_matrix
from torch import nn
from torch.utils.data import DataLoader





@torch.no_grad()
def evaluate_vfl(
    entity_a: nn.Module,
    entity_b: nn.Module,
    server: nn.Module,
    loader: DataLoader,
    device: torch.device,
    num_classes: int,
) -> dict:
    entity_a.eval()
    entity_b.eval()
    server.eval()
    loss_fn = nn.CrossEntropyLoss()
    total = 0.0
    truth_all = []
    prediction_all = []
    for pos, colors, labels in loader:
        pos = pos.to(device)
        colors = colors.to(device)
        labels = labels.to(device)
        logits = server(
            entity_a.get_embedding(pos),
            entity_b.get_embedding(colors),
        )
        total += float(loss_fn(logits, labels).item()) * len(labels)
        truth_all.append(labels.cpu().numpy())
        prediction_all.append(logits.argmax(dim=1).cpu().numpy())
    truth = np.concatenate(truth_all)
    predictions = np.concatenate(prediction_all)
    matrix = confusion_matrix(truth, predictions, labels=np.arange(num_classes))
    support = matrix.sum(axis=1)
    per_class = np.divide(
        np.diag(matrix),
        support,
        out=np.full(num_classes, np.nan),
        where=support > 0,
    )
    return {
        "loss": total / len(truth),
        "accuracy": float(np.mean(truth == predictions)),
        "mean_class_accuracy": float(np.nanmean(per_class)),
        "per_class_accuracy": per_class.tolist(),
        "support": support.tolist(),
        "confusion_matrix": matrix.tolist(),
    }


def run_vfl(args: argparse.Namespace) -> None:
    set_seed(args.seed)
    device = resolve_device(args.device)
    train_dataset = ShapeNetVFLDataset(
        args.csv_path,
        args.ply_dir,
        "train",
        args.n_points,
        True,
        args.seed,
    )
    val_dataset = ShapeNetVFLDataset(
        args.csv_path,
        args.ply_dir,
        "val",
        args.n_points,
        False,
        args.seed,
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=len(train_dataset) > args.batch_size,
        num_workers=args.num_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )

    # Entity A sees XYZ. Entity B receives RGB as its own private coordinates.
    entity_a = build_model(
        args.model,
        num_classes=args.num_classes,
        in_channels=3,
    ).to(device)
    entity_b = build_model(
        args.model,
        num_classes=args.num_classes,
        in_channels=3,
    ).to(device)
    server = VFLServerModel(
        entity_a.embedding_dim,
        entity_b.embedding_dim,
        args.num_classes,
    ).to(device)
    optimizer_a = torch.optim.Adam(entity_a.parameters(), lr=args.lr)
    optimizer_b = torch.optim.Adam(entity_b.parameters(), lr=args.lr)
    optimizer_server = torch.optim.Adam(server.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()
    output_dir = Path(args.output_dir) / args.model
    output_dir.mkdir(parents=True, exist_ok=True)
    history = []
    best_accuracy = -1.0
    best_state = None

    for epoch in range(1, args.epochs + 1):
        entity_a.train()
        entity_b.train()
        server.train()
        total_loss = 0.0
        seen = 0
        for pos, colors, labels in train_loader:
            pos = pos.to(device)
            colors = colors.to(device)
            labels = labels.to(device)
            optimizer_a.zero_grad(set_to_none=True)
            optimizer_b.zero_grad(set_to_none=True)
            optimizer_server.zero_grad(set_to_none=True)

            private_a = entity_a.get_embedding(pos)
            private_b = entity_b.get_embedding(colors)
            server_a = private_a.detach().requires_grad_(True)
            server_b = private_b.detach().requires_grad_(True)
            loss = loss_fn(server(server_a, server_b), labels)
            loss.backward()
            gradient_a = server_a.grad.detach().clone()
            gradient_b = server_b.grad.detach().clone()
            optimizer_server.step()

            private_a.backward(gradient_a)
            private_b.backward(gradient_b)
            torch.nn.utils.clip_grad_norm_(entity_a.parameters(), 1.0)
            torch.nn.utils.clip_grad_norm_(entity_b.parameters(), 1.0)
            optimizer_a.step()
            optimizer_b.step()
            total_loss += float(loss.item()) * len(labels)
            seen += len(labels)

        metrics = evaluate_vfl(
            entity_a,
            entity_b,
            server,
            val_loader,
            device,
            args.num_classes,
        )
        history.append(
            {
                "epoch": epoch,
                "train_loss": total_loss / seen,
                "val_loss": metrics["loss"],
                "val_accuracy": metrics["accuracy"],
                "val_mean_class_accuracy": metrics["mean_class_accuracy"],
            }
        )
        state = {
            "entity_a": entity_a.state_dict(),
            "entity_b": entity_b.state_dict(),
            "server": server.state_dict(),
            "model": args.model,
            "num_classes": args.num_classes,
        }
        torch.save(state, output_dir / "last.pt")
        if metrics["accuracy"] > best_accuracy:
            best_accuracy = metrics["accuracy"]
            best_state = copy.deepcopy(state)
            torch.save(best_state, output_dir / "best.pt")
            save_json(output_dir / "best_metrics.json", metrics)
        pd.DataFrame(history).to_csv(output_dir / "metrics.csv", index=False)
        print(
            f"Epoch {epoch:03d}/{args.epochs} "
            f"acc={metrics['accuracy']:.4f} "
            f"mca={metrics['mean_class_accuracy']:.4f}"
        )

# ============================================================
# Cell 12
# ============================================================
"""Partie 3: knowledge distillation from ECC/MoNet teachers to students."""


import argparse
import copy
from pathlib import Path

import pandas as pd
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader





STUDENT_BY_TEACHER = {
    "ecc": "ecc_student",
    "monet": "monet_student",
}


def distillation_loss(
    student_logits: torch.Tensor,
    teacher_logits: torch.Tensor,
    labels: torch.Tensor,
    alpha: float,
    temperature: float,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    tau = float(temperature)
    cross_entropy = F.cross_entropy(student_logits, labels)
    teacher_probabilities = F.softmax(teacher_logits.detach() / tau, dim=1)
    student_log_probabilities = F.log_softmax(student_logits / tau, dim=1)
    kl = F.kl_div(
        student_log_probabilities,
        teacher_probabilities,
        reduction="batchmean",
    )
    total = (1.0 - float(alpha)) * cross_entropy + float(alpha) * tau * tau * kl
    return total, cross_entropy, kl


def load_teacher(
    name: str,
    checkpoint_path: str | Path,
    num_classes: int,
    device: torch.device,
) -> nn.Module:
    teacher = build_model(name, num_classes=num_classes, in_channels=6).to(device)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        checkpoint = checkpoint["model_state_dict"]
    teacher.load_state_dict(checkpoint)
    teacher.eval()
    for parameter in teacher.parameters():
        parameter.requires_grad_(False)
    return teacher


def train_student(
    args: argparse.Namespace,
    alpha: float,
    temperature: float,
    suffix: str,
) -> dict:
    set_seed(args.seed)
    device = resolve_device(args.device)
    train_dataset = ShapeNetCap3DDataset(
        args.csv_path,
        args.ply_dir,
        "train",
        args.n_points,
        True,
        args.seed,
    )
    val_dataset = ShapeNetCap3DDataset(
        args.csv_path,
        args.ply_dir,
        "val",
        args.n_points,
        False,
        args.seed,
    )
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        drop_last=len(train_dataset) > args.batch_size,
        num_workers=args.num_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
    )
    teacher = load_teacher(
        args.teacher,
        args.teacher_ckpt,
        args.num_classes,
        device,
    )
    student = build_model(
        STUDENT_BY_TEACHER[args.teacher],
        num_classes=args.num_classes,
        in_channels=6,
    ).to(device)
    # Le teacher est gele (requires_grad=False) : on compte TOUS ses parametres
    # pour comparer les tailles d'architecture, sinon count_parameters renvoie 0.
    teacher_parameters = int(sum(p.numel() for p in teacher.parameters()))
    student_parameters = count_parameters(student)
    if student_parameters * 4 > teacher_parameters:
        raise ValueError(
            f"Student trop grand: teacher={teacher_parameters}, student={student_parameters}"
        )
    optimizer = torch.optim.Adam(student.parameters(), lr=args.lr)
    output_dir = Path(args.output_dir) / args.teacher / suffix
    output_dir.mkdir(parents=True, exist_ok=True)
    history = []
    best_accuracy = -1.0
    best_state = copy.deepcopy(student.state_dict())

    for epoch in range(1, args.epochs + 1):
        student.train()
        total_loss = 0.0
        total_ce = 0.0
        total_kl = 0.0
        seen = 0
        for pos, colors, labels in train_loader:
            pos = pos.to(device)
            colors = colors.to(device)
            labels = labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            with torch.no_grad():
                teacher_logits = teacher(pos, colors)
            student_logits = student(pos, colors)
            loss, ce, kl = distillation_loss(
                student_logits,
                teacher_logits,
                labels,
                alpha,
                temperature,
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(student.parameters(), 1.0)
            optimizer.step()
            total_loss += float(loss.item()) * len(labels)
            total_ce += float(ce.item()) * len(labels)
            total_kl += float(kl.item()) * len(labels)
            seen += len(labels)
        metrics = evaluate(student, val_loader, device, args.num_classes)
        history.append(
            {
                "epoch": epoch,
                "loss": total_loss / seen,
                "cross_entropy": total_ce / seen,
                "kl_divergence": total_kl / seen,
                "val_accuracy": metrics["accuracy"],
                "val_mean_class_accuracy": metrics["mean_class_accuracy"],
                "alpha": alpha,
                "temperature": temperature,
            }
        )
        if metrics["accuracy"] > best_accuracy:
            best_accuracy = metrics["accuracy"]
            best_state = copy.deepcopy(student.state_dict())
            torch.save(best_state, output_dir / "best.pt")
            save_json(output_dir / "best_metrics.json", metrics)
        torch.save(student.state_dict(), output_dir / "last.pt")
        pd.DataFrame(history).to_csv(output_dir / "metrics.csv", index=False)
        print(
            f"{args.teacher} alpha={alpha} tau={temperature} "
            f"epoch={epoch:03d} acc={metrics['accuracy']:.4f}"
        )
    return {
        "teacher": args.teacher,
        "student": STUDENT_BY_TEACHER[args.teacher],
        "alpha": alpha,
        "temperature": temperature,
        "accuracy": best_accuracy,
        "teacher_parameters": teacher_parameters,
        "student_parameters": student_parameters,
        "compression_ratio": teacher_parameters / student_parameters,
    }


def run_distill(args: argparse.Namespace) -> None:
    if not args.grid_search:
        train_student(
            args,
            args.alpha,
            args.temperature,
            f"alpha_{args.alpha}_tau_{args.temperature}",
        )
        return
    rows = []
    for alpha in (0.0, 0.3, 0.5, 0.7, 1.0):
        rows.append(
            train_student(
                args,
                alpha,
                args.temperature,
                f"alpha_{alpha}_tau_{args.temperature}",
            )
        )
    for temperature in (1.0, 2.0, 4.0, 8.0):
        rows.append(
            train_student(
                args,
                args.alpha,
                temperature,
                f"alpha_{args.alpha}_tau_{temperature}",
            )
        )
    output = Path(args.output_dir) / args.teacher / "grid_search.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output, index=False)

# ============================================================
# Cell 13
# ============================================================
if QUICK_MODE:
    N_POINTS = 64
    BATCH    = 8
    WORKERS  = 0
    EP_BASE  = 1
    ROUNDS   = 1
    LOCAL_EP = 1
else:
    N_POINTS = 1024
    BATCH    = 16
    WORKERS  = 2
    EP_BASE  = 25   # epoques baseline / VFL / distillation
    ROUNDS   = 15   # rondes federees
    LOCAL_EP = 3    # epoques locales federees
DEVICE   = 'auto'
print('mode:', 'rapide' if QUICK_MODE else 'complet', '| classes:', NUM_CLASSES, '| points:', N_POINTS, '| epochs:', EP_BASE)

# ============================================================
# Cell 14
# ============================================================
for m in ('ecc', 'monet'):
    cfg = TrainingConfig(model_name=m, csv_path=CSV, ply_dir=PLY, num_classes=NUM_CLASSES,
                         n_points=N_POINTS, epochs=EP_BASE, batch_size=BATCH, num_workers=WORKERS,
                         output_dir='results/baseline', device=DEVICE)
    train(cfg)

# ============================================================
# Cell 15
# ============================================================
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
for m in ('ecc', 'monet'):
    h = pd.read_csv(f'results/baseline/{m}_metrics.csv')
    ax[0].plot(h['epoch'], h['train_loss'], marker='.', label=m.upper())
    ax[1].plot(h['epoch'], h['val_accuracy'], marker='.', label=m.upper())
ax[0].set_title('Perte entrainement'); ax[0].set_xlabel('epoque'); ax[0].set_ylabel('loss'); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].set_title('Accuracy validation'); ax[1].set_xlabel('epoque'); ax[1].set_ylabel('accuracy'); ax[1].legend(); ax[1].grid(alpha=.3)
plt.tight_layout(); plt.show()

# ============================================================
# Cell 16
# ============================================================
for m in ('ecc', 'monet'):
    args = types.SimpleNamespace(model=m, mode='iid', csv_path=CSV, ply_dir=PLY,
        num_classes=NUM_CLASSES, n_points=N_POINTS, clients=4, rounds=ROUNDS, local_epochs=LOCAL_EP,
        batch_size=BATCH, lr=1e-3, participation=1.0, output_dir='results/hfl', seed=42, device=DEVICE)
    run_hfl(args)

# ============================================================
# Cell 17
# ============================================================
for m in ('ecc', 'monet'):
    args = types.SimpleNamespace(model=m, mode='non_iid', csv_path=CSV, ply_dir=PLY,
        num_classes=NUM_CLASSES, n_points=N_POINTS, clients=4, rounds=ROUNDS, local_epochs=LOCAL_EP,
        batch_size=BATCH, lr=1e-3, participation=0.75, output_dir='results/hfl', seed=42, device=DEVICE)
    run_hfl(args)

# ============================================================
# Cell 18
# ============================================================
for m in ('ecc', 'monet'):
    args = types.SimpleNamespace(model=m, csv_path=CSV, ply_dir=PLY, num_classes=NUM_CLASSES,
        n_points=N_POINTS, epochs=EP_BASE, batch_size=BATCH, num_workers=WORKERS, lr=1e-3,
        output_dir='results/vfl', seed=42, device=DEVICE)
    run_vfl(args)

# ============================================================
# Cell 19
# ============================================================
for m in ('ecc', 'monet'):
    args = types.SimpleNamespace(teacher=m, teacher_ckpt=f'results/baseline/{m}_best.pt',
        csv_path=CSV, ply_dir=PLY, num_classes=NUM_CLASSES, n_points=N_POINTS, epochs=EP_BASE,
        batch_size=BATCH, num_workers=WORKERS, lr=1e-3, alpha=0.5, temperature=4.0,
        grid_search=False, output_dir='results/distillation', seed=42, device=DEVICE)
    run_distill(args)

# ============================================================
# Cell 20
# ============================================================
ORDER = ['C1 Centralise', 'C2 FedAvg IID', 'C3 FedAvg non-IID', 'VFL XYZ/RGB', 'C4 Distillation']
CONFIGS = [
 ('C1 Centralise','ECC','results/baseline/ecc_best_metrics.json'),
 ('C1 Centralise','MONET','results/baseline/monet_best_metrics.json'),
 ('C2 FedAvg IID','ECC','results/hfl/ecc_iid/best_metrics.json'),
 ('C2 FedAvg IID','MONET','results/hfl/monet_iid/best_metrics.json'),
 ('C3 FedAvg non-IID','ECC','results/hfl/ecc_non_iid/best_metrics.json'),
 ('C3 FedAvg non-IID','MONET','results/hfl/monet_non_iid/best_metrics.json'),
 ('VFL XYZ/RGB','ECC','results/vfl/ecc/best_metrics.json'),
 ('VFL XYZ/RGB','MONET','results/vfl/monet/best_metrics.json'),
 ('C4 Distillation','ECC','results/distillation/ecc/alpha_0.5_tau_4.0/best_metrics.json'),
 ('C4 Distillation','MONET','results/distillation/monet/alpha_0.5_tau_4.0/best_metrics.json'),
]
def _load(p):
    with open(p, encoding='utf-8') as handle:
        return json.load(handle)
    
def _metric(data, key):
    value = data.get(key)
    return round(float(value), 4) if value is not None else None
rows = []
for cfg, mdl, p in CONFIGS:
    d = _load(p)
    rows.append({'config': cfg, 'model': mdl,
                 'accuracy': _metric(d, 'accuracy') if d else None,
                 'mca': _metric(d, 'mean_class_accuracy') if d else None})
res = pd.DataFrame(rows); os.makedirs('output', exist_ok=True); res.to_csv('output/summary.csv', index=False)
acc = res.pivot(index='config', columns='model', values='accuracy').reindex(ORDER)
mca = res.pivot(index='config', columns='model', values='mca').reindex(ORDER)
print('===== Accuracy globale ====='); display(acc)
print('===== Accuracy moyenne par classe ====='); display(mca)
fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
acc.plot(kind='bar', ax=ax[0], rot=20, edgecolor='black'); ax[0].set_title('Accuracy globale'); ax[0].set_ylim(0,1.05); ax[0].grid(axis='y', alpha=.3)
mca.plot(kind='bar', ax=ax[1], rot=20, edgecolor='black'); ax[1].set_title('Accuracy moyenne par classe'); ax[1].set_ylim(0,1.05); ax[1].grid(axis='y', alpha=.3)
for a in ax:
    for c in a.containers: a.bar_label(c, fmt='%.2f', fontsize=7, padding=2)
plt.tight_layout(); plt.show()
print('\n===== Nombre de parametres (compression par distillation) =====')
for name in ('ecc', 'monet'):
    tp = count_parameters(build_model(name, num_classes=NUM_CLASSES))
    sp = count_parameters(build_model(f'{name}_student', num_classes=NUM_CLASSES))
    print(f'{name.upper():6s} teacher={tp:,}  student={sp:,}  ratio={tp/sp:.1f}x')
