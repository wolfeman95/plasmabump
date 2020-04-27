import threading
import subprocess
import requests
import dateutil.parser
import time
import regex as re


class DuelStats:
    payload = {'region': 'NA',
             'gametype': 'Casual Duel',
             'ruleset': 'ZDDL', 
             'player1': '', 'player2': '',
             'highest_elo': 0,
             'player1_ip': '', 'player2_ip': '',
             'map': '',
             'winner': '', 'loser': '',
             'date_played': '',
             'match_length': 0,
             'player1_score': 0, 'player2_score': 0,
             'player1_spree': 0, 'player2_spree': 0,
             'player1_best_spree': 0, 'player2_best_spree': 0,
             'player1_total_frags': 0, 'player2_total_frags': 0,
             'player1_total_deaths': 0, 'player2_total_deaths': 0,
             'player1_ssg_frags': 0, 'player2_ssg_frags': 0,
             'player1_bfg_frags': 0, 'player2_bfg_frags': 0,
             'player1_bfg_direct_frags': 0, 'player2_bfg_direct_frags': 0,
             'player1_bfg_tracer_frags': 0, 'player2_bfg_tracer_frags': 0,
             'player1_rl_frags': 0, 'player2_rl_frags': 0,
             'player1_plas_frags': 0, 'player2_plas_frags': 0,
             'player1_cg_frags': 0, 'player2_cg_frags': 0,
             'player1_sg_frags': 0, 'player2_sg_frags': 0,
             'player1_pistol_frags': 0, 'player2_pistol_frags': 0,
             'player1_fist_frags': 0, 'player2_fist_frags': 0,
             'player1_saw_frags': 0, 'player2_saw_frags': 0,
             'player1_tele_frags': 0, 'player2_tele_frags': 0,
             'player1_total_suicides': 0, 'player2_total_suicides': 0, 
             'player1_rl_suicides': 0, 'player2_rl_suicides': 0,
             'player1_lava_suicides': 0, 'player2_lava_suicides': 0,
             'player1_self_suicides': 0, 'player2_self_suicides': 0,
             'player1_left': 0, 'player2_left': 0}

    payload_stats = {}

    def populate_stats(self, match_events):
        match_stats = self.payload.copy()
        match_stats.update({'region': match_events[0][0], 'gametype': match_events[0][1], 'ruleset': match_events[0][2],
                           'player1': match_events[0][3], 'player2': match_events[0][4], 'map': match_events[0][5], 'date_played': match_events[0][6]})

        nick_to_player = {match_stats['player1']: 'player1', match_stats['player2']: 'player2'}
        sprees = {'player1_current': 0, 'player1_best': 0, 'player2_current': 0, 'player2_best': 0}

        for event in match_events[1:-1]: #everything except header / footer
            frag_event = '{}_{}_{}'.format(nick_to_player[event[2]], event[3], event[1])  # weapon frag: player1_ssg_frags
            total_event = '{}_total_{}'.format(nick_to_player[event[2]], event[1])  # total event: player1_total_frags
            death_event = '{}_total_deaths'.format((nick_to_player[event[2]] if event[1] == 'suicides' else nick_to_player[event[4]])) 

            current = '{}_current'.format(nick_to_player[event[2]])  # sprees: player1_current or player2_current
            died_current = '{}_current'.format((nick_to_player[event[2]] if event[1] == 'suicides' else nick_to_player[event[4]]))
            best = '{}_best'.format(nick_to_player[event[2]])

            for any in [frag_event, total_event, death_event]:
                match_stats.update({any: match_stats[any] + 1})
          
            sprees.update({current: sprees[current] + 1, died_current: 0})
            sprees.update({best: sprees[current] if sprees[current] > sprees[best] else sprees[best]})

        match_stats.update({'player1_ip': '999', 'player2_ip': '999', 'winner': match_events[-1][2], 'match_length': match_events[-1][1],
                           'loser': (match_stats['player1'] if match_stats['player2'] == match_events[-1][2] else match_stats['player2']),
                           'player1_best_spree': sprees['player1_best'], 'player2_best_spree': sprees['player2_best'],
                           'player1_score': match_stats['player1_total_frags'] - match_stats['player1_total_suicides'],
                           'player2_score': match_stats['player2_total_frags'] - match_stats['player2_total_suicides'],
                           'player1_bfg_frags': match_stats['player1_bfg_direct_frags'] + match_stats['player1_bfg_tracer_frags'],
                           'player2_bfg_frags': match_stats['player2_bfg_direct_frags'] + match_stats['player2_bfg_tracer_frags'],
                           })

        self.payload_stats = match_stats

    def post_match(self):
        try:
            r = requests.post("#api url", data=self.payload_stats, auth=('user', 'pass'))
            r.raise_for_status()
            print("DUEL POST status -- " + str(r.status_code))
        except requests.exceptions.HTTPError as e:
            print("DUEL MATCH DID NOT POST - ", e, "POST status", r.status_code, r.text)

        self.payload_stats.clear()

