# Research Tournament Simulation

Python simulation for a two-player, two-period laboratory research tournament
with strategic disclosure.

The simulation uses a discrete quality grid from `0` to `100`. Each player gets
a private initial quality, chooses whether to reveal or hide, and hidden players
may later pay to improve. Revealed quality is locked in. Hype bonuses are paid
only to revealed winners.

## Quick Start

From the project folder, install the plotting dependency:

```bash
python -m pip install -r requirements.txt
```

On this machine, Codex has been using the full Python path:

```powershell
& 'C:\Users\KOK\AppData\Local\Programs\Python\Python313\python.exe' script_name.py
```

If plain `python` works in your terminal, you can use the shorter commands below.

## What To Run

Run a small readable demo:

```bash
python scripts/run_example.py
```

This prints:

- treatment cutoffs,
- one hand-picked example round,
- example decisions from the agent types,
- a small 40-subject simulation,
- compact treatment summaries.

Generate plots from the small development simulation:

```bash
python scripts/generate_small_plots.py
```

Outputs are written to:

```text
outputs/plots/small_example/
```

Run the full simulation:

```bash
python scripts/run_full_simulation.py
```

The full simulation uses:

```text
200 subjects
100 rounds
50 subjects per treatment
10,000 matches
20,000 player-round records
```

Full outputs are written to:

```text
outputs/full_simulation/
```

## Full Output Files

Raw data:

```text
outputs/full_simulation/data/player_round_records.csv
outputs/full_simulation/data/match_round_records.csv
```

Summary tables:

```text
outputs/full_simulation/summary_tables/treatment_summary.csv
outputs/full_simulation/summary_tables/treatment_by_player_type_summary.csv
outputs/full_simulation/summary_tables/cutoff_comparison_by_player_type.csv
outputs/full_simulation/summary_tables/reveal_rate_by_quality_bin.csv
outputs/full_simulation/summary_tables/improvement_by_revealed_quality.csv
```

Plots:

```text
outputs/full_simulation/plots/reveal_probability_by_quality_bin_treatment.png
outputs/full_simulation/plots/improvement_probability_by_revealed_quality_filtered.png
outputs/full_simulation/plots/theoretical_reveal_region.png
outputs/full_simulation/plots/payoff_distribution_by_treatment.png
outputs/full_simulation/plots/cutoff_comparison_by_player_type.png
```

## Treatments

| Treatment | Prize V | Cost c | Hype h | k = c / V |
| --- | ---: | ---: | ---: | ---: |
| `baseline_low_cost` | 100 | 20 | 0 | 0.20 |
| `baseline_high_cost` | 100 | 30 | 0 | 0.30 |
| `hype_low_cost` | 100 | 20 | 20 | 0.20 |
| `hype_high_cost` | 100 | 30 | 20 | 0.30 |

Treatment parameters are defined in:

```text
tournament_sim/treatment.py
```

## Agent Types

Current behavioral types:

- `EquilibriumAgent`: uses the no-hype theoretical benchmark cutoffs.
- `NoisyEquilibriumAgent`: logistic noise around equilibrium decisions.
- `UnderRevealerAgent`: equilibrium-style, but with a higher reveal cutoff.
- `OverRevealerAgent`: equilibrium-style, but with a lower reveal cutoff.
- `MyopicHeuristicAgent`: simple threshold behavior.

The full simulation population mix is set in:

```text
scripts/run_full_simulation.py
```

Current full-run mix:

```python
POPULATION_COMPOSITION = {
    "EquilibriumAgent": 0.40,
    "NoisyEquilibriumAgent": 0.20,
    "UnderRevealerAgent": 0.15,
    "OverRevealerAgent": 0.15,
    "MyopicHeuristicAgent": 0.10,
}
```

## Model Cutoffs

For the no-hype continuous benchmark:

```text
k = c / V
r_star = (1 - k^2) / (1 + 3*k^2)
s_star = ((1-k)*(1-3*k)) / (1 + 3*k^2)
```

Interpretation:

- reveal if normalized quality `q >= r_star`,
- if both players hide, improve if normalized quality `q >= s_star`,
- if the opponent revealed, hidden players compare expected payoff from
  improving versus stopping using exact discrete probabilities.

## Tests

Run all test files:

```bash
python tests/test_probabilities.py
python tests/test_round.py
python tests/test_equilibrium_agent.py
python tests/test_treatments.py
python tests/test_experiment.py
python tests/test_behavioral_agents.py
python tests/test_summary.py
python tests/test_plots.py
python tests/test_export.py
```

What they check:

- exact discrete probability calculations,
- one-round tournament rules,
- equilibrium cutoff behavior,
- treatment definitions,
- experiment-level random matching,
- behavioral agent variants,
- summary statistics,
- plot generation,
- CSV export.

## Project Structure

```text
tournament_sim/
  agents.py        agent decision rules
  experiment.py    subjects, treatment assignment, random matching
  export.py        CSV export
  plots.py         PNG plot generation
  probabilities.py exact probability and cutoff helpers
  round.py         one two-player round
  summary.py       summary tables
  treatment.py     treatment parameters

scripts/
  run_example.py          small readable demo
  generate_small_plots.py small plot generation
  run_full_simulation.py  full simulation, CSVs, and plots

tests/
  test_*.py        dependency-light checks for each project layer
```

## Git Notes

Generated outputs under `outputs/` are ignored by Git. The code that generates
them is committed, but the CSV and PNG files are local artifacts.
