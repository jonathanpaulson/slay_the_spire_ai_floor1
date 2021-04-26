from typing import List
from dataclasses import dataclass
from data import Card, Stance
from enum import Enum

class Output:
    pass

class EndTurn(Output):
    def __init__(self) -> None:
        pass
class Play(Output):
    def __init__(self, card: Card):
        self.card = card

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