class BaseMessage:
    def __init__(self, stats, line):
        self.stats = stats
        self.line = line
        self.date_time = str(dateutil.parser.parse(" ".join(line.split()[0:2])[1:-1], dayfirst=True))

    def publish_message(self, line):
        print('got line: {}'.format(line, end=''))

    def publish_date(self):
        print('datetime: ', self.date_time)

class PlayerChatMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). <CHAT> ((.+)+)']

class PlayerConnectMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) has connected.']

class VoteRestartMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). Vote restart passed! .((.+)+)$']

class PlayerDisconnectMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) disconnected\. .((.+)+)$',
                r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) timed out\. .((.+)+)$']

    def parse(self, line, joined_players):
        for pattern in self.PATTERNS:
            m = re.match(pattern, line)
            if m is not None and m.group('player') in joined_players:
                joined_players.remove(m.group('player'))
                return True
        return False

class ChangedNameMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) changed (his|her) name to (?P<newnick>(.+)+)\.']

class PlayerJoinMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) joined the game.']

class PlayerSpectateMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player>(.+)+) became a spectator.']

class MapChangeMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). --- MAP(\d{2}): "(?P<map>(.+)+)" ---']

class MatchStartMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). The match has started.']

class MatchEndMessage(BaseMessage):
    PATTERNS = [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). Frag limit hit. Game won by (?P<winner>(.+)+)!',
                r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). Frag limit hit. (?P<winner>(.+)+) team wins!']

    def parse(self, line, match_events, time_start):
        winner = ''
        for pattern in self.PATTERNS:
            m = re.match(pattern, line)
            if m is not None:
                winner += m.group('winner')

        match_events.append(['game ended', int(time.perf_counter() - time_start), winner])
        x = DuelStats()
        x.populate_stats(match_events)
        x.post_match()

class PlayerDeathMessage(BaseMessage):
    PATTERNS = [
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) was splintered by (?P<fragger>(.+)+)'s BFG.", 'bfg_direct'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) couldn't hide from (?P<fragger>(.+)+)'s BFG.", 'bfg_tracer'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) rode (?P<fragger>(.+)+)'s rocket.", 'rl'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) almost dodged (?P<fragger>(.+)+)'s rocket.", 'rl'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) was splattered by (?P<fragger>(.+)+)'s super shotgun.", 'ssg'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) was mowed down by (?P<fragger>(.+)+)'s chaingun.", 'cg'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) chewed on (?P<fragger>(.+)+)'s boomstick.", 'sg'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) was melted by (?P<fragger>(.+)+)'s plasma gun.", 'plas'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) was tickled by (?P<fragger>(.+)+)'s pea shooter.", 'pistol'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) chewed on (?P<fragger>(.+)+)'s fist.", 'fist'],
        [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) was mowed over by (?P<fragger>(.+)+)\.', 'saw'],
        [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<victim>(.+)+) was telefragged by (?P<fragger>(.+)+)\.', 'tele'],
    ]

    def __init__(self, stats, line):
        self.stats = stats
        self.line = line

    def parse(self, line, time_start):
        for pattern in self.PATTERNS:
            m = re.match(pattern[0], line)
            if m is not None:
                #[ second , type , fragger, weapon, victim ]
                self.stats.append([int(time.perf_counter() - time_start), 'frags', m.group('fragger'), pattern[1], m.group('victim')])
        print('parse complete')
        print(self.stats)


