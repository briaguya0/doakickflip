#!/usr/bin/env python3
"""Call out tricks to a running "Live Skate-Tricks" goal (test app for the mod).

Usage:
  call_trick.py --thugpro DIR TRICK [TRICK ...]   e.g. Air_SquareL "Air_CircleU x2"
  call_trick.py --thugpro DIR                     read tricks from stdin, one per line
  call_trick.py --thugpro DIR --reset             create/clear the inbox

Writes THUGPRO_DIR/User/Data/doakickflip/inbox.qb, which the mod polls every
0.1 s while live mode is active; tricks are called out in the order sent, one
per engine add. State (last seq, recent requests) is kept alongside in
inbox.json. The .qb is replaced atomically so the game never reads a partial file.

Inbox format (compiled QB): doakickflip_inbox = [ { seq = N
goal_tetris_key_combos = [ <combo> ] } ... ], oldest first, seq increasing.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import qbc
from tricks import combo_q, parse_trick

KEEP = 32  # recent requests kept in the inbox


class Inbox:
    def __init__(self, thugpro_dir):
        self.dir = os.path.join(thugpro_dir, 'User', 'Data', 'doakickflip')
        self.qb = os.path.join(self.dir, 'inbox.qb')
        self.state_path = os.path.join(self.dir, 'inbox.json')
        try:
            self.state = json.load(open(self.state_path))
        except (OSError, ValueError):
            self.state = {'seq': 0, 'requests': []}

    def reset(self):
        # keep seq increasing so a running game never sees an old number again
        self.state['requests'] = []
        self.write()

    def send(self, combo, taps):
        self.state['seq'] += 1
        self.state['requests'].append({'seq': self.state['seq'], 'combo': combo, 'taps': taps})
        self.state['requests'] = self.state['requests'][-KEEP:]
        self.write()
        return self.state['seq']

    def write(self):
        os.makedirs(self.dir, exist_ok=True)
        lines = ['doakickflip_inbox = [']
        for r in self.state['requests']:
            lines.append(f"{{ seq = {r['seq']} goal_tetris_key_combos = [ {combo_q(r['combo'], r['taps'])} ] }}")
        lines.append(']')
        data = qbc.compile_text('\n'.join(lines) + '\n')
        tmp = self.qb + '.tmp'
        with open(tmp, 'wb') as f:
            f.write(data)
        for attempt in range(50):  # on Windows the game may briefly hold the file open
            try:
                os.replace(tmp, self.qb)
                break
            except PermissionError:
                time.sleep(0.02)
        else:
            raise
        json.dump(self.state, open(self.state_path, 'w'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--thugpro', required=True)
    ap.add_argument('--reset', action='store_true')
    ap.add_argument('tricks', nargs='*')
    args = ap.parse_args()

    inbox = Inbox(args.thugpro)
    if args.reset:
        inbox.reset()
        print(f'inbox cleared: {inbox.qb}')
        return

    def call(text):
        try:
            t = parse_trick(text)
        except ValueError as e:
            print(f'  ! {e}', file=sys.stderr)
            return
        if t:
            seq = inbox.send(*t)
            print(f'  #{seq} {t[0]}' + (f' x{t[1]}' if t[1] > 1 else ''))

    if args.tricks:
        for t in args.tricks:
            call(t)
    else:
        if sys.stdin.isatty():
            print('type tricks (e.g. Air_SquareL, Air_CircleU x2), ctrl-d to quit')
        for line in sys.stdin:
            call(line)


if __name__ == '__main__':
    main()
