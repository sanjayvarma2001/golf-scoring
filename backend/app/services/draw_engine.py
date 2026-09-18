"""
The monthly draw engine: ticket generation, winning-number selection, match
calculation, and prize-pool math.

Documented assumption (PRD section 6/7 describe match tiers and pool shares
but not the underlying mechanism, and section 17 says "ambiguity is part of
the test"): every active subscriber is auto-issued one 5-number ticket
(1-49, lottery-style) per draw. A draw picks 5 "winning numbers"; a
subscriber's tier is however many of their ticket numbers appear in that
set. "Algorithmic" mode biases which numbers get picked by weighting each
candidate number by how often it appears on the tickets of higher-scoring
players, so more active/skilled players' numbers are somewhat more likely
to be drawn - "weighted by score frequency" - while still leaving the
outcome non-deterministic. "Random" mode is a plain uniform draw.

Kept as plain functions operating on already-loaded data (not raw ORM
queries sprinkled through route handlers) so the matching/pool math can be
unit tested without a database.
"""
import random
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Sequence

NUMBER_POOL = range(1, 50)  # 1-49, standard lottery-style range
NUMBERS_PER_TICKET = 5


def generate_ticket_numbers() -> List[int]:
    """A fresh, unique 5-number ticket for one subscriber in one draw."""
    return sorted(random.sample(NUMBER_POOL, NUMBERS_PER_TICKET))


def pick_winning_numbers(
    draw_type: str,
    all_ticket_numbers: Sequence[Sequence[int]],
    avg_score_by_ticket_index: Sequence[float],
) -> List[int]:
    """
    Choose the 5 winning numbers for a draw.

    all_ticket_numbers[i] is one participant's numbers; avg_score_by_ticket_index[i]
    is that same participant's average of their last 5 Stableford scores
    (used only in "algorithmic" mode, ignored otherwise).
    """
    if draw_type == "random" or not all_ticket_numbers:
        return sorted(random.sample(NUMBER_POOL, NUMBERS_PER_TICKET))

    if draw_type != "algorithmic":
        raise ValueError(f"Unknown draw_type: {draw_type!r}")

    # Build a weighted candidate pool: every number a participant holds is
    # added to the pool a number of times proportional to that participant's
    # average score (higher engagement/performance -> more weight), with a
    # floor of 1 so every number stays possible.
    weighted_pool: Counter = Counter()
    for numbers, avg_score in zip(all_ticket_numbers, avg_score_by_ticket_index):
        weight = max(1, round(avg_score))
        for n in numbers:
            weighted_pool[n] += weight

    candidates = list(weighted_pool.keys())
    weights = [weighted_pool[c] for c in candidates]

    chosen: List[int] = []
    pool, pool_weights = candidates[:], weights[:]
    while len(chosen) < NUMBERS_PER_TICKET and pool:
        pick = random.choices(pool, weights=pool_weights, k=1)[0]
        chosen.append(pick)
        idx = pool.index(pick)
        pool.pop(idx)
        pool_weights.pop(idx)

    # Top up from the full number range if fewer than 5 distinct numbers were held across all tickets.
    remaining = [n for n in NUMBER_POOL if n not in chosen]
    while len(chosen) < NUMBERS_PER_TICKET and remaining:
        pick = random.choice(remaining)
        chosen.append(pick)
        remaining.remove(pick)

    return sorted(chosen)


def match_tier(ticket_numbers: Sequence[int], winning_numbers: Sequence[int]) -> int:
    """How many of a ticket's numbers are in the winning set - 0 to 5."""
    return len(set(ticket_numbers) & set(winning_numbers))


@dataclass
class PoolBreakdown:
    pool_5_match: float
    pool_4_match: float
    pool_3_match: float


def compute_prize_pools(
    *,
    active_subscriber_count: int,
    average_subscription_fee: float,
    share_5: float,
    share_4: float,
    share_3: float,
    jackpot_rollover_in: float,
) -> PoolBreakdown:
    """
    PRD section 7: "auto-calculation of each pool tier based on active
    subscriber count", with fixed 40/35/25 shares and 5-match jackpot rollover.
    """
    total_pool = active_subscriber_count * average_subscription_fee
    return PoolBreakdown(
        pool_5_match=round(total_pool * share_5 + jackpot_rollover_in, 2),
        pool_4_match=round(total_pool * share_4, 2),
        pool_3_match=round(total_pool * share_3, 2),
    )


@dataclass
class TierResult:
    match_tier: int
    winner_user_ids: List[str]
    prize_per_winner: float
    pool_amount: float


def resolve_tiers(
    *,
    matches_by_user: Dict[str, int],
    pools: PoolBreakdown,
) -> List[TierResult]:
    """
    Group participants by match tier (3/4/5) and split each tier's pool
    equally among its winners (PRD: "prizes split equally among multiple
    winners in the same tier"). A tier with zero winners keeps its pool at
    0 distributed - the 5-match pool's rollover is handled by the caller,
    since only that tier rolls over per the PRD.
    """
    winners_by_tier: Dict[int, List[str]] = {5: [], 4: [], 3: []}
    for user_id, tier in matches_by_user.items():
        if tier in winners_by_tier:
            winners_by_tier[tier].append(user_id)

    pool_by_tier = {5: pools.pool_5_match, 4: pools.pool_4_match, 3: pools.pool_3_match}
    results = []
    for tier in (5, 4, 3):
        winners = winners_by_tier[tier]
        pool_amount = pool_by_tier[tier]
        prize_per_winner = round(pool_amount / len(winners), 2) if winners else 0.0
        results.append(
            TierResult(match_tier=tier, winner_user_ids=winners, prize_per_winner=prize_per_winner, pool_amount=pool_amount)
        )
    return results
