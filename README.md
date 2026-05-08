# Research Tournament Simulation

Simulation code for a two-player, two-period laboratory research tournament with strategic disclosure.

The project will be built in small steps so the model, assumptions, and implementation remain easy to inspect.

## Planned Scope

- Discrete quality grid from 0 to 100.
- Reveal or hide decisions.
- Lock-in after reveal.
- Costly improvement for hidden players.
- Winner-contingent hype treatment.
- Multiple configurable behavioral agent types.
- Random matching across simulated subjects.
- Summary tables and plots for treatment comparisons.

## Initial Treatments

| Treatment | Prize V | Cost c | Hype h |
| --- | ---: | ---: | ---: |
| Baseline low cost | 100 | 20 | 0 |
| Baseline high cost | 100 | 30 | 0 |
| Hype low cost | 100 | 20 | 20 |
| Hype high cost | 100 | 30 | 20 |

## Development Plan

1. Implement treatment parameters and exact discrete payoff calculations.
2. Implement a single-round simulator.
3. Add equilibrium benchmark agents.
4. Add noisy and heuristic behavioral agents.
5. Add experiment-level random matching.
6. Generate summary tables and plots.

## Current Status

The first project skeleton is in place:

- `tournament_sim/treatment.py` defines treatment parameters.
- `tournament_sim/probabilities.py` defines exact discrete probability helpers.
- `tournament_sim/agents.py` defines the basic agent interface.
- `tournament_sim/round.py` defines a simple player state object.
- `scripts/run_example.py` prints the default treatment cutoffs.
- `tests/test_probabilities.py` checks the first probability helpers.

Once Python is available, run the small checks with:

```bash
python tests/test_probabilities.py
python scripts/run_example.py
```
