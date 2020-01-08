from operator import setitem, getitem, gt, ge, contains
from functools import partial, reduce
from logging import debug, basicConfig, DEBUG
from string import whitespace


# region Utilities


def binary_compose(f, g):
    return lambda *args, **kwargs: f(g(*args, **kwargs))


def compose(*functions):
    return reduce(binary_compose, functions)


def selector(property):
    def get(store):
        return getitem(store, property)

    def set(value, store):
        return {**store, property: value}

    return dict(set=set, get=get)


def property(property):
    def targetable(target):
        return target[property]
    return targetable


def get(lens, store):
    return property('get')(lens)(store)


def set(lens, value, store):
    return property('set')(lens)(value, store)


def apply(lens, f, store):
    return set(lens, f(get(lens, store)), store)


def greatherThanOne(x):
    return partial(ge, x)(1)


def append(*values):
    def to(target):
        return [*target, *values]
    return to


def extends(values):
    def to(target):
        return [*target, *values]
    return to


def first(expression):
    return expression[0]


def last(expression):
    return expression[-1]


def tail(expression):
    return expression[1:]


def has(source):
    return partial(contains, source)


def has_any(source):
    return compose(any, partial(map, has(source)))


def repeat(times):
    def text(expression):
        return expression * times
    return text
# endregion


# region Business
def expressionIsLongEnough(expression):
    return greatherThanOne(len(expression))


def expressionIsNotLongEnough(expression):
    return not expressionIsLongEnough(expression)


def transition_starts_with(transition, state):
    return state in transition and transition.index(state) == 0


def search_current_transitions(transitions):
    def starts_with(state):
        return {
            transition: value
            for transition, value in transitions.items()
            if transition_starts_with(transition, state)
        }
    return starts_with


def could_be_epsilon_transition(alphabets):
    return any( [ None in alphabet for alphabet in alphabets ] )


def is_epsilon_transition(transitions, transition):
    return None in property(transition)(transitions)


def is_not_epsilon_transition(transitions, transition):
    return not is_epsilon_transition(transitions, transition)


def is_transition(transitions, transition, symbol):
    return symbol in property(transition)(transitions)


def robot(states, alphabet, transitions, initial_state, acceptance_states, epsilon=None):

    # region Store
    store = dict(
        state=initial_state,
        states=[],
        transitions=transitions,
        epsilon=epsilon,
        transition=None
    )

    select_state = selector('state')
    get_state = partial(get, select_state)
    set_state = partial(set, select_state)

    select_states = selector('states')
    get_states = partial(get, select_states)
    set_states = partial(set, select_states)
    apply_states = partial(apply, select_states)
    # endregion

    # region Currying
    get_current_transitions = search_current_transitions(transitions)
    contains = has_any(acceptance_states)
    # endregion

    def transite(store, expression):
        current_transitions = get_current_transitions(get_state(store))

        if expressionIsNotLongEnough(expression) and not could_be_epsilon_transition(current_transitions.values()):
            next_state = get_state(store) 
            next_states = get_states(
                set_states( [ *get_states(store), next_state ] , store)
            )

            return next_states

        for current_transition in current_transitions:
        
            if is_epsilon_transition(transitions, current_transition):
                debug(
                    f' Transiting from state { first(current_transition) } to { last(current_transition) } with epsilon transition  '
                )

                next_state = last(current_transition)
                next_states = transite(
                    set_state(next_state, store), 
                    expression
                ) 

                store = set_states(next_states, store)

            if expressionIsLongEnough(expression) and is_transition(transitions, current_transition, first(expression)):  
                debug(
                    f' Transiting from state { first(current_transition) } to { last(current_transition) } with symbol { first(expression) }  '
                )

                next_state = last(current_transition)
                next_states = transite(
                    set_state(next_state, store), 
                    tail(expression)
                )

                store = set_states(next_states, store)


        debug(
            f'{get_states(store)}'
        )
        return get_states(store)

    def evaluate(expression):
        return contains(transite(store, expression))

    return evaluate

# endregion
