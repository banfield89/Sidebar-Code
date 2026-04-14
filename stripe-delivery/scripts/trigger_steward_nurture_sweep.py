"""SP3 Session 1 stub for the Steward nurture-sweep cron service.

Session 7 will replace this with HTTP POST logic that hits a nurture
enrollment admin endpoint. For Session 1 this stub exists so render.yaml
can declare the cron service and Kyle can re-apply the Blueprint once.
"""

from __future__ import annotations

import sys


def main() -> int:
    print("SP3 Session 1 stub: trigger_steward_nurture_sweep.py")
    print("Session 7 will implement the HTTP-trigger for nurture sweep")
    return 0


if __name__ == "__main__":
    sys.exit(main())
