"""Summary statistics for simulated tournament data."""

from tournament_sim.probabilities import theoretical_reveal_cutoff


def summarize_by_treatment_and_type(player_records):
    """Return one summary row for each treatment and player type."""
    rows = []

    for key, records in _group_records(player_records, ["treatment_id", "player_type"]).items():
        treatment_id, player_type = key
        row = {
            "treatment_id": treatment_id,
            "player_type": player_type,
            "n_player_records": len(records),
            "reveal_rate": _mean_bool(records, "reveal_decision"),
            "improvement_rate": _mean_applicable(records, "improve_decision_if_applicable"),
            "improvement_rate_after_opponent_reveal": _improvement_rate_after_opponent_reveal(records),
            "average_payoff": _mean_number(records, "payoff"),
            "win_rate": _mean_bool(records, "won"),
            "theoretical_reveal_cutoff": theoretical_reveal_cutoff(records[0]["k"]),
            "empirical_reveal_cutoff": estimate_empirical_reveal_cutoff(records),
            "deterrence_rate": deterrence_rate(records),
        }
        rows.append(row)

    return _sort_rows(rows, ["treatment_id", "player_type"])


def reveal_rate_by_quality_bin(player_records, bin_size=10):
    """Return reveal rates by treatment, player type, and initial-quality bin."""
    prepared_records = []
    for record in player_records:
        copied = dict(record)
        copied["quality_bin"] = quality_bin_label(record["initial_quality"], bin_size)
        prepared_records.append(copied)

    rows = []
    groups = _group_records(prepared_records, ["treatment_id", "player_type", "quality_bin"])

    for key, records in groups.items():
        treatment_id, player_type, quality_bin = key
        rows.append(
            {
                "treatment_id": treatment_id,
                "player_type": player_type,
                "quality_bin": quality_bin,
                "n_player_records": len(records),
                "reveal_rate": _mean_bool(records, "reveal_decision"),
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            row["treatment_id"],
            row["player_type"],
            quality_bin_midpoint(row["quality_bin"]),
        ),
    )


def improvement_rate_by_revealed_opponent_quality(player_records, bin_size=10):
    """Return improvement rates after observing a revealed opponent quality."""
    prepared_records = []
    for record in player_records:
        if not record["opponent_reveal_decision"]:
            continue
        if record["reveal_decision"]:
            continue

        copied = dict(record)
        opponent_q = record["opponent_revealed_quality_if_observed"]
        copied["opponent_quality_bin"] = quality_bin_label(opponent_q, bin_size)
        prepared_records.append(copied)

    rows = []
    groups = _group_records(
        prepared_records,
        ["treatment_id", "player_type", "opponent_quality_bin"],
    )

    for key, records in groups.items():
        treatment_id, player_type, opponent_quality_bin = key
        rows.append(
            {
                "treatment_id": treatment_id,
                "player_type": player_type,
                "opponent_quality_bin": opponent_quality_bin,
                "n_player_records": len(records),
                "improvement_rate": _mean_applicable(records, "improve_decision_if_applicable"),
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            row["treatment_id"],
            row["player_type"],
            quality_bin_midpoint(row["opponent_quality_bin"]),
        ),
    )


def treatment_comparison_summary(player_records):
    """Return compact treatment-level comparisons."""
    rows = []

    for treatment_id, records in _group_records(player_records, ["treatment_id"]).items():
        row = {
            "treatment_id": treatment_id,
            "V": records[0]["V"],
            "c": records[0]["c"],
            "h": records[0]["h"],
            "k": records[0]["k"],
            "n_player_records": len(records),
            "reveal_rate": _mean_bool(records, "reveal_decision"),
            "improvement_rate": _mean_applicable(records, "improve_decision_if_applicable"),
            "average_payoff": _mean_number(records, "payoff"),
            "win_rate": _mean_bool(records, "won"),
        }
        rows.append(row)

    return _sort_rows(rows, ["treatment_id"])


