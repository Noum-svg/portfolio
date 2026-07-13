# ============================================================
# Cell 1
# ============================================================
%pip install requests beautifulsoup4 torch -q

# ============================================================
# Cell 2
# ============================================================
import math
import random
import re
from collections import Counter, defaultdict

import requests
from bs4 import BeautifulSoup
import torch

SEED = 42
random.seed(SEED)
torch.manual_seed(SEED)

print('torch:', torch.__version__)

# ============================================================
# Cell 3
# ============================================================
# Vocabulaire impose par le TP
# V = {^, $, space, a..z}
VOCAB = ['^', '$', ' '] + [chr(c) for c in range(ord('a'), ord('z') + 1)]
V = len(VOCAB)
stoi = {ch: i for i, ch in enumerate(VOCAB)}
itos = {i: ch for ch, i in stoi.items()}

print('Taille vocabulaire =', V)
print('Debut vocab:', VOCAB[:6], '...')

# ============================================================
# Cell 4
# ============================================================
def fetch_text(url: str, max_chars: int = 300000, timeout: int = 20) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (MarkovTPBot/1.0)'
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get('Content-Type', '').lower()
    if 'html' in content_type:
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = [p.get_text(' ', strip=True) for p in soup.find_all('p')]
        text = ' '.join(paragraphs)
    else:
        text = response.text

    return text[:max_chars]

# ============================================================
# Cell 5
# ============================================================
def preprocess_text(raw_text: str) -> str:
    # lowercase
    t = raw_text.lower()
    # keep only a-z and spaces
    t = re.sub(r'[^a-z\s]+', ' ', t)
    # collapse multiple spaces
    t = re.sub(r'\s+', ' ', t).strip()

    if len(t) == 0:
        raise ValueError('Texte vide apres preprocessing.')

    return '^' + t + '$'

# ============================================================
# Cell 6
# ============================================================
# Choix de sources (meme auteur pour train/test si possible)
train_url = 'https://www.gutenberg.org/files/11/11-0.txt'      # Alice in Wonderland
test_same_url = 'https://www.gutenberg.org/files/12/12-0.txt'   # Through the Looking-Glass
test_diff_url = 'https://www.gutenberg.org/files/1342/1342-0.txt'  # Pride and Prejudice

fallback_train = 'Alice was beginning to get very tired of sitting by her sister on the bank.'
fallback_same = 'It was a bright cold day in April and the clocks were striking thirteen.'
fallback_diff = 'Financial markets move rapidly when uncertainty rises in the global economy.'

try:
    raw_train = fetch_text(train_url)
except Exception as e:
    print('Fetch train failed, fallback used:', e)
    raw_train = fallback_train

try:
    raw_same = fetch_text(test_same_url)
except Exception as e:
    print('Fetch test_same failed, fallback used:', e)
    raw_same = fallback_same

try:
    raw_diff = fetch_text(test_diff_url)
except Exception as e:
    print('Fetch test_diff failed, fallback used:', e)
    raw_diff = fallback_diff

train_text = preprocess_text(raw_train)
test_same_text = preprocess_text(raw_same)
test_diff_text = preprocess_text(raw_diff)
test_gibberish_text = preprocess_text('zxqv qqq jjj zzz qzxv qjjxv zq')

print('train length:', len(train_text))
print('test_same length:', len(test_same_text))
print('test_diff length:', len(test_diff_text))

# ============================================================
# Cell 7
# ============================================================
def build_order1_model(clean_text: str, vocab: list[str], alpha: float = 1.0):
    stoi_local = {ch: i for i, ch in enumerate(vocab)}
    n = len(vocab)

    counts = torch.zeros((n, n), dtype=torch.float64)
    for a, b in zip(clean_text[:-1], clean_text[1:]):
        if a in stoi_local and b in stoi_local:
            counts[stoi_local[a], stoi_local[b]] += 1.0

    # Laplace smoothing
    counts_smoothed = counts + alpha
    P = counts_smoothed / counts_smoothed.sum(dim=1, keepdim=True)
    return P, counts

