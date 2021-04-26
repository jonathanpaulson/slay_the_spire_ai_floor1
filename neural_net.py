# Watcher vs. cultist floor 1

from collections import defaultdict
from typing import List
import random

import numpy as np
import tensorflow as tf

from agent import Agent, EndTurn, Play, Input, Output
from data import Card, Stance

def inputToNeural(state: Input) -> List[float]:
    ans = []
    incoming_damage = max(0, (0 if state.their_ritual==0 else 6+state.their_strength) - state.block)
    ans.append(state.current_hp/100.) # 1
    ans.append(state.their_hp/100.) # 2
    ans.append(state.energy/3.) # 3
    ans.append(incoming_damage/20.) # 4
    ans.append(1.0 if state.my_stance == Stance.Empty else 0.0) # 5
    ans.append(1.0 if state.my_stance == Stance.Wrath else 0.0) # 6
    ans.append(1.0 if state.my_stance == Stance.Calm else 0.0) # 7
    for lst in [state.hand, state.deck, state.discard]: # 22
        for card in list(Card):
            count = lst.count(card)
            ans.append(count/5.)
    assert len(ans) == 22
    return ans

class NeuralNet(Agent):
    def __init__(self) -> None:
        self.current_fight = []
        self.train_data = []

        self.model = tf.keras.models.Sequential([
            tf.keras.layers.Flatten(input_shape=(22,)),
            tf.keras.layers.Dense(20, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(5)
        ])

    def act(self, state: Input) -> Output:
        actions = [EndTurn(), Play(Card.Strike), Play(Card.Defend), Play(Card.Eruption), Play(Card.Vigilance)]

        input_ = inputToNeural(state)
        np_input = np.expand_dims(np.asarray(input_, dtype=np.float32), axis=0)
        scores = self.model(np_input).numpy()
        scored_actions = zip(scores[0], list(range(len(actions))), actions)
        scored_actions = list(reversed(sorted(scored_actions)))

        for (_score, i, action) in scored_actions:
            if state.is_legal(action) and not isinstance(action, EndTurn):
                y = [False]*len(actions)
                y[i] = True
                self.current_fight.append((input_, y))
                return action
        self.current_fight.append((input_, [True]+[False]*(len(actions)-1)))
        return EndTurn()

    def fight_over(self, score: int) -> None:
        for (input_, did_action) in self.current_fight:
            output = [score if x else 0.0 for x in did_action]
            np_input = np.asarray(input_, dtype=np.float32)
            np_output = np.asarray(output, dtype=np.float32)
            self.train_data.append((np_input, np_output))
        self.current_fight = []

    def train(self) -> None:
        random.shuffle(self.train_data)
        loss_fn = tf.keras.losses.CategoricalCrossentropy(from_logits=True)
        self.model.compile(optimizer='adam', loss=loss_fn, metrics=['accuracy'])

        np_x = np.asarray([x for x,y in self.train_data])
        np_y = np.asarray([y for x,y in self.train_data])

        self.model.evaluate(np_x, np_y, verbose=2)
        self.model.fit(np_x, np_y, epochs=2)
        self.model.evaluate(np_x, np_y, verbose=2)
        self.train_data = []
