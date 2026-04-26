"""
main.py
-------
Interactive CLI menu for the Advanced Brute Force Login Simulator.
Ties together targetlogin.py and bruteforce.py into a user-friendly
educational demonstration.

Run with:  python main.py

EDUCATIONAL USE ONLY — simulation runs entirely in-process.
No real network connections are made.
"""

import os
import sys
import time
from pathlib import Path

# ── Colour helpers ──────────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    RED    = Fore.RED
    GREEN  = Fore.GREEN
    YELLOW = Fore.YELLOW
    CYAN   = Fore.CYAN
    BLUE   = Fore.BLUE
    BOLD   = Style.BRIGHT
    RESET  = Style.RESET_ALL
except ImportError:
    RED = GREEN = YELLOW = CYAN = BLUE = BOLD = RESET = ""


# ── Local modules ────────────────────────────────────────────────────────────
from targetlogin import LoginSystem, LoginConfig
from bruteforce  import (
    AttackConfig,
    DictionaryAttacker,
    BruteForceAttacker,
    UsernameEnumerator,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BASE_DIR       = Path(__file__).parent
USERNAMES_FILE = BASE_DIR / "usernames.txt"
PASSWORDS_FILE = BASE_DIR / "passwords.txt"
LOGS_FILE      = BASE_DIR / "logs.txt"


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

BANNER = f"""
{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║     ADVANCED BRUTE FORCE LOGIN SIMULATOR                     ║
║     Cybersecurity Educational Tool  •  Python 3              ║
╠══════════════════════════════════════════════════════════════╣
║  EDUCATIONAL USE ONLY — local in-process simulation          ║
║  No real network traffic is generated.                       ║
╚══════════════════════════════════════════════════════════════╝
{RESET}"""

MENU = f"""
{BOLD}  ┌─────────────────────────────────────┐
  │          MAIN MENU                  │
  ├─────────────────────────────────────┤
  │  1 │ Dictionary Attack              │
  │  2 │ Brute Force Attack             │
  │  3 │ Username Enumeration           │
  │  4 │ View Logs                      │
  │  5 │ Reset All Lockouts             │
  │  6 │ Attack Settings                │
  │  7 │ Exit                           │
  └─────────────────────────────────────┘{RESET}"""


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def load_file(path: Path, label: str) -> list[str]:
    """Read a text file and return non-empty, stripped lines."""
    if not path.exists():
        print(f"{RED}  [!] File not found: {path}{RESET}")
        return []
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    print(f"{GREEN}  [+] Loaded {len(lines)} {label} from {path.name}{RESET}")
    return lines


def prompt_int(prompt: str, default: int, lo: int = 1, hi: int = 10_000) -> int:
    """Ask for an integer input with validation."""
    raw = input(f"  {prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        val = int(raw)
        if lo <= val <= hi:
            return val
        print(f"{YELLOW}  Out of range ({lo}–{hi}). Using default {default}.{RESET}")
    except ValueError:
        print(f"{YELLOW}  Invalid input. Using default {default}.{RESET}")
    return default


def prompt_float(prompt: str, default: float) -> float:
    raw = input(f"  {prompt} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"{YELLOW}  Invalid. Using default {default}.{RESET}")
        return default


def print_result(stats, label: str = "Attack") -> None:
    print(f"\n{CYAN}{stats.report()}{RESET}")
    if stats.found_credentials:
        for u, p in stats.found_credentials:
            print(f"\n{GREEN}{BOLD}  ✔  SUCCESS FOUND")
            print(f"     Username : {u}")
            print(f"     Password : {p}")
            print(f"     Attempts : {stats.total_attempts}")
            print(f"     Time     : {stats.elapsed:.2f}s{RESET}")
    else:
        print(f"{YELLOW}  No credentials discovered in this run.{RESET}")


def pause() -> None:
    input(f"\n{BOLD}  Press Enter to return to menu…{RESET}")


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def action_dictionary_attack(login: LoginSystem, cfg: AttackConfig) -> None:
    print(f"\n{CYAN}{BOLD}  ── Dictionary Attack ──────────────────────────{RESET}")
    usernames = load_file(USERNAMES_FILE, "usernames")
    passwords = load_file(PASSWORDS_FILE, "passwords")
    if not usernames or not passwords:
        pause()
        return

    # Optionally narrow target
    target = input(f"\n  Target username (leave blank to try all): ").strip()
    if target:
        usernames = [target]

    stop_first = input("  Stop on first success? [Y/n]: ").strip().lower() != "n"

    print(f"\n{YELLOW}  Starting dictionary attack…{RESET}\n")
    attacker = DictionaryAttacker(login, cfg)
    # For multi-user runs, always find one credential per user.
    # stop_on_first only applies when attacking a single username.
    effective_stop = stop_first and len(usernames) == 1
    stats    = attacker.run(usernames, passwords, stop_on_first=effective_stop)
    print_result(stats, "Dictionary Attack")
    pause()


def action_brute_force(login: LoginSystem, cfg: AttackConfig) -> None:
    print(f"\n{CYAN}{BOLD}  ── Brute Force Attack ─────────────────────────{RESET}")
    target = input("  Target username (required for brute force): ").strip()
    if not target:
        print(f"{RED}  Username is required.{RESET}")
        pause()
        return

    print(f"\n  Charset options:")
    print(f"   1  lowercase letters (a-z)")
    print(f"   2  digits (0-9)")
    print(f"   3  lowercase + digits")
    print(f"   4  custom")
    ch = input("  Choice [3]: ").strip()
    import string
    charsets = {
        "1": string.ascii_lowercase,
        "2": string.digits,
        "3": string.ascii_lowercase + string.digits,
    }
    if ch == "4":
        cfg.charset = input("  Enter custom charset: ").strip() or cfg.charset
    else:
        cfg.charset = charsets.get(ch, string.ascii_lowercase + string.digits)

    cfg.min_password_length = prompt_int("  Min password length", 1, 1, 4)
    cfg.max_password_length = prompt_int("  Max password length", 4, 1, 6)

    print(f"\n{YELLOW}  Starting brute force attack…{RESET}\n")
    attacker = BruteForceAttacker(login, cfg)
    stats    = attacker.run([target])
    print_result(stats, "Brute Force Attack")
    pause()


def action_username_enum(login: LoginSystem, cfg: AttackConfig) -> None:
    print(f"\n{CYAN}{BOLD}  ── Username Enumeration ────────────────────────{RESET}")
    usernames = load_file(USERNAMES_FILE, "usernames")
    if not usernames:
        pause()
        return

    print(f"\n  {YELLOW}How it works:{RESET} Probing each username with a dummy password")
    print(f"  and measuring response-time variance. A well-hardened login")
    print(f"  system returns constant-time responses — but many real apps don't.\n")

    enumerator = UsernameEnumerator(login, cfg)
    stats, timing = enumerator.run(usernames)

    # Sort by response time (descending = potentially slower = might exist)
    sorted_users = sorted(timing.items(), key=lambda x: x[1], reverse=True)
    median_ms    = sorted(timing.values())[len(timing) // 2]

    print(f"\n{CYAN}  ── Response-Time Analysis ─────────────────────{RESET}")
    print(f"  {'Username':<18} {'Avg (ms)':>10}  {'Signal':>10}")
    print(f"  {'─'*18} {'─'*10}  {'─'*10}")
    for u, avg in sorted_users:
        delta = avg - median_ms
        signal = (f"{GREEN}+{delta:+.1f}ms  (slower)  ← possible hit{RESET}"
                  if delta > 5
                  else f"{RESET}  baseline{RESET}")
        print(f"  {u:<18} {avg:>10.2f}  {signal}")

    print(f"\n  {YELLOW}Note:{RESET} This simulator uses randomised response timing,")
    print(f"  so results are intentionally noisy — reflecting a hardened system.")
    print_result(stats, "Username Enumeration")
    pause()


def action_view_logs() -> None:
    print(f"\n{CYAN}{BOLD}  ── Attack Logs ({LOGS_FILE.name}) ─────────────────────{RESET}\n")
    if not LOGS_FILE.exists() or LOGS_FILE.stat().st_size == 0:
        print(f"  {YELLOW}No log entries yet.{RESET}")
    else:
        lines = LOGS_FILE.read_text(encoding="utf-8").splitlines()
        # Show last 40 lines to keep the screen manageable
        visible = lines[-40:] if len(lines) > 40 else lines
        if len(lines) > 40:
            print(f"  {YELLOW}(showing last 40 of {len(lines)} lines){RESET}\n")
        for line in visible:
            if "SUCCESS" in line:
                print(f"  {GREEN}{line}{RESET}")
            elif "LOCKED" in line:
                print(f"  {RED}{line}{RESET}")
            elif line.startswith("#"):
                print(f"  {BLUE}{line}{RESET}")
            else:
                print(f"  {line}")
    pause()


def action_reset_lockouts(login: LoginSystem) -> None:
    confirm = input(f"\n  {YELLOW}Reset ALL account lockouts? [y/N]: {RESET}").strip().lower()
    if confirm == "y":
        login.reset_all_lockouts()
        print(f"  {GREEN}All lockouts cleared.{RESET}")
    else:
        print(f"  Cancelled.")
    pause()


def action_settings(cfg: AttackConfig) -> None:
    print(f"\n{CYAN}{BOLD}  ── Attack Settings ────────────────────────────{RESET}")
    print(f"  (Press Enter to keep current value)\n")
    cfg.delay_between_attempts = prompt_float(
        "Delay between attempts (seconds)", cfg.delay_between_attempts
    )
    cfg.thread_count  = prompt_int("Thread count", cfg.thread_count, 1, 32)
    cfg.max_attempts  = prompt_int("Max total attempts", cfg.max_attempts, 1, 1_000_000)

    print(f"\n{GREEN}  Settings saved:{RESET}")
    print(f"   delay   = {cfg.delay_between_attempts}s")
    print(f"   threads = {cfg.thread_count}")
    print(f"   max     = {cfg.max_attempts:,}")

    print(f"\n  {CYAN}Login System Settings:{RESET}")
    print(f"   lockout after {LoginConfig.MAX_ATTEMPTS_BEFORE_LOCKOUT} failures")
    print(f"   lockout duration {LoginConfig.LOCKOUT_DURATION_SECONDS}s")
    print(f"   CAPTCHA after {LoginConfig.CAPTCHA_THRESHOLD} failures")
    pause()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    login = LoginSystem()     # Single shared login system instance
    cfg   = AttackConfig()    # Default attack configuration

    while True:
        clear()
        print(BANNER)
        print(MENU)

        choice = input(f"\n{BOLD}  Choose option [1-7]: {RESET}").strip()

        if choice == "1":
            action_dictionary_attack(login, cfg)

        elif choice == "2":
            action_brute_force(login, cfg)

        elif choice == "3":
            action_username_enum(login, cfg)

        elif choice == "4":
            action_view_logs()

        elif choice == "5":
            action_reset_lockouts(login)

        elif choice == "6":
            action_settings(cfg)

        elif choice == "7":
            print(f"\n{GREEN}  Exiting. Stay ethical!{RESET}\n")
            sys.exit(0)

        else:
            print(f"{YELLOW}  Invalid choice. Please enter 1–7.{RESET}")
            time.sleep(1)


if __name__ == "__main__":
    main()