# ============================================================
# Cell 8
# ============================================================
P1, C1 = build_order1_model(train_text, VOCAB, alpha=1.0)
row_sums = P1.sum(dim=1)
print('shape P1:', tuple(P1.shape))
print('Min row sum:', float(row_sums.min()), 'Max row sum:', float(row_sums.max()))
print('All rows approx 1:', bool(torch.allclose(row_sums, torch.ones_like(row_sums), atol=1e-10)))

# ============================================================
# Cell 9
# ============================================================
def top_transitions(counts: torch.Tensor, vocab: list[str], k: int = 10):
    n = counts.shape[0]
    flat = counts.flatten()
    vals, idx = torch.topk(flat, k=min(k, flat.numel()))
    out = []
    for v, i in zip(vals.tolist(), idx.tolist()):
        r = i // n
        c = i % n
        out.append((vocab[r], vocab[c], int(v)))
    return out

print('Top 10 transitions (x -> y, count):')
for x, y, c in top_transitions(C1, VOCAB, k=10):
    print(f'{repr(x)} -> {repr(y)} : {c}')

# ============================================================
# Cell 10
# ============================================================
def log_likelihood_order1(clean_text: str, P: torch.Tensor, stoi_local: dict[str, int]) -> float:
    ll = 0.0
    for a, b in zip(clean_text[:-1], clean_text[1:]):
        if a in stoi_local and b in stoi_local:
            ll += math.log(float(P[stoi_local[a], stoi_local[b]]))
    return ll

def perplexity_from_ll(ll: float, n_tokens: int) -> float:
    if n_tokens <= 0:
        return float('inf')
    return math.exp(-ll / n_tokens)

def evaluate_order1(clean_text: str, P: torch.Tensor, stoi_local: dict[str, int]):
    ll = log_likelihood_order1(clean_text, P, stoi_local)
    n = max(1, len(clean_text) - 1)
    ppl = perplexity_from_ll(ll, n)
    return ll, ppl

# ============================================================
# Cell 11
# ============================================================
scores = {}
scores['train'] = evaluate_order1(train_text, P1, stoi)
scores['test_same_author'] = evaluate_order1(test_same_text, P1, stoi)
scores['test_diff_author'] = evaluate_order1(test_diff_text, P1, stoi)
scores['gibberish'] = evaluate_order1(test_gibberish_text, P1, stoi)

for name, (ll, ppl) in scores.items():
    print(f'{name:20s} | log-likelihood = {ll:12.2f} | perplexity = {ppl:10.4f}')

# ============================================================
# Cell 12
# ============================================================
def sample_next(probs: torch.Tensor, top_k: int | None = None) -> int:
    probs = probs.clone().to(dtype=torch.float64)

    if top_k is not None and top_k > 0 and top_k < probs.numel():
        vals, idxs = torch.topk(probs, k=top_k)
        vals = vals / vals.sum()
        pick = torch.multinomial(vals, num_samples=1).item()
        return int(idxs[pick].item())

    return int(torch.multinomial(probs, num_samples=1).item())

def generate_order1(P: torch.Tensor, vocab: list[str], stoi_local: dict[str, int],
                    max_len: int = 300, mode: str = 'sample', top_k: int = 5) -> str:
    cur = '^'
    out = []

    for _ in range(max_len):
        probs = P[stoi_local[cur]]
        if mode == 'greedy':
            nxt_idx = int(torch.argmax(probs).item())
        elif mode == 'topk':
            nxt_idx = sample_next(probs, top_k=top_k)
        else:
            nxt_idx = sample_next(probs, top_k=None)

        nxt = vocab[nxt_idx]
        if nxt == '$':
            break

        out.append(nxt)
        cur = nxt

    return ''.join(out).strip()

# ============================================================
# Cell 13
# ============================================================
print('Sample 1 (full sampling):')
print(generate_order1(P1, VOCAB, stoi, max_len=250, mode='sample'))
print('\nSample 2 (top-k=5):')
print(generate_order1(P1, VOCAB, stoi, max_len=250, mode='topk', top_k=5))
print('\nSample 3 (greedy):')
print(generate_order1(P1, VOCAB, stoi, max_len=250, mode='greedy'))

# ============================================================
# Cell 14
# ============================================================
def prepare_for_order_n(raw_text: str, n: int) -> str:
    base = preprocess_text(raw_text)
    # remplacer le seul '^' par n fois '^' pour initialiser le contexte
    return ('^' * n) + base[1:]

