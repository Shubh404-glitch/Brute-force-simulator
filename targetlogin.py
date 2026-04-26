"""
targetlogin.py
--------------
Simulates a secure login system (the "defender" side).
Includes: hashed user database, rate limiting, account lockout,
CAPTCHA simulation, username enumeration protection, and
randomised response timing to frustrate automated attacks.

EDUCATIONAL USE ONLY — this is a local, in-process simulation.
No real network connections are made.
"""

import hashlib
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class LoginConfig:
    """Central configuration for the login system."""
    MAX_ATTEMPTS_BEFORE_LOCKOUT: int = 5        # Failures before account locks
    LOCKOUT_DURATION_SECONDS: int = 30          # How long the lockout lasts
    CAPTCHA_THRESHOLD: int = 3                  # Failures before CAPTCHA required
    MIN_RESPONSE_DELAY: float = 0.05           # Simulated server min latency (s)
    MAX_RESPONSE_DELAY: float = 0.25           # Simulated server max latency (s)
    RATE_LIMIT_WINDOW: int = 10                 # Seconds for rate-limit window
    RATE_LIMIT_MAX_REQUESTS: int = 20           # Max requests per window per IP


# ---------------------------------------------------------------------------
# Password Utilities
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a SHA-256 hex digest of the password (salted simulation)."""
    salt = "edu_sim_salt_2024"          # Fixed salt for reproducibility in demo
    return hashlib.sha256((salt + password).encode()).hexdigest()


# ---------------------------------------------------------------------------
# User Database
# ---------------------------------------------------------------------------

class UserDatabase:
    """
    In-memory user store.  Stores username → hashed_password.
    In a real system this would be a database with per-user salts.
    """

    def __init__(self) -> None:
        self._users: Dict[str, str] = {}
        self._seed_users()

    def _seed_users(self) -> None:
        """Populate demo accounts — every username gets a credential findable
        from passwords.txt so dictionary attacks always succeed."""
        accounts = {
            # Original accounts (passwords present in passwords.txt)
            "admin":            "secure123",
            "alice":            "abc123",
            "bob":              "password",
            "john":             "123456",
            "root":             "toor",
            "guest":            "guest",
            "superuser":        "superman",
            "manager":          "master",
            # Extra accounts matching remaining usernames.txt entries
            "user":             "password1",
            "administrator":    "admin123",
            "test":             "test",
            "webmaster":        "welcome",
            "support":          "letmein",
            "info":             "hello",
            "service":          "login",
            "alpha_user":       "monkey",
            "beta_user":        "dragon",
            "gamma_user":       "shadow",
            "delta_user":       "sunshine",
            "echo_user":        "princess",
            "foxtrot_user":     "football",
            "hotel_user":       "michael",
            "india_user":       "trustno1",
            "juliet_user":      "charlie",
            "kilo_user":        "donald",
            "lima_user":        "iloveyou",
            "mike_user":        "password123",
            "november_user":    "111111",
            "oscar_user":       "123123",
            "papa_user":        "qwerty",
        }
        for username, plaintext in accounts.items():
            self._users[username] = hash_password(plaintext)

    def user_exists(self, username: str) -> bool:
        return username in self._users

    def verify(self, username: str, password: str) -> bool:
        if not self.user_exists(username):
            return False
        return self._users[username] == hash_password(password)

    def add_user(self, username: str, password: str) -> None:
        self._users[username] = hash_password(password)

    def list_usernames(self):
        return list(self._users.keys())


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """
    Sliding-window rate limiter keyed by (simulated) IP address.
    Thread-safe via a lock.
    """

    def __init__(self,
                 window_seconds: int = LoginConfig.RATE_LIMIT_WINDOW,
                 max_requests: int = LoginConfig.RATE_LIMIT_MAX_REQUESTS) -> None:
        self._window = window_seconds
        self._max = max_requests
        self._records: Dict[str, list] = {}   # ip → [timestamp, ...]
        self._lock = threading.Lock()

    def is_allowed(self, ip: str) -> bool:
        """Return True if the IP has not exceeded the rate limit."""
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            timestamps = self._records.get(ip, [])
            # Prune old entries
            timestamps = [t for t in timestamps if t > cutoff]
            if len(timestamps) >= self._max:
                self._records[ip] = timestamps
                return False
            timestamps.append(now)
            self._records[ip] = timestamps
            return True

    def reset(self, ip: str) -> None:
        with self._lock:
            self._records.pop(ip, None)


# ---------------------------------------------------------------------------
# Account Lockout Manager
# ---------------------------------------------------------------------------

class LockoutManager:
    """
    Tracks per-account failed attempts and enforces timed lockouts.
    Thread-safe.
    """

    def __init__(self,
                 max_attempts: int = LoginConfig.MAX_ATTEMPTS_BEFORE_LOCKOUT,
                 lockout_seconds: int = LoginConfig.LOCKOUT_DURATION_SECONDS) -> None:
        self._max = max_attempts
        self._duration = lockout_seconds
        # username → {"count": int, "locked_until": datetime | None}
        self._state: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def record_failure(self, username: str) -> None:
        with self._lock:
            entry = self._state.setdefault(username, {"count": 0, "locked_until": None})
            entry["count"] += 1
            if entry["count"] >= self._max:
                entry["locked_until"] = datetime.now() + timedelta(seconds=self._duration)

    def record_success(self, username: str) -> None:
        with self._lock:
            self._state.pop(username, None)

    def is_locked(self, username: str) -> bool:
        with self._lock:
            entry = self._state.get(username)
            if not entry:
                return False
            if entry["locked_until"] and datetime.now() < entry["locked_until"]:
                return True
            # Lockout expired — reset counter
            if entry["locked_until"] and datetime.now() >= entry["locked_until"]:
                self._state.pop(username, None)
            return False

    def lockout_remaining(self, username: str) -> float:
        """Seconds remaining on lockout (0 if not locked)."""
        with self._lock:
            entry = self._state.get(username)
            if not entry or not entry["locked_until"]:
                return 0.0
            remaining = (entry["locked_until"] - datetime.now()).total_seconds()
            return max(0.0, remaining)

    def failure_count(self, username: str) -> int:
        with self._lock:
            return self._state.get(username, {}).get("count", 0)

    def reset_all(self) -> None:
        with self._lock:
            self._state.clear()

    def reset_account(self, username: str) -> None:
        with self._lock:
            self._state.pop(username, None)


# ---------------------------------------------------------------------------
# CAPTCHA Simulator
# ---------------------------------------------------------------------------

class CaptchaSimulator:
    """
    Simulates CAPTCHA verification.
    In the simulator, CAPTCHA always 'passes' (we return True) but the
    call adds a realistic delay to model the UX friction.
    """

    def __init__(self, threshold: int = LoginConfig.CAPTCHA_THRESHOLD) -> None:
        self._threshold = threshold

    def is_required(self, failure_count: int) -> bool:
        return failure_count >= self._threshold

    def verify(self) -> bool:
        """Simulate the time cost of a CAPTCHA challenge."""
        time.sleep(random.uniform(0.1, 0.3))   # CAPTCHA solve delay
        return True   # Always passes in simulation


# ---------------------------------------------------------------------------
# Login Result
# ---------------------------------------------------------------------------

class LoginResult:
    """Value object returned by LoginSystem.attempt_login()."""

    SUCCESS         = "SUCCESS"
    FAILURE         = "FAILURE"
    LOCKED          = "LOCKED"
    RATE_LIMITED    = "RATE_LIMITED"
    CAPTCHA_NEEDED  = "CAPTCHA_NEEDED"

    def __init__(self,
                 status: str,
                 username: str,
                 message: str,
                 lockout_remaining: float = 0.0) -> None:
        self.status = status
        self.username = username
        self.message = message
        self.lockout_remaining = lockout_remaining
        self.timestamp = datetime.now()

    def is_success(self) -> bool:
        return self.status == self.SUCCESS

    def __repr__(self) -> str:
        return f"LoginResult(status={self.status}, user={self.username})"


# ---------------------------------------------------------------------------
# Login System  (main public API)
# ---------------------------------------------------------------------------

class LoginSystem:
    """
    Facade that wires together the user database, rate limiter,
    lockout manager, and CAPTCHA simulator into a single
    authenticate() call.
    """

    def __init__(self) -> None:
        self.db            = UserDatabase()
        self.rate_limiter  = RateLimiter()
        self.lockout_mgr   = LockoutManager()
        self.captcha       = CaptchaSimulator()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def attempt_login(self,
                      username: str,
                      password: str,
                      ip: str = "127.0.0.1") -> LoginResult:
        """
        Process a login attempt.  Returns a LoginResult describing outcome.
        Applies rate limiting → lockout check → CAPTCHA → credential verify.
        Also adds a randomised response delay to resist timing analysis.
        """
        start = time.time()

        # 1. Rate limiting
        if not self.rate_limiter.is_allowed(ip):
            self._apply_response_delay(start)
            return LoginResult(
                LoginResult.RATE_LIMITED,
                username,
                f"Too many requests from {ip}. Slow down."
            )

        # 2. Account lockout
        if self.lockout_mgr.is_locked(username):
            remaining = self.lockout_mgr.lockout_remaining(username)
            self._apply_response_delay(start)
            return LoginResult(
                LoginResult.LOCKED,
                username,
                f"Account locked. Retry in {remaining:.1f}s.",
                lockout_remaining=remaining
            )

        # 3. CAPTCHA gate (after enough failures)
        failures = self.lockout_mgr.failure_count(username)
        if self.captcha.is_required(failures):
            self.captcha.verify()       # adds delay

        # 4. Credential check — intentionally constant-time style
        #    (hash comparison is done internally by verify())
        user_ok     = self.db.user_exists(username)
        creds_valid = self.db.verify(username, password)

        if creds_valid:
            self.lockout_mgr.record_success(username)
            self._apply_response_delay(start)
            return LoginResult(
                LoginResult.SUCCESS,
                username,
                "Authentication successful."
            )
        else:
            self.lockout_mgr.record_failure(username)
            self._apply_response_delay(start)
            # NOTE: we do NOT distinguish "bad user" vs "bad password"
            # to prevent username enumeration via error messages.
            return LoginResult(
                LoginResult.FAILURE,
                username,
                "Invalid credentials."
            )

    def reset_all_lockouts(self) -> None:
        self.lockout_mgr.reset_all()

    def reset_lockout(self, username: str) -> None:
        self.lockout_mgr.reset_account(username)

    def reset_rate_limit(self, ip: str) -> None:
        self.rate_limiter.reset(ip)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_response_delay(self, start: float) -> None:
        """
        Sleep enough to bring total response time to a random value in
        [MIN_RESPONSE_DELAY, MAX_RESPONSE_DELAY].  Provides timing
        consistency and frustrates high-speed automated attacks.
        """
        target = random.uniform(
            LoginConfig.MIN_RESPONSE_DELAY,
            LoginConfig.MAX_RESPONSE_DELAY
        )
        elapsed = time.time() - start
        remaining = target - elapsed
        if remaining > 0:
            time.sleep(remaining)
