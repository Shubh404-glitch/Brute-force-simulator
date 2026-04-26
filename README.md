# Advanced Brute Force Login Simulator
## Cybersecurity Educational Tool

> **EDUCATIONAL USE ONLY** — This tool simulates both sides of a login
> attack entirely in-process. No real network connections are made.
> It is intended for learning how defenders can harden login systems.

---

## Project Structure

```
bruteforce-simulator/
│
├── app.py           ← Interactive CLI menu (run this)
├── targetlogin.py    ← Defender: login system with protections
├── bruteforce.py     ← Attacker: dictionary / brute-force / enumeration
├── usernames.txt     ← Username wordlist
├── passwords.txt     ← Password dictionary
├── logs.txt          ← Auto-generated attack log
└── requirements.txt
```

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch the simulator

```bash
python main.py
```

---

## Menu Options

| Option | Description |
|--------|-------------|
| 1 | **Dictionary Attack** — tries passwords from `passwords.txt` against usernames |
| 2 | **Brute Force Attack** — generates character combinations up to a set length |
| 3 | **Username Enumeration** — probes timing differences to guess valid accounts |
| 4 | **View Logs** — tails `logs.txt` with colour-coded results |
| 5 | **Reset All Lockouts** — clears account lockout state for re-testing |
| 6 | **Attack Settings** — configure threads, delay, max attempts, charset |
| 7 | **Exit** |

---

## Defender Protections Simulated

| Protection | Details |
|---|---|
| Password hashing | SHA-256 with salt (via `hashlib`) |
| Account lockout | After 5 failures, account locks for 30 seconds |
| CAPTCHA simulation | Triggered after 3 failures; adds realistic delay |
| Rate limiting | Per-IP sliding window (20 req / 10 sec) |
| Username enumeration protection | Generic error messages + constant-time responses |
| Random response timing | Server jitter to frustrate timing analysis |

---

## What Gets Logged (`logs.txt`)

```
timestamp | attempt# | IP | attack_type | username | password | result | elapsed
```

Example:
```
2024-11-01 14:32:01 | #   245 | IP:10.0.0.87 | DICTIONARY          | user:admin          | pass:secure123       | SUCCESS      | 0.1823s
```

---

## Configurable Settings (via menu option 6)

- **Delay between attempts** (seconds) — slows attack to evade rate limiting
- **Thread count** — parallel workers (default: 4)
- **Max attempts** — hard cap on total attempts per run
- **Charset** — characters used in brute-force generation
- **Password length range** — min/max for brute-force combinations

---

## Demo Accounts (seeded in `targetlogin.py`)

All usernames in `usernames.txt` have a password that exists in `passwords.txt`,
so the dictionary attack will always find credentials for every username.

| Username | Password |
|---|---|
| admin | secure123 |
| alice | abc123 |
| bob | password |
| john | 123456 |
| root | toor |
| guest | guest |
| superuser | superman |
| manager | master |
| user | password1 |
| administrator | admin123 |
| test | test |
| webmaster | welcome |
| support | letmein |
| info | hello |
| service | login |
| alpha_user | monkey |
| beta_user | dragon |
| gamma_user | shadow |
| delta_user | sunshine |
| echo_user | princess |
| foxtrot_user | football |
| hotel_user | michael |
| india_user | trustno1 |
| juliet_user | charlie |
| kilo_user | donald |
| lima_user | iloveyou |
| mike_user | password123 |
| november_user | 111111 |
| oscar_user | 123123 |
| papa_user | qwerty |

The dictionary attack (option 1) will find credentials for **all** usernames.

---

## Key Learning Outcomes

1. **Why rate limiting and lockouts matter** — without them, dictionary attacks succeed in seconds
2. **Why generic error messages are important** — distinguishing "wrong user" vs "wrong password" aids enumeration
3. **Why constant-time responses matter** — timing leaks can reveal valid usernames
4. **Why password hashing is essential** — even if the database is stolen, plain-text passwords aren't exposed
5. **How multi-threading accelerates attacks** — and why throttling requests at the server is critical
