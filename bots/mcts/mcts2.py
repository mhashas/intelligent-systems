from api import State, Planet
import random
import math


class Bot:
    __max_depth = -1
    __randomize = True

    def __init__(self, randomize=True, depth=4):
        """
        :param randomize: Whether to select randomly from moves of equal value (or to select the first always)
        :param depth:
        """
        self.__randomize = randomize
        self.__max_depth = depth

    def get_move(self, state):
        # type: (State) -> tuple[int, int]

        move = self.value(state, 10)

        return move  # to do nothing, return None

    # Monte Carlo Search Tree Implementation
    def value(self, rootstate, depth=0):
        # type: (State, int) -> tuple[float, tuple[int, int]]
        """
        Return the value of this state and the associated move
        :param state:
        :param depth:
        :return: A tuple containing the value of this state, and the best move for the player currently to move
        """
        rootnode = MCSTNode(state=rootstate)

        for i in range(depth):
            node = rootnode
            state = rootstate.clone()

            # select
            while node.untriedMoves == [] and node.childNodes != []: # while node is not fully expanded and it has child nodes
                node = node.MCSTSelectChild()
                state = state.next(node.move)

            # expand
            if not state.finished():
                move = random.choice(node.untriedMoves)
                state = state.next(move)
                node.addChild(move, state)

            # rollout
            while not state.finished() :
                moves = getMoves(state)
                state = state.next(random.choice(moves))

            # backpropagate
            while node != None: # backpropagate from the expanded node and work back to the root node
                node.update(1 if state.winner() == node.player else 0)
                node = node.parent

        move = sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited

        if move is None:
            return None

        planets = state.planets()
        src_planet = planets[move[0]]
        dst_planet = planets[move[1]]

        if (rootstate.garrison(src_planet) / 2 <= rootstate.garrison(dst_planet)): # doesn't make sense to attack, not a good result, return none
            return None
        else:
            return move


class MCSTNode:
    """
        A node in the Monte Carlo Search tree.
    """

    def __init__(self, move=None, parent=None, state=None):
        self.move = move  # previous move made in order to reach this node
        self.parent = parent  # parent of this node in the search tree
        self.childNodes = []
        self.wins = 0  # wins are always from the viewpoint of the player that just moved
        self.visits = 0
        self.untriedMoves = getMoves(state)  # moves that are going to become future child nodes
        self.player = state.whose_turn()  # player that just moved

    def MCSTSelectChild(self):
        """
            We are using the UCB1 formula / heuristic in order to select a child node.

            c.wins / c.visits + 4 + sqrt(2*log(self.visits)/c.visits))
        """

        selectedChild = sorted(self.childNodes, key=lambda c: c.wins / max(1,c.visits) + math.sqrt(2 * math.log(self.visits) / max(1,c.visits)))[-1]
        return selectedChild

    def addChild(self, move, state):
        node = MCSTNode(move=move, parent=self, state=state)
        self.untriedMoves.remove(move)
        self.childNodes.append(node)
        return node

    def update(self, result):
        self.visits += 1
        self.wins += result


def getMoves(state):
    mine = state.planets(state.whose_turn())
    all = state.planets()

    moves = []
    for m in mine:
        if state.garrison(m) > 1:
            for a in all:
                exists, incoming = fleetAnalysis(state,a,m) # does this fleet already exist ? is there an incoming attack to this source ?
                if (state.garrison(m) > state.garrison(a) * 2 and not exists and not incoming): # only append if we are conquering and we are not already attacking
                    moves.append((m.id(), a.id()))

    if len(moves) == 0:
        moves.append(None)

    return moves


def fleetAnalysis(state, source, destination):
    exists = False
    incoming = False
    for fleet in state.fleets():
        if fleet.source() == source and fleet.target() == destination:
            exists = True
        if fleet.target == source:
            incoming = True


    return exists, incoming
