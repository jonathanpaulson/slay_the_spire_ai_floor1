# Watcher vs. cultist floor 1

from typing import List
import random
import copy
import sys
from enum import Enum
from collections import defaultdict
import time

from agent import Agent, EndTurn, Play, DumbAgent, Input
from manual import Manual
from neural_net import NeuralNet
from data import Card, Stance
#random.seed(0)

# spike slimes attacks for 6 every turn
# acid slime has 3 moves: 8 dmg 1 slime, 1 weak, 12 damage 30-30-40 split

# cultist: ritual 4 -> 6 damage
DECK = [Card.Strike]*4 + [Card.Defend]*4 + [Card.Eruption, Card.Vigilance, Card.Bane]

class State(object):
    # Beginning of my turn
    def __init__(self, deck: List[Card], strategy: Agent, debug: bool) -> None:
        self.strategy = strategy
        self.debug = debug

        # Fight variables
        self.turn = 0
        self.my_hp = 72
        self.my_stance = Stance.Empty
        self.their_hp = 56
        self.their_ritual = 0
        self.their_strength = 0
        self.deck = copy.copy(deck)
        self.discard = []

        # Turn variables
        self.hand = None
        self.energy = None
        self.block = None

    def toInput(self) -> Input:
        return Input(self.my_hp, self.turn, self.hand,
                self.my_stance, self.their_hp, self.their_ritual, self.their_strength, self.deck, 
                self.discard, self.energy, self.block)

    def draw_hand(self):
        self.turn += 1
        self.energy = 3
        self.block = 0
        if len(self.deck) < 5:
            random.shuffle(self.discard)
            self.deck = self.deck + self.discard
            self.discard = []
        random.shuffle(self.deck)
        self.hand, self.deck = self.deck[:5], self.deck[5:]

    def dmg(self, dmg):
        return dmg*(2 if self.my_stance == Stance.Wrath else 1)

    def discard_hand(self):
        for card in self.hand:
            if card != Card.Bane:
                self.discard.append(card)

    def play_turn(self):
        if self.my_hp <= 0:
            if self.debug:
                print(f'Lost fight cultist_hp={self.their_hp}!\n\n\n')
            return -self.their_hp
        elif self.their_hp <= 0:
            if self.debug:
                print(f'Won fight with hp={self.my_hp}\n\n\n')
            return self.my_hp

        self.draw_hand()
        if self.debug:
            print(f'Starting turn {self.turn} hand={self.hand} deck={self.deck} discard={self.discard} my_hp={self.my_hp} their_hp={self.their_hp}')
        assert len(self.hand) == 5
        ncards = len(self.hand) + len(self.deck) + len(self.discard)
        # could have exhausted bane
        assert ncards == 10 or ncards == 11, f'Starting turn {self.turn} hand={self.hand} deck={self.deck} discard={self.discard} their_hp={self.their_hp}'

        while True:
            action = self.strategy.act(self.toInput())
            if isinstance(action, EndTurn):
                break
            else:
                assert isinstance(action, Play)
                matching_cards = [i for i,card in enumerate(self.hand) if card==action.card]
                assert len(matching_cards) > 0, f'Tried to play {action.card} but hand={self.hand}'
                self.play_card(matching_cards[0])
        self.discard_hand()
        self.their_play()

    def their_play(self):
        if self.their_hp > 0:
            if self.their_ritual == 0:
                self.their_ritual += 4
                if self.debug:
                    print(f'Cultist played ritual; ritual={self.their_ritual}')
            else:
                dmg = self.dmg(self.their_strength + 6)
                self.my_hp = self.my_hp - max(0, dmg-self.block)
                if self.debug:
                    print(f'Enemy attacked dmg={dmg} block={self.block} new_hp={self.my_hp}')
                self.their_strength += self.their_ritual

    def play_fight(self):
        while True:
            ans = self.play_turn()
            if ans is not None:
                return ans

    def is_playable(self, i):
        card = self.hand[i]
        if card == Card.Strike and self.energy >= 1:
            return True
        elif card == Card.Defend and self.energy >= 1:
            return True
        elif card == Card.Eruption and self.energy >= 2:
            return True
        elif card == Card.Vigilance and self.energy>=2:
            return True
        return False

    def play_card(self, i):
        card = self.hand[i]
        assert self.is_playable(i), f'Card is not playable card={card} energy={self.energy}'
        self.hand = [c for j,c in enumerate(self.hand) if j!=i]
        self.discard.append(card)
        if card == Card.Strike:
            dmg = self.dmg(6)
            self.their_hp -= dmg
            self.energy -= 1
            if self.debug:
                print(f'Played strike on Cultist for {dmg} damage new_hp={self.their_hp} energy={self.energy}')
        elif card == Card.Defend:
            self.block += 5
            self.energy -= 1
            if self.debug:
                print(f'Played defend new_block={self.block}')
        elif card == Card.Eruption:
            dmg = self.dmg(8)
            self.their_hp -= dmg
            self.energy -= 2
            if self.debug:
                print(f'Played eruption on Cultist for {dmg} damage new_hp={self.their_hp} energy={self.energy}')
            if self.my_stance == Stance.Calm:
                self.energy += 2
            self.my_stance = Stance.Wrath
        elif card == Card.Vigilance:
            self.block += 8
            self.my_stance = Stance.Calm
            self.energy -= 2
            if self.debug:
                print(f'Played vigilance new_block={self.block}')

def prompt_strategy(state):
    print(f'hand={state.hand}')
    to_play = [int(x) for x in input().split(',')]
    for idx in to_play:
        state.play_card(idx)

def evaluate(strategy, T, debug):
    hp_left = []
    for trial in range(T):
        state = State(DECK, strategy, debug=(trial==0))
        score = state.play_fight()
        hp_left.append(score)
        strategy.fight_over(score)
        if debug and trial % 500 == 0:
            print(f'{trial} {sum(hp_left)/len(hp_left)}', flush=True)
    avg = sum(hp_left)/T
    return avg

if len(sys.argv) > 1:
    evaluate(prompt_strategy)
else:
    T = int(1e5)
    net = NeuralNet()
    t0 = time.time()
    dumb_score = evaluate(DumbAgent(), 100, False)
    print(f'Dumb {dumb_score} {time.time()-t0}', flush=True)
    manual_score = evaluate(Manual(), T, False)
    print(f'Manual {manual_score} {time.time()-t0}', flush=True)
    net_scores = []
    for t in range(10):
        net.training = 10-t
        net_score = evaluate(net, T, True)
        print(f'Net{t} {net_score} {time.time()-t0}', flush=True)
        net.train()
        net_scores.append(net_score)
    net.training = 0
    net_final = evaluate(net, T, True)
    print(f'NetFinal {net_final} {time.time()-t0}', flush=True)
    print(f'dumb={dumb_score} manual={manual_score} {net_scores} net={net_final}')