def cutoff_comparison_summary(player_records):
    """Compare model reveal cutoff to simulated empirical cutoff by player type."""
    rows = []

    for key, records in _group_records(player_records, ["treatment_id", "player_type"]).items():
        treatment_id, player_type = key
        theoretical_cutoff = 100 * theoretical_reveal_cutoff(records[0]["k"])
        empirical_cutoff = estimate_empirical_reveal_cutoff(records)

        cutoff_difference = None
        if empirical_cutoff is not None:
            cutoff_difference = empirical_cutoff - theoretical_cutoff

        rows.append(
            {
                "treatment_id": treatment_id,
                "player_type": player_type,
                "V": records[0]["V"],
                "c": records[0]["c"],
                "h": records[0]["h"],
                "k": records[0]["k"],
                "model_reveal_cutoff": theoretical_cutoff,
                "simulated_empirical_cutoff": empirical_cutoff,
                "cutoff_difference_empirical_minus_model": cutoff_difference,
                "reveal_rate": _mean_bool(records, "reveal_decision"),
                "n_player_records": len(records),
            }
        )

    return _sort_rows(rows, ["treatment_id", "player_type"])


def estimate_empirical_reveal_cutoff(player_records, bin_size=5):
    """
    Estimate the first quality-bin midpoint where reveal rate is at least 50%.

    This is a descriptive simulated-data estimate, not the theoretical formula.
    """
    bin_rows = reveal_rate_by_quality_bin(player_records, bin_size)

    for row in bin_rows:
        if row["reveal_rate"] >= 0.5:
            return quality_bin_midpoint(row["quality_bin"])

    return None


def deterrence_rate(player_records, high_reveal_threshold=80):
    """
    Frequency of deterrence after a high opponent reveal.

    A deterrence case is counted when the player hid, saw an opponent reveal a
    quality at or above the threshold, and then chose not to improve.
    """
    cases = []

    for record in player_records:
        if record["reveal_decision"]:
            continue
        if not record["opponent_reveal_decision"]:
            continue

        opponent_q = record["opponent_revealed_quality_if_observed"]
        if opponent_q is None or opponent_q < high_reveal_threshold:
            continue

        cases.append(record)

    if not cases:
        return None

    deterred = 0
    for record in cases:
        if record["improve_decision_if_applicable"] is False:
            deterred += 1

    return deterred / len(cases)


def quality_bin_label(q, bin_size):
    """Create a label such as '80-89' or '100-100'."""
    low = int(q // bin_size) * bin_size
    high = low + bin_size - 1

    if high > 100:
        high = 100

    return str(low) + "-" + str(high)


def quality_bin_midpoint(label):
    low_text, high_text = label.split("-")
    low = int(low_text)
    high = int(high_text)
    return (low + high) / 2


def _group_records(records, field_names):
    groups = {}

    for record in records:
        key_parts = []
        for field_name in field_names:
            key_parts.append(record[field_name])

        if len(key_parts) == 1:
            key = key_parts[0]
        else:
            key = tuple(key_parts)

        if key not in groups:
            groups[key] = []
        groups[key].append(record)

    return groups


def _mean_bool(records, field_name):
    if not records:
        return None

    count = 0
    for record in records:
        if record[field_name]:
            count += 1

    return count / len(records)


def _mean_applicable(records, field_name):
    applicable = []

    for record in records:
        if record[field_name] is not None:
            applicable.append(record)

    if not applicable:
        return None

    return _mean_bool(applicable, field_name)


def _mean_number(records, field_name):
    if not records:
        return None

    total = 0.0
    for record in records:
        total += record[field_name]

    return total / len(records)


def _improvement_rate_after_opponent_reveal(records):
    applicable = []

    for record in records:
        if record["reveal_decision"]:
            continue
        if not record["opponent_reveal_decision"]:
            continue
        applicable.append(record)

    if not applicable:
        return None

    return _mean_applicable(applicable, "improve_decision_if_applicable")


def _sort_rows(rows, field_names):
    return sorted(rows, key=lambda row: tuple(row[field_name] for field_name in field_names))
