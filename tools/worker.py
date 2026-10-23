"""Provided training collector; student answers remain Bash scripts."""
import argparse
import os
import signal
import time

parser = argparse.ArgumentParser()
parser.add_argument("--token", required=True)
parser.add_argument("--log", required=True)
args = parser.parse_args()
running = True


def stop(signum, frame):
    global running
    running = False


for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(sig, stop)
with open(args.log, "a", buffering=1) as stream:
    stream.write(f"START {args.token} pid={os.getpid()}\n")
    number = 0
    while running:
        stream.write(f"TICK {args.token} {number}\n")
        number += 1
        time.sleep(0.15)
    stream.write(f"STOP {args.token}\n")
