"""
bruteforce.py
-------------
Simulates a brute-force / dictionary attacker targeting the LoginSystem.
All attacks run entirely in-process against the local LoginSystem object —
no real network traffic is generated.

Attack modes:
  1. Dictionary Attack   – try passwords from a wordlist
  2. Brute Force Attack  – generate character combinations up to max_length
  3. Username Enumeration – probe which usernames exist (timing-based)

EDUCATIONAL USE ONLY.
"""

import itertools
import logging
import random
import string
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from tqdm import tqdm

from targetlogin import LoginSystem, LoginResult

# ---------------------------------------------------------------------------
# Logging to file
# ---------------------------------------------------------------------------

_file_handler = logging.FileHandler("logs.txt", mode="a", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(message)s"))

attack_logger = logging.getLogger("bruteforce")
attack_logger.setLevel(logging.DEBUG)
attack_logger.addHandler(_file_handler)
attack_logger.propagate = False


def _log_attempt(attempt_no: int,
                 ip: str,
                 attack_type: str,
                 username: str,
                 password: str,
                 result: LoginResult,
                 elapsed: float) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    attack_logger.info(
        f"{ts} | #{attempt_no:>6} | IP:{ip} | {attack_type:<20} | "
        f"user:{username:<15} | pass:{password:<20} | "
        f"{result.status:<12} | {elapsed:.4f}s"
    )


# ---------------------------------------------------------------------------
# Attacker Configuration
# ---------------------------------------------------------------------------

@dataclass
class AttackConfig:
    """All tunable parameters for an attack session."""
    delay_between_attempts: float = 0.0      # Extra sleep between attempts (s)
    thread_count: int            = 4          # Worker threads
    max_attempts: int            = 100_000    # Hard cap on total attempts
    charset: str                 = string.ascii_lowercase + string.digits
    min_password_length: int     = 1
    max_password_length: int     = 5
    simulated_ip_prefix: str     = "10.0.0"  # e.g. 10.0.0.1 – 10.0.0.254


# ---------------------------------------------------------------------------
# Attack Statistics
# ---------------------------------------------------------------------------

@dataclass
class AttackStats:
    """Thread-safe counters updated throughout the attack."""
    total_attempts: int     = 0
    successful_hits: int    = 0
    locked_accounts: int    = 0
    rate_limited: int       = 0
    start_time: float       = field(default_factory=time.time)
    found_credentials: list = field(default_factory=list)   # [(user, pass), ...]
    _lock: threading.Lock   = field(default_factory=threading.Lock, repr=False)

    def increment(self, result_status: str) -> None:
        with self._lock:
            self.total_attempts += 1
            if result_status == LoginResult.SUCCESS:
                self.successful_hits += 1
            elif result_status == LoginResult.LOCKED:
                self.locked_accounts += 1
            elif result_status == LoginResult.RATE_LIMITED:
                self.rate_limited += 1

    def add_found(self, username: str, password: str) -> None:
        with self._lock:
            self.found_credentials.append((username, password))

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def attempts_per_second(self) -> float:
        e = self.elapsed
        return self.total_attempts / e if e > 0 else 0.0

    def report(self) -> str:
        lines = [
            "─" * 55,
            "  ATTACK STATISTICS",
            "─" * 55,
            f"  Total Attempts   : {self.total_attempts}",
            f"  Successful Hits  : {self.successful_hits}",
            f"  Locked Encounters: {self.locked_accounts}",
            f"  Rate-Limited     : {self.rate_limited}",
            f"  Time Elapsed     : {self.elapsed:.2f}s",
            f"  Speed            : {self.attempts_per_second:.1f} attempts/sec",
        ]
        if self.found_credentials:
            lines.append(f"  Credentials Found: {len(self.found_credentials)}")
            for u, p in self.found_credentials:
                lines.append(f"    ✔  {u} / {p}")
        else:
            lines.append("  Credentials Found: none")
        lines.append("─" * 55)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Base Attacker
# ---------------------------------------------------------------------------

class BaseAttacker:
    """
    Shared machinery used by all attack subclasses:
    – sends login attempts via the LoginSystem
    – logs each attempt to logs.txt
    – maintains AttackStats
    – supports early-exit when credentials are found
    """

    def __init__(self,
                 login_system: LoginSystem,
                 config: Optional[AttackConfig] = None) -> None:
        self.login   = login_system
        self.config  = config or AttackConfig()
        self.stats   = AttackStats()
        self._stop   = threading.Event()

    # ------------------------------------------------------------------

    def _random_ip(self) -> str:
        """Return a simulated attacker IP (rotated to bypass per-IP rate limits)."""
        return f"{self.config.simulated_ip_prefix}.{random.randint(1, 254)}"

    def _try_once(self,
                  username: str,
                  password: str,
                  attack_type: str) -> LoginResult:
        """Issue one login attempt and log the outcome."""
        ip = self._random_ip()
        t0 = time.time()
        result = self.login.attempt_login(username, password, ip=ip)
        elapsed = time.time() - t0

        _log_attempt(
            self.stats.total_attempts + 1,
            ip,
            attack_type,
            username,
            password,
            result,
            elapsed,
        )
        self.stats.increment(result.status)

        if result.is_success():
            self.stats.add_found(username, password)
            # Only set global stop if single-user mode (stop_on_first handled
            # at the attacker level for multi-user runs)

        if self.config.delay_between_attempts > 0:
            time.sleep(self.config.delay_between_attempts)

        return result

    def stop(self) -> None:
        self._stop.set()

    @property
    def should_stop(self) -> bool:
        return self._stop.is_set() or (self.stats.total_attempts >= self.config.max_attempts)


# ---------------------------------------------------------------------------
# Dictionary Attack
# ---------------------------------------------------------------------------

class DictionaryAttacker(BaseAttacker):
    """
    Tries every (username, password) pair from supplied wordlists.
    Runs workers in a thread pool for speed; stops immediately on success.
    """

    ATTACK_TYPE = "DICTIONARY"

    def run(self,
            usernames: list[str],
            passwords: list[str],
            stop_on_first: bool = True) -> AttackStats:
        """
        Execute the attack.

        Args:
            usernames:     List of usernames to probe.
            passwords:     Ordered list of passwords to try.
            stop_on_first: If True AND single username, stop on first hit.
                           For multiple usernames, always finds one credential
                           per user (does NOT stop on the very first global hit).
        """
        total_tasks = len(usernames) * len(passwords)
        print(f"\n  Loaded {len(passwords)} passwords, {len(usernames)} usernames")
        print(f"  Total combinations : {total_tasks:,}")
        print(f"  Thread workers     : {self.config.thread_count}\n")

        self.stats = AttackStats()
        self._stop.clear()

        # Track which usernames have already been cracked so we skip further
        # passwords for them (avoids duplicate results while still finding
        # credentials for every user).
        cracked_users: set[str] = set()
        cracked_lock  = threading.Lock()

        single_user = len(usernames) == 1

        def _try_user_pass(username: str, password: str):
            with cracked_lock:
                # Skip if this user already cracked
                if username in cracked_users:
                    return None, username, password
            result = self._try_once(username, password, self.ATTACK_TYPE)
            if result.is_success():
                with cracked_lock:
                    cracked_users.add(username)
                # Stop globally only for single-user stop_on_first mode
                if single_user and stop_on_first:
                    self._stop.set()
            return result, username, password

        with tqdm(total=total_tasks,
                  desc="  Dictionary",
                  unit="attempt",
                  colour="cyan",
                  dynamic_ncols=True) as pbar:

            with ThreadPoolExecutor(max_workers=self.config.thread_count) as pool:
                futures = {}

                for username in usernames:
                    for password in passwords:
                        if self.stats.total_attempts >= self.config.max_attempts:
                            break
                        fut = pool.submit(_try_user_pass, username, password)
                        futures[fut] = (username, password)

                for fut in as_completed(futures):
                    pbar.update(1)
                    result, u, p = fut.result()
                    if result is None:
                        continue   # was skipped (already cracked)
                    pbar.set_postfix({
                        "trying": f"{u}/{p[:8]}",
                        "speed": f"{self.stats.attempts_per_second:.0f}/s",
                        "found": self.stats.successful_hits,
                    })
                    # If every username is cracked, we can stop
                    with cracked_lock:
                        all_done = len(cracked_users) == len(usernames)
                    if all_done:
                        pool.shutdown(wait=False, cancel_futures=True)
                        break

        return self.stats


# ---------------------------------------------------------------------------
# Brute Force Attack (character-combination generation)
# ---------------------------------------------------------------------------

class BruteForceAttacker(BaseAttacker):
    """
    Generates every combination of characters from `config.charset`
    between `config.min_password_length` and `config.max_password_length`
    and attempts each one against the target username(s).
    """

    ATTACK_TYPE = "BRUTE_FORCE"

    def _generate_passwords(self):
        """Yield all passwords for the configured charset and lengths."""
        for length in range(self.config.min_password_length,
                            self.config.max_password_length + 1):
            for combo in itertools.product(self.config.charset, repeat=length):
                yield "".join(combo)

    def _total_combinations(self) -> int:
        total = 0
        base = len(self.config.charset)
        for l in range(self.config.min_password_length,
                       self.config.max_password_length + 1):
            total += base ** l
        return total

    def run(self, usernames: list[str]) -> AttackStats:
        """
        Try all character combinations against each username.

        Args:
            usernames: Accounts to attack.
        """
        total = self._total_combinations() * len(usernames)
        print(f"\n  Charset          : {self.config.charset[:20]}{'...' if len(self.config.charset) > 20 else ''}")
        print(f"  Password lengths : {self.config.min_password_length}–{self.config.max_password_length}")
        print(f"  Total candidates : {total:,}")
        print(f"  Thread workers   : {self.config.thread_count}\n")

        self.stats = AttackStats()
        self._stop.clear()

        with tqdm(total=min(total, self.config.max_attempts),
                  desc="  BruteForce",
                  unit="attempt",
                  colour="red",
                  dynamic_ncols=True) as pbar:

            with ThreadPoolExecutor(max_workers=self.config.thread_count) as pool:
                futures = {}

                for password in self._generate_passwords():
                    if self.should_stop:
                        break
                    for username in usernames:
                        if self.should_stop:
                            break
                        fut = pool.submit(
                            self._try_once, username, password, self.ATTACK_TYPE
                        )
                        futures[fut] = (username, password)

                for fut in as_completed(futures):
                    pbar.update(1)
                    result = fut.result()
                    u, p = futures[fut]
                    pbar.set_postfix({
                        "trying": f"{u}/{p[:8]}",
                        "speed": f"{self.stats.attempts_per_second:.0f}/s",
                        "found": self.stats.successful_hits,
                    })
                    if result.is_success():
                        pool.shutdown(wait=False, cancel_futures=True)
                        self._stop.set()
                        break

        return self.stats


# ---------------------------------------------------------------------------
# Username Enumeration Attack
# ---------------------------------------------------------------------------

class UsernameEnumerator(BaseAttacker):
    """
    Attempts to identify valid usernames by measuring response-time
    differences.  In a well-hardened system this should not work — but
    many real-world systems still leak this information.

    The simulator demonstrates the concept: the LoginSystem here is
    designed to resist enumeration (constant-time responses, generic
    error messages), so results will be ambiguous — which is the lesson.
    """

    ATTACK_TYPE = "USER_ENUM"
    PROBE_PASSWORD = "probe_password_intentionally_wrong_xyz123"
    SAMPLES_PER_USER = 5        # Repeat measurements for statistical accuracy

    def run(self, usernames: list[str]) -> tuple[AttackStats, dict]:
        """
        Probe each username and record average response times.

        Returns:
            (stats, timing_map)  where timing_map is {username: avg_ms}
        """
        print(f"\n  Probing {len(usernames)} usernames × {self.SAMPLES_PER_USER} samples each\n")

        self.stats = AttackStats()
        self._stop.clear()
        timing: dict[str, list[float]] = {u: [] for u in usernames}

        with tqdm(total=len(usernames) * self.SAMPLES_PER_USER,
                  desc="  Enumeration",
                  unit="probe",
                  colour="yellow",
                  dynamic_ncols=True) as pbar:

            for username in usernames:
                for _ in range(self.SAMPLES_PER_USER):
                    t0 = time.perf_counter()
                    result = self._try_once(username, self.PROBE_PASSWORD, self.ATTACK_TYPE)
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    timing[username].append(elapsed_ms)
                    pbar.update(1)
                    pbar.set_postfix({"user": username})

        # Compute averages
        avg_timing = {
            u: sum(v) / len(v) for u, v in timing.items() if v
        }
        return self.stats, avg_timing
