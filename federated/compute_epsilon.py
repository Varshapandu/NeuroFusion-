# federated/compute_epsilon.py
import argparse
from federated.accountant import compute_eps_fullparticipation, compute_eps_poisson_subsampled

def main():
    parser = argparse.ArgumentParser(description="Compute (epsilon, alpha) for update-level DP (Gaussian mechanism).")
    parser.add_argument("--sigma", type=float, required=True, help="Noise multiplier sigma (std = sigma * clip_norm).")
    parser.add_argument("--rounds", type=int, required=True, help="Number of rounds (compositions).")
    parser.add_argument("--delta", type=float, default=1e-5, help="Delta for (epsilon, delta).")
    parser.add_argument("--total_clients", type=int, default=0, help="Total clients (if using sampling).")
    parser.add_argument("--clients_per_round", type=int, default=0, help="Clients selected per round (if using sampling).")
    parser.add_argument("--mode", choices=["full", "poisson"], default="poisson", help="Compute mode: full participation or poisson subsampling.")
    args = parser.parse_args()

    sigma = args.sigma
    rounds = args.rounds
    delta = args.delta

    if args.mode == "full":
        eps, alpha = compute_eps_fullparticipation(clip_norm=1.0, sigma_multiplier=sigma, rounds=rounds, delta=delta)
        print(f"Full participation | sigma={sigma} rounds={rounds} delta={delta} -> eps={eps:.6f} (alpha={alpha})")
    else:
        if args.total_clients <= 0 or args.clients_per_round <= 0:
            print("For poisson mode you must pass --total_clients and --clients_per_round (positive ints).")
            return
        q = float(args.clients_per_round) / float(args.total_clients)
        eps, alpha = compute_eps_poisson_subsampled(sigma, q, rounds, delta)
        print(f"Poisson subsampling | sigma={sigma} q={q:.6f} rounds={rounds} delta={delta} -> eps={eps:.6f} (alpha={alpha})")

if __name__ == "__main__":
    main()
