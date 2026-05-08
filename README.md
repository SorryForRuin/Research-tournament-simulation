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
- `tournament_sim/agents.py` defines the basic agent interface and benchmark `EquilibriumAgent`.
- `tournament_sim/experiment.py` simulates subjects, treatments, and random matching.
- `tournament_sim/round.py` simulates one complete two-player round.
- `scripts/run_example.py` prints treatment cutoffs and one example round.
- `tests/test_probabilities.py` checks the first probability helpers.
- `tests/test_round.py` checks the first round-simulation rules.
- `tests/test_treatments.py` checks the default treatment definitions.
- `tests/test_experiment.py` checks experiment-level matching and records.
- `tests/test_behavioral_agents.py` checks the additional behavioral agent types.

Once Python is available, run the small checks with:

```bash
python tests/test_probabilities.py
python tests/test_round.py
python tests/test_equilibrium_agent.py
python tests/test_treatments.py
python tests/test_experiment.py
python tests/test_behavioral_agents.py
python scripts/run_example.py
```

## Round Simulator Notes

The current one-round simulator handles:

- simultaneous reveal/hide decisions,
- reveal lock-in,
- simultaneous improve/stop decisions when both players hide,
- hidden-player best-response information when the opponent revealed,
- improvement draws from the current quality up to 100,
- random tie-breaking,
- winner-contingent hype for revealed winners only,
- improvement costs paid whether the player wins or loses.

## Experiment Simulator Notes

The current experiment simulator uses between-subjects treatment assignment:
subjects are split as evenly as possible across the four default treatments, and
random matching happens within each treatment group each round.

The population composition is configurable. For example:

```python
population_composition = {
    "EquilibriumAgent": 0.4,
    "NoisyEquilibriumAgent": 0.2,
    "UnderRevealerAgent": 0.15,
    "OverRevealerAgent": 0.15,
    "MyopicHeuristicAgent": 0.1,
}
```
