#!/usr/bin/env python3
"""Merge every finished translation batch that has not been merged yet.

  tools/collect.py            validate + merge each work/batches/*.th.jsonl not listed in work/merged.txt
  tools/collect.py --status   list batches: merged / ready / invalid / pending (no output yet)

A batch that fails validation is reported and left alone; the rest are merged. Merging is idempotent
(rows already in translations/ are skipped), so re-running is always safe.
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.dirname(HERE)
B = os.path.join(MOD, 'work', 'batches')
LEDGER = os.path.join(MOD, 'work', 'merged.txt')


def run(*args):
    return subprocess.run([sys.executable, os.path.join(HERE, 'batch.py'), *args],
                          capture_output=True, text=True)


def main(status_only):
    merged = set(open(LEDGER).read().split()) if os.path.isfile(LEDGER) else set()
    inputs = sorted(p for p in glob.glob(os.path.join(B, '*.jsonl')) if not p.endswith('.th.jsonl'))
    state = {'merged': [], 'ready': [], 'invalid': [], 'pending': []}
    for inp in inputs:
        name = os.path.basename(inp)[:-6]
        out = inp[:-6] + '.th.jsonl'
        if name in merged:
            state['merged'].append(name)
        elif not os.path.isfile(out):
            state['pending'].append(name)
        elif run('validate', inp, out).returncode == 0:
            state['ready'].append(name)
        else:
            state['invalid'].append(name)
    for k, v in state.items():
        print(f'{k:8} {len(v):4}  {" ".join(v[:12])}{" ..." if len(v) > 12 else ""}')
    if status_only or not state['ready']:
        return 0
    outs = [os.path.join(B, n + '.th.jsonl') for n in state['ready']]
    r = run('merge', '-', *outs)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr)
    if r.returncode == 0:
        with open(LEDGER, 'a') as f:
            f.write('\n'.join(state['ready']) + '\n')
    return r.returncode


if __name__ == '__main__':
    sys.exit(main('--status' in sys.argv))
