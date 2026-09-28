#!/usr/bin/env python3
"""Send trick requests to a running "Do a Kickflip!" session.

Usage:
  call_trick.py --thugpro DIR [--user NAME] TRICK [TRICK ...]   e.g. Kickflip "Pop Shove-It"
  call_trick.py --thugpro DIR                                  read stdin: "Kickflip" or "user: Kickflip"
  call_trick.py --thugpro DIR --reset                          create/clear the inbox
  call_trick.py --thugpro DIR --max-pending 15                 change the cap (with or without tricks)

Tricks are the game's display names, matched exactly (case included):
Kickflip, Heelflip, Impossible, Pop Shove-It, Varial Kickflip, Melon, Indy,
Manual, Nose Manual, ... Grinds carry a direction (BS 50-50, FS Nosegrind).

Writes THUGPRO_DIR/User/Data/doakickflip/inbox.qb, which the mod polls about
every 0.1 s while the mode is active. State (last seq, recent requests) is kept
alongside in inbox.json; the .qb is replaced atomically so the game never reads
a partial file.

Inbox format (compiled QB), oldest first, seq increasing:
    doakickflip_inbox = [ { seq = N trick = "Kickflip" user = "name" } ... ]
    doakickflip_inbox_settings = { max_pending = 8 }
The game re-reads the settings on every poll: more than max_pending tricks
pending makes the skater bail, and the list turns red from 75% of it.
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import qbc

KEEP = 32  # recent requests kept in the inbox
DEFAULT_SETTINGS = {'max_pending': 8}
TRICK = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .'!&-]{0,39}")
USER = re.compile(r'[A-Za-z0-9_]{1,25}')


def check(trick, user):
    if not TRICK.fullmatch(trick):
        raise ValueError(f'not a trick name: {trick!r}')
    if not USER.fullmatch(user):
        raise ValueError(f'not a user name: {user!r}')


class Inbox:
    def __init__(self, thugpro_dir):
        self.dir = os.path.join(thugpro_dir, 'User', 'Data', 'doakickflip')
        self.qb = os.path.join(self.dir, 'inbox.qb')
        self.state_path = os.path.join(self.dir, 'inbox.json')
        try:
            self.state = json.load(open(self.state_path))
        except (OSError, ValueError):
            self.state = {'seq': 0, 'requests': []}
        # entries from the key-combo era of the format don't carry a trick name
        self.state['requests'] = [r for r in self.state['requests'] if 'trick' in r]
        self.state['settings'] = {**DEFAULT_SETTINGS, **self.state.get('settings', {})}

    def set_max_pending(self, n):
        if not 1 <= n <= 30:
            raise ValueError('max pending must be 1-30 (the list has 30 slots at most)')
        self.state['settings']['max_pending'] = n
        self.write()

    def reset(self):
        # keep seq increasing so a running game never sees an old number again
        self.state['requests'] = []
        self.write()

    def send(self, trick, user):
        check(trick, user)
        self.state['seq'] += 1
        self.state['requests'].append({'seq': self.state['seq'], 'trick': trick, 'user': user})
        self.state['requests'] = self.state['requests'][-KEEP:]
        self.write()
        return self.state['seq']

    def write(self):
        os.makedirs(self.dir, exist_ok=True)
        lines = ['doakickflip_inbox = [']
        for r in self.state['requests']:
            lines.append(f"{{ seq = {r['seq']} trick = \"{r['trick']}\" user = \"{r['user']}\" }}")
        lines.append(']')
        lines.append(f"doakickflip_inbox_settings = {{ max_pending = {int(self.state['settings']['max_pending'])} }}")
        data = qbc.compile_text('\n'.join(lines) + '\n')
        tmp = self.qb + '.tmp'
        with open(tmp, 'wb') as f:
            f.write(data)
        for _ in range(50):  # on Windows the game may briefly hold the file open
            try:
                os.replace(tmp, self.qb)
                break
            except PermissionError:
                time.sleep(0.02)
        else:
            raise PermissionError(f'could not replace {self.qb}')
        json.dump(self.state, open(self.state_path, 'w'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--thugpro', required=True)
    ap.add_argument('--user', default='you')
    ap.add_argument('--reset', action='store_true')
    ap.add_argument('--max-pending', type=int, help='bail when more than this many tricks are pending (default 8)')
    ap.add_argument('tricks', nargs='*')
    args = ap.parse_args()

    inbox = Inbox(args.thugpro)
    if args.max_pending is not None:
        try:
            inbox.set_max_pending(args.max_pending)
        except ValueError as e:
            sys.exit(str(e))
        print(f'max pending: {args.max_pending}')
        if not args.tricks and not args.reset:
            return
    if args.reset:
        inbox.reset()
        print(f'inbox cleared: {inbox.qb}')
        return

    def call(text, user):
        text = text.strip()
        if not text:
            return
        if ':' in text:
            user, text = (part.strip() for part in text.split(':', 1))
        try:
            seq = inbox.send(text, user)
        except ValueError as e:
            print(f'  ! {e}', file=sys.stderr)
            return
        print(f'  #{seq} {user}: {text}')

    if args.tricks:
        for t in args.tricks:
            call(t, args.user)
    else:
        if sys.stdin.isatty():
            print('type tricks (e.g. Kickflip, or "someone: Melon"), ctrl-d to quit')
        for line in sys.stdin:
            call(line, args.user)


if __name__ == '__main__':
    main()
