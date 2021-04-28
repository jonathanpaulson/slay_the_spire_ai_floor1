from __future__ import annotations

from typing import List
from dataclasses import dataclass
from data import Card, Stance
from enum import Enum

class Output:
    @staticmethod
    def allActions() -> List[Output]:
        actions = [EndTurn(), Play(Card.Strike), Play(Card.Defend), Play(Card.Eruption), Play(Card.Vigilance)]
        return actions

    @staticmethod
    def goodActions() -> List[Output]:
        actions = [Play(Card.Strike), Play(Card.Defend), Play(Card.Eruption), Play(Card.Vigilance)]
        return actions

class EndTurn(Output):
    def __init__(self) -> None:
        pass
    def __eq__(self, other) -> bool:
        return isinstance(other, EndTurn)

class Play(Output):
    def __init__(self, card: Card):
        self.card = card
    def __eq__(self, other) -> bool:
        return isinstance(other, Play) and self.card == other.card

@dataclass
class Input:
    current_hp: int
    turn: int
    hand: List[Card]
    my_stance: Stance
    their_hp: int
    their_ritual: int
    their_strength: int
    deck: List[Card]
    discard: List[Card]
    energy: int
    block: int

    def incomingDamage(self) -> int:
        atk = (0 if self.their_ritual == 0 else 6+self.their_strength)
        dmg = atk * (2 if self.my_stance == Stance.Wrath else 1)
        unblocked = dmg - self.block
        return max(0, unblocked)

    def is_legal(self, action: Output) -> bool:
        if isinstance(action, EndTurn):
            return True
        else:
            assert isinstance(action, Play)
            card = action.card

            if all([c != card for c in self.hand]):
                # Card is not in hand
                return False

            if card == Card.Strike and self.energy >= 1:
                return True
            elif card == Card.Defend and self.energy >= 1:
                return True
            elif card == Card.Eruption and self.energy >= 2:
                return True
            elif card == Card.Vigilance and self.energy>=2:
                return True
            return False

class Agent:
    def act(self, state: Input) -> Output:
        raise NotImplementedError()
    def fight_over(self, score: int) -> None:
        pass

class DumbAgent(Agent):
    def act(self, state: Input) -> Output:
        for i,card in enumerate(state.hand):
            if state.is_legal(Play(card)):
                return Play(card)
        else:
            return EndTurn()
