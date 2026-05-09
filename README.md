# Research Tournament Simulation

Python code for simulating and analyzing a two-player, two-period laboratory
research tournament with strategic disclosure.

This README is written for someone opening the repository in PyCharm, VS Code,
or a similar IDE.

## 1. Setup

Open the repository folder in your IDE:

```text
Research-tournament-simulation/
```

Create or select a Python interpreter, then install the required packages from
the project root:

```bash
python -m pip install -r requirements.txt
```

The project currently uses:

```text
matplotlib
pandas
statsmodels
```

## 2. What To Run

### Quick Demo

Run:

```bash
python scripts/run_example.py
```

This prints a small readable demo:

- treatment cutoffs,
- one hand-picked round,
- agent decision examples,
- a small 40-subject simulation,
- compact treatment summaries.

### Run All Core Tests

Run these files from the project root:

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
python tests/test_analysis.py
```

Each test file prints a short success message if it passes.

### Generate Small Example Plots

Run:

```bash
python scripts/generate_small_plots.py
```

Outputs:

```text
outputs/plots/small_example/
```

Use this while developing because it is fast.

### Run The Full Simulation

Run:

```bash
python scripts/run_full_simulation.py
```

This creates the main simulated dataset:

```text
200 subjects
100 rounds
50 subjects per treatment
10,000 matches
20,000 player-round records
```

Outputs:

```text
outputs/full_simulation/
```

### Run Statistical Tests

Run this after `scripts/run_full_simulation.py` has created the full dataset:

```bash
python scripts/run_analysis.py
```

Outputs:

```text
outputs/analysis/
```

This runs the requested regressions, deterrence test, equilibrium-compliance
checks, descriptive tables, and analysis plots.

## 3. Output Folders

### Full Simulation Outputs

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
outputs/full_simulation/plots/
```

### Analysis Outputs

Regression text summaries:

```text
outputs/analysis/regression_summaries/
```

Coefficient tables:

```text
outputs/analysis/coefficient_tables/
```

Descriptive tables:

```text
outputs/analysis/descriptive_tables/
```

Statistical-test plots:

```text
outputs/analysis/plots/
```

## 4. File Map

### Core Simulation Package

```text
tournament_sim/treatment.py
```

Defines treatment parameters:

- prize `V`,
- improvement cost `c`,
- hype bonus `h`,
- quality grid.

```text
tournament_sim/probabilities.py
```

Defines exact discrete probability helpers and theoretical cutoffs:

- `r_star`,
- `s_star`,
- exact win probability after improvement.

```text
tournament_sim/agents.py
```

Defines behavioral agent types:

- `EquilibriumAgent`
- `NoisyEquilibriumAgent`
- `UnderRevealerAgent`
- `OverRevealerAgent`
- `MyopicHeuristicAgent`

```text
tournament_sim/round.py
```

Simulates one two-player round:

- draw qualities,
- reveal/hide,
- improve/stop,
- final quality,
- tie-breaking,
- payoff calculation.

```text
tournament_sim/experiment.py
```

Simulates a full experiment:

- creates subjects,
- assigns treatments,
- assigns agent types,
- randomly matches subjects within treatment,
- collects player-round and match-round records.

```text
tournament_sim/summary.py
```

Computes summary tables:

- reveal rates,
- improvement rates,
- payoff averages,
- quality-bin summaries,
- deterrence summaries,
- cutoff/compliance summaries.

```text
tournament_sim/plots.py
```

Generates PNG plots from simulation records.

```text
tournament_sim/export.py
```

Exports raw records and summary tables to CSV.

```text
tournament_sim/analysis.py
```

Runs the statistical analysis:

- clustered OLS/LPM regressions,
- optional logit regressions,
- deterrence test,
- equilibrium-compliance test,
- under/over-reveal test,
- payoff regressions,
- descriptive tables,
- analysis plots.

## 5. Script Map

```text
scripts/run_example.py
```

Small readable demo. Use this first to see the model working.

```text
scripts/generate_small_plots.py
```

Creates quick development plots from a small simulation.

```text
scripts/run_full_simulation.py
```

Runs the full 200-subject simulation and writes CSVs and plots.

Population composition is set in this file:

```python
POPULATION_COMPOSITION = {
    "EquilibriumAgent": 0.40,
    "NoisyEquilibriumAgent": 0.20,
    "UnderRevealerAgent": 0.15,
    "OverRevealerAgent": 0.15,
    "MyopicHeuristicAgent": 0.10,
}
```

```text
scripts/run_analysis.py
```

Runs all statistical tests on the full simulation output.

## 6. Statistical Tests Implemented

The analysis pipeline implements:

1. Reveal probability increasing with initial quality.
2. Effect of higher cost ratio `c / V` on reveal frequency.
3. Effect of hype treatment on reveal frequency.
4. Deterrence: whether observed revealed opponent quality reduces improvement.
5. Equilibrium-compliance and empirical cutoff checks.
6. Under-reveal versus over-reveal relative to the benchmark cutoff.
7. Payoff effect of revealing while controlling for quality and treatment.

Important deterrence restriction:

```text
eligible_to_improve == 1
opponent_revealed == 1
```

So the deterrence regression only uses hidden players who actually observed an
opponent reveal.

## 7. Model Details

Each round:

1. Two players receive private initial quality `q` on the grid `0` to `100`.
2. Each chooses `Reveal` or `Hide`.
3. Reveal locks quality permanently.
4. Hidden players may choose `Stop` or `Improve`.
5. Improvement costs `c` and redraws quality uniformly from `{q, ..., 100}`.
6. Highest final quality wins prize `V`.
7. Ties are broken randomly.
8. Revealed winners receive hype bonus `h` in hype treatments.

No-hype continuous benchmark:

```text
k = c / V
r_star = (1 - k^2) / (1 + 3*k^2)
s_star = ((1-k)*(1-3*k)) / (1 + 3*k^2)
```

Interpretation:

- reveal if `q_norm >= r_star`,
- if both hide, improve if `q_norm >= s_star`,
- if the opponent revealed, hidden players best respond to the revealed quality.

## 8. Treatments

| Treatment | Prize V | Cost c | Hype h | k = c / V |
| --- | ---: | ---: | ---: | ---: |
| `baseline_low_cost` | 100 | 20 | 0 | 0.20 |
| `baseline_high_cost` | 100 | 30 | 0 | 0.30 |
| `hype_low_cost` | 100 | 20 | 20 | 0.20 |
| `hype_high_cost` | 100 | 30 | 20 | 0.30 |

## 9. Git And Outputs

Generated outputs under `outputs/` are ignored by Git.

That means:

- code is committed,
- scripts are committed,
- tests are committed,
- generated CSV and PNG files are local artifacts.

To reproduce outputs, run:

```bash
python scripts/run_full_simulation.py
python scripts/run_analysis.py
```
