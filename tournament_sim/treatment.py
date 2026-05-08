"""Treatment settings for the research tournament simulation."""

from dataclasses import dataclass


@dataclass
class Treatment:
    """Parameters for one experimental treatment."""

    treatment_id: str
    V: float = 100.0
    c: float = 20.0
    h: float = 0.0
    quality_max: int = 100

    @property
    def k(self):
        """Cost as a share of the prize."""
        return self.c / self.V

    @property
    def has_hype(self):
        """Whether revealed winners can earn a hype bonus."""
        return self.h > 0


def default_treatments(hype_bonus=20.0):
    """Return the four baseline treatments from the project specification."""
    return [
        Treatment("baseline_low_cost", V=100.0, c=20.0, h=0.0),
        Treatment("baseline_high_cost", V=100.0, c=30.0, h=0.0),
        Treatment("hype_low_cost", V=100.0, c=20.0, h=hype_bonus),
        Treatment("hype_high_cost", V=100.0, c=30.0, h=hype_bonus),
    ]
