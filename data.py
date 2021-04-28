from enum import Enum

class Card(Enum):
    Strike = 'strike'
    Defend = 'defend'
    Eruption = 'eruption'
    Vigilance = 'vigilance'
    Bane = 'bane'

    def __repr__(self) -> str:
        return self.value

class Stance(Enum):
    Empty = 0
    Calm = 1
    Wrath = 2
