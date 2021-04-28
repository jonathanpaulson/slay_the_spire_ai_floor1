# Watcher vs. cultist floor 1

from collections import defaultdict
from typing import List
import random

import numpy as np
import tensorflow as tf

from agent import Agent, EndTurn, Play, Input, Output
from data import Card, Stance

def inputToNeural(state: Input, action: Output) -> List[float]:
    ans = []
    ans.append(state.current_hp/100.) # 1
    ans.append(state.their_hp/100.) # 2
    ans.append(state.energy/3.) # 3
    ans.append(state.incomingDamage()/20.) # 4
    ans.append(state.turn/5.) # 5
    ans.append(1.0 if state.my_stance == Stance.Empty else 0.0) # 6
    ans.append(1.0 if state.my_stance == Stance.Wrath else 0.0) # 7
    ans.append(1.0 if state.my_stance == Stance.Calm else 0.0) # 8
    for lst in [state.hand, state.deck, state.discard]: # 23
        for card in list(Card):
            count = lst.count(card)
            ans.append(count/5.)
    for a in Output.goodActions(): # 27
        ans.append(1.0 if a==action else 0.0)
    assert len(ans) == 27
    return ans

class NeuralNet(Agent):
    def __init__(self) -> None:
        self.current_fight = []
        self.train_data = []
        self.training = 10

        self.model = tf.keras.models.Sequential([
            tf.keras.layers.Flatten(input_shape=(27,)),
            tf.keras.layers.Dense(30, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(30, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1)
        ])

    def act(self, state: Input) -> Output:

        inputs_ : List[List[float]] = []
        for action in Output.goodActions():
            input_ = inputToNeural(state, action)
            inputs_.append(input_)

        np_input = np.asarray(inputs_)
        scores = self.model(np_input).numpy()


        scored_actions: List[Tuple[float, List[float], Output]] = []
        for i,action in enumerate(Output.goodActions()):
            #input_ = inputToNeural(state, action)
            #np_input = np.expand_dims(np.asarray(input_, dtype=np.float32), axis=0)
            scored_actions.append((scores[i], inputs_[i], action))

        scored_actions = list(reversed(sorted(scored_actions)))

        if self.training>0 and random.randint(1,100) <= self.training:
            random.shuffle(scored_actions)

        for (score, input_, action) in scored_actions:
            if state.is_legal(action):
                self.current_fight.append((input_, score))
                return action
        return EndTurn()

    def fight_over(self, score: int) -> None:
        for (input_, _prediction) in self.current_fight:
            np_input = np.asarray(input_, dtype=np.float32)
            np_output = np.asarray([score], dtype=np.float32)
            self.train_data.append((np_input, np_output))
        self.current_fight = []

    def train(self) -> None:
        random.shuffle(self.train_data)

        #loss_fn = tf.keras.losses.CategoricalCrossentropy(from_logits=True)
        loss_fn = tf.keras.losses.MeanSquaredError()
        self.model.compile(optimizer='adam', loss=loss_fn, metrics=['accuracy'])

        np_x = np.asarray([x for x,y in self.train_data])
        np_y = np.asarray([y for x,y in self.train_data])

        self.model.evaluate(np_x, np_y, verbose=2)
        self.model.fit(np_x, np_y, epochs=5)
        self.model.evaluate(np_x, np_y, verbose=2)
        self.train_data = []
