# rng.py - Reproducible RNG system with seed support

import random
from typing import Any, Dict, List, Optional, Protocol, TypeVar, cast


class RNG(Protocol):
    """Random number generator interface for testability"""
    
    def random(self) -> float:
        """Return random float in [0, 1)"""
        ...
    
    def randint(self, low: int, high: int) -> int:
        """Return random int in [low, high]"""
        ...
    
    def choice(self, seq: List[T]) -> T:
        """Return random choice from sequence"""
        ...
    
    def shuffle(self, seq: List[T]) -> None:
        """Shuffle sequence in place"""
        ...
    
    def choices(self, seq: List[T], weights: List[float], k: int = 1) -> List[T]:
        """Return k choices with weights"""
        ...
    
    def seed(self, seed: int) -> None:
        """Set RNG seed"""
        ...
    
    def get_state(self) -> Dict[str, Any]:
        """Get RNG state for serialization"""
        ...
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> "RNG":
        """Restore RNG from state"""
        ...


T = TypeVar("T")


class DefaultRNG:
    """Default RNG implementation wrapping Python's random"""
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._seed = seed
    
    def random(self) -> float:
        return self._rng.random()
    
    def randint(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)
    
    def choice(self, seq: List[Any]) -> Any:
        return self._rng.choice(seq)
    
    def shuffle(self, seq: List[Any]) -> None:
        self._rng.shuffle(seq)
    
    def choices(self, seq: List[Any], weights: List[float], k: int = 1) -> List[Any]:
        return self._rng.choices(seq, weights=weights, k=k)
    
    def sample(self, seq: List[Any], k: int = 1) -> List[Any]:
        return self._rng.sample(seq, k)
    
    def seed(self, seed: int) -> None:
        self._seed = seed
        self._rng.seed(seed)
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "seed": self._seed,
            "state": self._rng.getstate()
        }
    
    @classmethod
    def from_state(cls, state: Dict[str, Any]) -> "DefaultRNG":
        rng = cls(seed=state.get("seed"))
        if "state" in state:
            rng._rng.setstate(state["state"])
        return rng
    
    def copy(self) -> "DefaultRNG":
        """Create a copy with the same state"""
        new_rng = DefaultRNG(seed=self._seed)
        new_rng._rng.setstate(self._rng.getstate())
        return new_rng


class RNGContext:
    """Context manager for temporary RNG state"""
    
    def __init__(self, rng: RNG):
        self.rng = rng
        self.saved_state: Optional[Dict[str, Any]] = None
    
    def __enter__(self) -> RNG:
        self.saved_state = self.rng.get_state()
        return self.rng
    
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[BaseException]) -> None:
        if self.saved_state is not None:
            # Restore RNG state
            if hasattr(self.rng, 'from_state'):
                restored = self.rng.from_state(self.saved_state)
                # Copy state back
                self.rng.seed(restored._rng.getstate() if hasattr(restored, '_rng') else 0)


def create_rng(seed: Optional[int] = None) -> RNG:
    """Factory function to create RNG"""
    return DefaultRNG(seed=seed)


# Specialized random functions using the RNG interface

def random_between(rng: RNG, low: int, high: int) -> int:
    """Get random int between low and high (inclusive)"""
    return rng.randint(low, high)


def random_float(rng: RNG, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Get random float between min and max"""
    return min_val + rng.random() * (max_val - min_val)


def random_choice(rng: RNG, items: List[T]) -> T:
    """Get random item from list"""
    if not items:
        raise ValueError("Cannot choose from empty list")
    return rng.choice(items)


def random_weighted_choice(
    rng: RNG,
    items: List[T],
    weights: List[float]
) -> T:
    """Get weighted random item"""
    if not items:
        raise ValueError("Cannot choose from empty list")
    if len(items) != len(weights):
        raise ValueError(f"Items count ({len(items)}) != weights count ({len(weights)})")
    return rng.choices(items, weights, k=1)[0]


def shuffle_list(rng: RNG, items: List[T]) -> None:
    """Shuffle list in place"""
    rng.shuffle(items)


def roll_chance(rng: RNG, percent: float) -> bool:
    """Roll for percentage chance (0-100)"""
    return rng.random() * 100 < percent


def roll_critical(rng: RNG, crit_chance: float, crit_multiplier: float = 2.0) -> tuple:
    """Roll for critical hit
    
    Returns:
        (is_critical, multiplier)
    """
    if roll_chance(rng, crit_chance):
        return True, crit_multiplier
    return False, 1.0


def random_stat_bonus(rng: RNG, base: int, variance: float = 0.1) -> int:
    """Get stat with random variance
    
    Args:
        rng: RNG instance
        base: Base stat value
        variance: Variance percentage (0.1 = ±10%)
    
    Returns:
        Modified stat value
    """
    modifier = random_float(rng, 1 - variance, 1 + variance)
    return max(1, int(base * modifier))


# Loot rarity probabilities (can be configured)
DEFAULT_LOOT_TABLE = {
    "common": 60.0,
    "rare": 25.0,
    "epic": 10.0,
    "legendary": 4.0,
    "corrupted": 1.0,
}


def random_rarity(rng: RNG, table: Dict[str, float] | None = None) -> str:
    """Roll for loot rarity"""
    if table is None:
        table = DEFAULT_LOOT_TABLE
    
    items = list(table.keys())
    weights = list(table.values())
    return random_weighted_choice(rng, items, weights)
