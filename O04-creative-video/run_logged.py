#!/usr/bin/env python3
import argparse, datetime as dt, json, os, pathlib, subprocess, sys, time

p = argparse.ArgumentParser()
p.add_argument('--label', required=True)
p.add_argument('--cwd', default=os.getcwd())
p.add_argument('--network', action='append', default=[])
p.add_argument('command', nargs=argparse.REMAINDER)
a = p.parse_args()
if a.command and a.command[0] == '--':
    a.command = a.command[1:]
if not a.command:
    raise SystemExit('command required')
root = pathlib.Path(__file__).resolve().parent
logs = root / 'logs'
logs.mkdir(parents=True, exist_ok=True)
stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
stdout_path = logs / f'{stamp}-{a.label}.stdout.log'
stderr_path = logs / f'{stamp}-{a.label}.stderr.log'
start = time.monotonic()
started = dt.datetime.now(dt.timezone.utc).isoformat()
with stdout_path.open('wb') as out, stderr_path.open('wb') as err:
    cp = subprocess.run(a.command, cwd=a.cwd, stdout=out, stderr=err)
ended = dt.datetime.now(dt.timezone.utc).isoformat()
rec = {
    'label': a.label,
    'started_utc': started,
    'ended_utc': ended,
    'duration_s': round(time.monotonic() - start, 6),
    'cwd': str(pathlib.Path(a.cwd).resolve()),
    'argv': a.command,
    'network_targets': a.network,
    'exit_code': cp.returncode,
    'stdout_log': str(stdout_path),
    'stderr_log': str(stderr_path),
}
with (logs / 'process-network-log.jsonl').open('a', encoding='utf-8') as f:
    f.write(json.dumps(rec, sort_keys=True) + '\n')
print(json.dumps(rec, indent=2))
if stdout_path.stat().st_size:
    print('--- stdout tail ---')
    print(stdout_path.read_text(errors='replace')[-4000:])
if stderr_path.stat().st_size:
    print('--- stderr tail ---', file=sys.stderr)
    print(stderr_path.read_text(errors='replace')[-4000:], file=sys.stderr)
raise SystemExit(cp.returncode)
