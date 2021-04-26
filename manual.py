# Watcher vs. cultist floor 1

from collections import defaultdict
from agent import Agent, EndTurn, Play, Input, Output
from data import Card, Stance

class Manual(Agent):
    def act(self, state: Input) -> Output:
        cards: DefaultDict[Card, List[int]] = defaultdict(list)
        for i,card in enumerate(state.hand):
            cards[card].append(i)
        incoming_damage =(0 if state.their_ritual==0 else 6+state.their_strength)

        if Card.Eruption in cards and Card.Strike in cards and state.their_ritual == 0 and state.energy >= 2:
            return Play(Card.Eruption)
        elif state.my_stance == Stance.Calm and Card.Eruption in state.hand and state.energy >= 2:
            return Play(Card.Eruption)
        elif state.my_stance == Stance.Wrath and Card.Strike in state.hand and state.energy >= 1:
            return Play(Card.Strike)
        elif Card.Vigilance in cards and state.energy >= 2:
            return Play(Card.Vigilance)
        elif Card.Defend in cards and state.energy >= 1 and state.block+5 <= incoming_damage:
            return Play(Card.Defend)
        elif Card.Strike in cards and state.energy >= 1:
            return Play(Card.Strike)
        elif Card.Defend in cards and state.energy >= 1:
            return Play(Card.Defend)
        else:
            return EndTurn()
