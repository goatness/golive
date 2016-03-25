import collections
import random
import simpy

RANDOM_SEED = 555
PLAYERS_PER_TABLE = 9
SIM_TIME = 120

def grinder(env, table, num_players, casino):
    """ A grinder (poker player) tries to sit down at
       a poker table in a casino. """

    with casino.checkin.request() as grinder_turn:
        result = yield grinder_turn | casino.full[table]

        if grinder_turn not in result:
            casino.num_renegers[table] += 1
            env.exit()

        if casino.available[table] < num_players:
            yield env.timeout(1)
            env.exit()

        casino.available[table] -= num_players
        if casino.available[table] < 2:
            casino.full[table].succeed()
            casino.when_full[table] = env.now
            casino.available[table] = 0
        yield env.timeout(1)

def player_arrival(env, casino):
    while True:
        yield env.timeout(random.expovariate(1/0.5))
    
        table = random.choice(casino.tables)
        num_players = 1
        if casino.available[table]:
            env.process(grinder(env, table, num_players, casino))

Casino = collections.namedtuple('Casino', 'checkin, tables, available, '
                                'full, when_full, '
                                'num_renegers')

print('Poker room sim')
random.seed(RANDOM_SEED)
env = simpy.Environment()

checkin = simpy.Resource(env, capacity=1)
tables = ['NL 1/2 Hold \'em', 'Omaha PLO 2/5', 'NL 2/5 Hold \'em']
available = {table: PLAYERS_PER_TABLE for table in tables}
full = {table: env.event() for table in tables}
when_full = {table: None for table in tables}
num_renegers = {table: 0 for table in tables}
casino = Casino(checkin, tables, available, full, when_full, num_renegers)

env.process(player_arrival(env, casino))
env.run(until=SIM_TIME)

for table in tables:
    if casino.full[table]:
        print('Table "%s" full %.1f minutes after check in opened '
        % (table, casino.when_full[table]))
    
        print('Number of players leaving queue when table full: %s'
        % casino.num_renegers[table])