class PlayerSuicideMessage(BaseMessage):
    PATTERNS = [
        [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player1>(.+)+) should have stood back.', 'rl'],
        [r".(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player1>(.+)+) mutated.", 'lava'],
        [r'.(\d{2})/(\d{2})/(\d{4}) (\d{2}):(\d{2}):(\d{2}). (?P<player1>(.+)+) suicides.', 'self'],
    ]

    def __init__(self, stats, line):
        self.stats = stats
        self.line = line

    def parse(self, line, time_start):
        for pattern in self.PATTERNS:
            m = re.match(pattern[0], line)
            if m is not None:
                self.stats.append([int(time.perf_counter() - time_start), 'suicides', m.group('player1'), pattern[1], None])
        self.publish_message(line)

def parse_line(match_events, line, time_start):
    parser = None
    match = None

    #frags
    if any(re.match(pattern[0], line) for pattern in PlayerDeathMessage.PATTERNS):
        parser = PlayerDeathMessage(match_events, time_start)

    #suicides
    if any(re.match(pattern[0], line) for pattern in PlayerSuicideMessage.PATTERNS):
        parser = PlayerSuicideMessage(match_events, time_start)

    if parser:
        parser.parse(line, time_start)

def stdout_reader(proc,):
    """
    Analyzing the server stdout
    """

    match_events = []
    map_playing = ""
    joined_players = []
    time_start = 0

    players_in_server = 0

    match_underway = False

    for l in iter(proc.stdout.readline, b''):
        line = l.decode('utf-8')
        print('got line: {}'.format(line, end=''))

        #chat
        if re.match(PlayerChatMessage.PATTERNS[0], line):
            print('chatter')
            continue

        #match start
        if re.match(MatchStartMessage.PATTERNS[0], line) and len(joined_players) == 2:
            match_events.clear()
            date_played = str(dateutil.parser.parse(line[1:20], dayfirst=True))
            time_start = time.perf_counter()
            match_underway = True
            match_events.append(['NA', 'Casual Duel', 'ZDDL', joined_players[0], joined_players[1], map_playing, date_played])

        #match end
        if any(re.match(pattern, line) for pattern in MatchEndMessage.PATTERNS):
            match_underway = False
            MatchEndMessage(match_events, line).parse(line, match_events, time_start)
            joined_players.clear()
            match_events.clear()

        #player connect
        if any(re.match(pattern, line) for pattern in PlayerConnectMessage.PATTERNS):
            players_in_server += 1

        # joined game
        if re.match(PlayerJoinMessage.PATTERNS[0], line):
            joined_players.append(re.match(PlayerJoinMessage.PATTERNS[0], line).group('player'))

        # spectate
        if re.match(PlayerSpectateMessage.PATTERNS[0], line):
            joined_players.remove(re.match(PlayerSpectateMessage.PATTERNS[0], line).group('player'))
            match_underway = False

        # player disconnect / timeout
        if any(re.match(pattern, line) for pattern in PlayerDisconnectMessage.PATTERNS):
            players_in_server -= 1
            if match_underway and PlayerDisconnectMessage(match_events, line).parse(line, joined_players):
                match_underway = False
            PlayerDisconnectMessage(match_events, line).parse(line, joined_players) 

        #map change
        if re.match(MapChangeMessage.PATTERNS[0], line):
            map_playing = re.match(MapChangeMessage.PATTERNS[0], line).group('map')
            joined_players.clear()
            match_events.clear()
            match_underway = False
            print('map changed to ', map_playing)

        # Callvote restart mid match, stat collection will break & start over
        if re.match(VoteRestartMessage.PATTERNS[0], line):
            match_events.clear()
            date_played = ""
            match_underway = False

        # player changed nickname
        if re.match(ChangedNameMessage.PATTERNS[0], line):
            first_nick = re.match(ChangedNameMessage.PATTERNS[0], line).group('player')
            if first_nick in joined_players:
                new_nick = re.match(ChangedNameMessage.PATTERNS[0], line).group('newnick')
                joined_players[joined_players.index(first_nick)] = new_nick
            else:
                pass

        if match_underway:
            parse_line(match_events, line, time_start)


def main():
    proc = subprocess.Popen(['./odasrv', '-i', '-u', '-config', 'casual_duel.cfg'], 
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)

    t = threading.Thread(target=stdout_reader, args=(proc,))
    t.start()
    t.join(timeout=None)


if __name__ == '__main__':
    main()
