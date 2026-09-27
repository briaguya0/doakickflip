#!/usr/bin/env python3
"""Pretend to be Twitch chat: send random trick requests to "Do a Kickflip!".

Usage: fake_chat.py --thugpro DIR [--rate N] [--burst P] [--tricks A,B,...] [--seed S]

Start it, then skate: requests arrive at random (on average --rate per minute),
from random made-up users, and now and then several at once (--burst is the
chance that a request brings company). Uses the same inbox as call_trick.py,
so the game can't tell the difference. Ctrl-C to stop.
"""
import argparse
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from call_trick import Inbox

# Exact display names from the trick scripts; flips, grabs and manuals (grinds
# carry an FS/BS prefix, so they're left out of the default list).
DEFAULT_TRICKS = [
    'Kickflip', 'Heelflip', 'Impossible', 'Pop Shove-It', 'Hardflip',
    'Varial Kickflip', '360 Flip', 'Melon', 'Indy', 'Nosegrab', 'Tailgrab',
    'Madonna', 'Method', 'Airwalk', 'Benihana', 'Manual', 'Nose Manual',
]
USER_PARTS = (['sk8', 'tony', 'grind', 'kick', 'flip', 'rail', 'vert', 'ollie', 'bail', 'combo'],
              ['lord', 'fan', 'god', 'king', 'rat', 'enjoyer', 'goblin', 'wizard', 'dad', 'kid'])


def fake_user(rng):
    return rng.choice(USER_PARTS[0]) + rng.choice(USER_PARTS[1]) + str(rng.randint(1, 999))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--thugpro', required=True)
    ap.add_argument('--rate', type=float, default=10, help='average requests per minute (default 10)')
    ap.add_argument('--burst', type=float, default=0.15, help='chance a request comes with 1-3 more (default 0.15)')
    ap.add_argument('--tricks', help='comma-separated trick names (default: common flips/grabs/manuals)')
    ap.add_argument('--seed', type=int)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    tricks = [t.strip() for t in args.tricks.split(',')] if args.tricks else DEFAULT_TRICKS
    users = [fake_user(rng) for _ in range(12)]
    inbox = Inbox(args.thugpro)
    print(f'fake chat: ~{args.rate:g} requests/min from {len(users)} users, ctrl-c to stop')
    try:
        while True:
            time.sleep(rng.expovariate(args.rate / 60))
            count = 1 + (rng.randint(1, 3) if rng.random() < args.burst else 0)
            for _ in range(count):
                user, trick = rng.choice(users), rng.choice(tricks)
                seq = inbox.send(trick, user)
                print(f'  #{seq} {user}: {trick}', flush=True)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
