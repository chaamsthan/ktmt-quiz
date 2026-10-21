#!/usr/bin/env python3
"""Own the temporary preview for parallel browser suites, or test public URL.

uv run --with playwright==1.60.0 python tools/run_quiz_checks.py
uv run --with playwright==1.60.0 python tools/run_quiz_checks.py --url https://chaamsthan.github.io/ktmt-quiz/
"""
import argparse
import functools
import http.server
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url')
    args=parser.parse_args();server=None
    if args.url:url=args.url
    else:
        handler=functools.partial(QuietHandler,directory=str(ROOT))
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        url=f'http://127.0.0.1:{server.server_port}/'
    print('Browser target: '+url,flush=True)
    scripts=['test_nmmmh.py','test_nmmmh_upgrade.py','test_ktmt_chapter2.py']
    failures=[]
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            running={executor.submit(subprocess.run,[sys.executable,str(ROOT/'tools'/script),'--url',url],
                                      cwd=ROOT,capture_output=True,text=True):script for script in scripts}
            for future in as_completed(running):
                result=future.result();script=running[future]
                print(f'{script}: exit {result.returncode}\n{result.stdout}{result.stderr}',flush=True)
                if result.returncode:failures.append(script)
    finally:
        if server:server.shutdown();server.server_close()
    if failures:raise SystemExit('FAILED: '+', '.join(failures))
    print('ALL THREE BROWSER SUITES PASSED',flush=True)


if __name__=='__main__':main()
