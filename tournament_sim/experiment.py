"""Experiment-level simulation with subjects, treatments, and random matching."""

from dataclasses import dataclass
import random

from tournament_sim.agents import (
    AlwaysHideImproveAgent,
    AlwaysHideStopAgent,
    AlwaysRevealAgent,
    EquilibriumAgent,
)
from tournament_sim.round import simulate_round
from tournament_sim.treatment import default_treatments


AGENT_TYPES = {
    "EquilibriumAgent": EquilibriumAgent,
    "AlwaysRevealAgent": AlwaysRevealAgent,
    "AlwaysHideStopAgent": AlwaysHideStopAgent,
    "AlwaysHideImproveAgent": AlwaysHideImproveAgent,
}


@dataclass
class Subject:
    """One simulated subject in the experiment."""

    subject_id: int
    agent: object
    player_type: str
    treatment_id: str


@dataclass
class ExperimentResult:
    """Data returned by an experiment-level simulation."""

    player_records: list
    match_records: list
    subjects: list


def simulate_experiment(
    num_subjects=200,
    num_rounds=100,
    treatments=None,
    population_composition=None,
    random_matching=True,
    rng_seed=12345,
):
    """
    Simulate many subjects across many rounds.

    The current default is between-subjects treatment assignment: each simulated
    subject is assigned to one treatment, and random matching happens within
    that treatment group each round.
    """
    if treatments is None:
        treatments = default_treatments()

    if population_composition is None:
        population_composition = {"EquilibriumAgent": 1.0}

    rng = random.Random(rng_seed)
    subjects = create_subjects(
        num_subjects,
        treatments,
        population_composition,
        rng,
    )

    treatment_by_id = {}
    for treatment in treatments:
        treatment_by_id[treatment.treatment_id] = treatment

    subjects_by_treatment = _group_subjects_by_treatment(subjects)
    player_records = []
    match_records = []
    match_id = 1

    for round_number in range(1, num_rounds + 1):
        for treatment in treatments:
            group = subjects_by_treatment[treatment.treatment_id]
            pairs = _make_pairs(group, rng, random_matching)

            for subject_1, subject_2 in pairs:
                result = simulate_round(
                    subject_1.agent,
                    subject_2.agent,
                    treatment_by_id[subject_1.treatment_id],
                    rng=rng,
                    round_number=round_number,
                    subject_ids=(subject_1.subject_id, subject_2.subject_id),
                )

                for record in result.player_records:
                    record["match_id"] = match_id
                    player_records.append(record)

                result.match_record["match_id"] = match_id
                match_records.append(result.match_record)
                match_id += 1

    return ExperimentResult(player_records, match_records, subjects)


def create_subjects(num_subjects, treatments, population_composition, rng):
    """Create subjects and assign each to one treatment and one agent type."""
    if num_subjects < 2:
        raise ValueError("num_subjects must be at least 2")

    _check_population_composition(population_composition)

    treatment_shares = {}
    for treatment in treatments:
        treatment_shares[treatment.treatment_id] = 1.0

    treatment_counts = _allocate_counts(num_subjects, treatment_shares)

    subjects = []
    next_subject_id = 1

    for treatment in treatments:
        treatment_id = treatment.treatment_id
        treatment_count = treatment_counts[treatment_id]
        agent_counts = _allocate_counts(treatment_count, population_composition)

        for agent_type, count in agent_counts.items():
            for _ in range(count):
                agent = make_agent(agent_type)
                subjects.append(
                    Subject(
                        subject_id=next_subject_id,
                        agent=agent,
                        player_type=agent_type,
                        treatment_id=treatment_id,
                    )
                )
                next_subject_id += 1

    rng.shuffle(subjects)
    return subjects


def make_agent(agent_type):
    """Create a fresh agent object from its type name."""
    if agent_type not in AGENT_TYPES:
        raise ValueError("Unknown agent type: " + str(agent_type))

    return AGENT_TYPES[agent_type]()


def _check_population_composition(population_composition):
    total_share = sum(population_composition.values())
    if total_share <= 0:
        raise ValueError("population_composition must have positive shares")

    for agent_type, share in population_composition.items():
        if agent_type not in AGENT_TYPES:
            raise ValueError("Unknown agent type: " + str(agent_type))
        if share < 0:
            raise ValueError("Population shares cannot be negative")


def _allocate_counts(total_count, shares):
    """
    Convert shares into integer counts.

    This uses the largest-remainder method: take the floor of each exact count,
    then give remaining slots to the largest fractional remainders.
    """
    share_total = sum(shares.values())
    exact_counts = {}
    floor_counts = {}

    for key, share in shares.items():
        exact = total_count * share / share_total
        exact_counts[key] = exact
        floor_counts[key] = int(exact)

    remaining = total_count - sum(floor_counts.values())
    remainders = []

    for key, exact in exact_counts.items():
        remainders.append((exact - floor_counts[key], key))

    remainders.sort(reverse=True)

    for index in range(remaining):
        key = remainders[index][1]
        floor_counts[key] += 1

    return floor_counts


def _group_subjects_by_treatment(subjects):
    groups = {}

    for subject in subjects:
        if subject.treatment_id not in groups:
            groups[subject.treatment_id] = []
        groups[subject.treatment_id].append(subject)

    return groups


def _make_pairs(subjects, rng, random_matching):
    """Pair subjects. If a group is odd, the last shuffled subject sits out."""
    ordered_subjects = list(subjects)

    if random_matching:
        rng.shuffle(ordered_subjects)
    else:
        ordered_subjects.sort(key=lambda subject: subject.subject_id)

    pairs = []
    index = 0
    while index + 1 < len(ordered_subjects):
        pairs.append((ordered_subjects[index], ordered_subjects[index + 1]))
        index += 2

    return pairs