def build_order_n_model(clean_text_n: str, vocab: list[str], n: int, alpha: float = 1.0):
    counts = defaultdict(Counter)

    for i in range(len(clean_text_n) - n):
        ctx = clean_text_n[i:i+n]
        nxt = clean_text_n[i+n]
        if all(ch in vocab for ch in ctx) and nxt in vocab:
            counts[ctx][nxt] += 1

    # distributions avec Laplace smoothing
    probs = {}
    for ctx, ctr in counts.items():
        total = sum(ctr.values()) + alpha * len(vocab)
        dist = {ch: (ctr.get(ch, 0) + alpha) / total for ch in vocab}
        probs[ctx] = dist

    return probs, counts

def get_dist_for_context(model_probs: dict, ctx: str, vocab: list[str]):
    # contexte jamais vu => distribution uniforme
    if ctx not in model_probs:
        u = 1.0 / len(vocab)
        return {ch: u for ch in vocab}
    return model_probs[ctx]

# ============================================================
# Cell 15
# ============================================================
def score_order_n(clean_text_n: str, model_probs: dict, vocab: list[str], n: int):
    ll = 0.0
    steps = 0
    for i in range(len(clean_text_n) - n):
        ctx = clean_text_n[i:i+n]
        nxt = clean_text_n[i+n]
        dist = get_dist_for_context(model_probs, ctx, vocab)
        ll += math.log(dist[nxt])
        steps += 1
    ppl = perplexity_from_ll(ll, max(1, steps))
    return ll, ppl

def generate_order_n(model_probs: dict, vocab: list[str], n: int,
                     max_len: int = 300, mode: str = 'sample', top_k: int = 5):
    ctx = '^' * n
    out = []

    for _ in range(max_len):
        dist = get_dist_for_context(model_probs, ctx, vocab)
        chars = list(dist.keys())
        probs = torch.tensor([dist[ch] for ch in chars], dtype=torch.float64)

        if mode == 'greedy':
            idx = int(torch.argmax(probs).item())
        elif mode == 'topk':
            idx = sample_next(probs, top_k=top_k)
        else:
            idx = sample_next(probs)

        nxt = chars[idx]
        if nxt == '$':
            break

        out.append(nxt)
        ctx = ctx[1:] + nxt

    return ''.join(out).strip()

# ============================================================
# Cell 16
# ============================================================
n = 3
train_n = prepare_for_order_n(raw_train, n)
same_n = prepare_for_order_n(raw_same, n)
diff_n = prepare_for_order_n(raw_diff, n)

P3, C3 = build_order_n_model(train_n, VOCAB, n=n, alpha=1.0)
print('Nombre de contextes observes (ordre 3):', len(P3))

ll_train_3, ppl_train_3 = score_order_n(train_n, P3, VOCAB, n)
ll_same_3, ppl_same_3 = score_order_n(same_n, P3, VOCAB, n)
ll_diff_3, ppl_diff_3 = score_order_n(diff_n, P3, VOCAB, n)

print(f'Order-3 train perplexity: {ppl_train_3:.4f}')
print(f'Order-3 same  perplexity: {ppl_same_3:.4f}')
print(f'Order-3 diff  perplexity: {ppl_diff_3:.4f}')

print('\nGeneration ordre-3 (top-k=5):')
print(generate_order_n(P3, VOCAB, n=3, max_len=250, mode='topk', top_k=5))

# ============================================================
# Cell 17
# ============================================================
ll_train_1, ppl_train_1 = evaluate_order1(train_text, P1, stoi)
ll_same_1, ppl_same_1 = evaluate_order1(test_same_text, P1, stoi)
ll_diff_1, ppl_diff_1 = evaluate_order1(test_diff_text, P1, stoi)

print('Perplexity comparison:')
print(f'Order-1 train={ppl_train_1:.4f} | same={ppl_same_1:.4f} | diff={ppl_diff_1:.4f}')
print(f'Order-3 train={ppl_train_3:.4f} | same={ppl_same_3:.4f} | diff={ppl_diff_3:.4f}')

print('\nInterpretation attendue:')
print('- Perplexity plus basse sur train/same author que sur different author.')
print('- Ordre 3 tend a mieux capturer le contexte local, mais demande plus de donnees.')
