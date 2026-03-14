# federated/accountant.py
"""
RDP accountant with privacy amplification (Poisson subsampling) for the sampled Gaussian mechanism.

Functions provided:
 - compute_eps_from_sigma(sigma, rounds, delta)        # full-participation (sigma = noise multiplier)
 - compute_eps_fullparticipation(clip_norm, sigma, rounds, delta)
 - compute_eps_poisson_subsampled(sigma, q, rounds, delta)

Notes:
 - We treat 'sigma' as the noise multiplier where noise std = sigma * clip_norm.
 - For the accountant we assume sensitivity = 1 (i.e., you clipped updates to norm C, then used noise std = sigma * C).
   The accountant therefore takes sigma (the multiplier) directly.
 - Poisson subsampling is assumed when using compute_eps_poisson_subsampled (each client independently participates with probability q).
 - The implementation follows the standard RDP formulas used by TensorFlow-Privacy / Opacus:
     rdp_subsampled(alpha) = log(A_alpha) / (alpha - 1)
   where A_alpha = sum_{j=0}^alpha binom(alpha, j) q^j (1-q)^(alpha-j) * exp( j*(j-1) / (2*sigma^2) )
   (we compute log(A_alpha) using log-sum-exp to preserve stability).
"""

import math
import numpy as np
from typing import Tuple

# ------------------- Low-level helpers -------------------
def _log_comb(n: int, k: int) -> float:
    """Log of binomial coefficient nCk."""
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)

def _logsumexp(a: np.ndarray) -> float:
    """Stable log-sum-exp for numpy array."""
    a_max = np.max(a)
    return a_max + math.log(np.sum(np.exp(a - a_max)))

# ------------------- RDP for subsampled Gaussian mech -------------------
def _log_a_subsampled_gaussian(alpha: int, q: float, sigma: float) -> float:
    """
    Compute log(A_alpha) for Poisson subsampled Gaussian mechanism (integer alpha >= 2).
    A_alpha = sum_{j=0}^alpha binom(alpha, j) q^j (1-q)^(alpha-j) * exp( j*(j-1) / (2*sigma^2) )
    We return log(A_alpha).
    """
    if q == 0:
        return -float("inf")  # log(0)
    if q == 1.0:
        # No subsampling; A_alpha = exp(alpha*(alpha-1)/(2*sigma^2))
        return float(alpha * (alpha - 1) / (2.0 * (sigma ** 2)))

    terms = []
    # compute terms in log-space: log binom + j*log(q) + (alpha-j)*log(1-q) + j*(j-1)/(2*sigma^2)
    log_q = math.log(q)
    log_1_q = math.log(1.0 - q)
    for j in range(0, alpha + 1):
        # log binomial
        log_binom = _log_comb(alpha, j)
        # exponent term from Gaussian moment: j*(j-1)/(2*sigma^2)
        gauss_term = float((j * (j - 1)) / (2.0 * (sigma ** 2)))
        # full log-term
        log_term = log_binom + j * log_q + (alpha - j) * log_1_q + gauss_term
        terms.append(log_term)
    terms = np.array(terms, dtype=float)
    return _logsumexp(terms)

def _rdp_subsampled_gaussian(q: float, sigma: float, alpha: int) -> float:
    """
    RDP for subsampled Gaussian mechanism at order alpha.
    Returns RDP_(alpha).
    """
    if sigma <= 0:
        return float("inf")
    if q == 1.0:
        # Full participation reduces to plain Gaussian RDP:
        return float(alpha) / (2.0 * (sigma ** 2))
    if q == 0.0:
        return 0.0

    # Compute log(A_alpha)
    log_a = _log_a_subsampled_gaussian(alpha, q, sigma)
    # RDP = log(A_alpha) / (alpha - 1)
    return float(log_a / (alpha - 1.0))

# ------------------- Conversion utilities -------------------
def _rdp_compose(rdps: np.ndarray) -> float:
    """Linear composition: sum of RDPs"""
    return float(np.sum(rdps))

def _rdp_to_eps(rdp: float, alpha: int, delta: float) -> float:
    """
    Convert RDP value at order alpha to (epsilon, delta) guarantee.
    epsilon = rdp + log(1/delta) / (alpha - 1)
    """
    return float(rdp + (math.log(1.0 / delta) / (alpha - 1.0)))

# ------------------- Public API -------------------
def compute_eps_from_sigma(sigma: float, rounds: int, delta: float, alphas: np.ndarray = None) -> Tuple[float, int]:
    """
    Compute epsilon assuming full participation (q = 1).
    sigma: noise multiplier (std = sigma * clip_norm)
    rounds: number of compositions (rounds)
    delta: target delta
    alphas: array of alpha (Rényi orders) to search over (optional)
    Returns (epsilon, best_alpha)
    """
    if alphas is None:
        alphas = np.arange(2, 512)
    best_eps = float("inf")
    best_a = None
    for a in alphas:
        rdp_round = float(a) / (2.0 * (sigma ** 2))  # Gaussian RDP
        rdp_total = rdp_round * rounds
        eps = _rdp_to_eps(rdp_total, int(a), delta)
        if eps < best_eps:
            best_eps = eps
            best_a = int(a)
    return best_eps, best_a

def compute_eps_fullparticipation(clip_norm: float, sigma_multiplier: float, rounds: int, delta: float) -> Tuple[float, int]:
    """
    Convenience wrapper: clip_norm is not used explicitly because accountant works with sigma multiplier.
    Pass sigma_multiplier = noise_std / clip_norm.
    """
    return compute_eps_from_sigma(sigma_multiplier, rounds, delta)

def compute_eps_poisson_subsampled(sigma: float, q: float, rounds: int, delta: float, alphas: np.ndarray = None) -> Tuple[float, int]:
    """
    Compute epsilon for Poisson subsampled Gaussian mechanism:
     - sigma: noise multiplier (std = sigma * clip_norm)
     - q: subsampling probability per round (clients_per_round / total_clients)
     - rounds: number of compositions
     - delta: target delta
    Returns (epsilon, best_alpha)
    """
    if q <= 0.0:
        return 0.0, 2
    if q >= 1.0:
        return compute_eps_from_sigma(sigma, rounds, delta, alphas)

    if alphas is None:
        alphas = np.arange(2, 512)

    best_eps = float("inf")
    best_a = None
    # compute per-alpha RDP per round and compose
    for a in alphas:
        # RDP per round (subsampled)
        rdp_r = _rdp_subsampled_gaussian(q, sigma, int(a))
        rdp_tot = rdp_r * rounds
        eps = _rdp_to_eps(rdp_tot, int(a), delta)
        if eps < best_eps:
            best_eps = eps
            best_a = int(a)
    return best_eps, best_a

# ------------------- Example usage -------------------
if __name__ == "__main__":
    # Example scenario:
    sigma = 0.5             # noise multiplier (std = 0.5 * clip_norm)
    rounds = 50
    delta = 1e-5
    total_clients = 100
    clients_per_round = 10
    q = clients_per_round / total_clients

    eps_full, a_full = compute_eps_from_sigma(sigma, rounds, delta)
    eps_sampled, a_sampled = compute_eps_poisson_subsampled(sigma, q, rounds, delta)
    print(f"Full participation: sigma={sigma}, rounds={rounds}, delta={delta} -> eps={eps_full:.4f} (alpha={a_full})")
    print(f"Poisson subsampling q={q:.4f}: sigma={sigma}, rounds={rounds}, delta={delta} -> eps={eps_sampled:.4f} (alpha={a_sampled})")
