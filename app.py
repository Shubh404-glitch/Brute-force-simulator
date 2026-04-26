"""
app.py
------
Streamlit web interface — Advanced Brute Force Login Simulator.
UI: Framework Security dark-teal aesthetic + rich CSS animations,
    particle background, glowing effects, typing indicators,
    animated metric counters, hover transitions, pulse indicators.

Run with:  streamlit run app.py
EDUCATIONAL USE ONLY — in-process simulation, no real network traffic.
"""

import time
import threading
import string
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Brute Force Simulator",
    page_icon="💀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Brute Force Simulator — Cybersecurity Educational Tool"},
)

from targetlogin import LoginSystem, LoginConfig, LoginResult
from bruteforce  import AttackConfig, DictionaryAttacker, BruteForceAttacker, UsernameEnumerator

BASE_DIR       = Path(__file__).parent
USERNAMES_FILE = BASE_DIR / "usernames.txt"
PASSWORDS_FILE = BASE_DIR / "passwords.txt"
LOGS_FILE      = BASE_DIR / "logs.txt"

# ══════════════════════════════════════════════════════════════════════════
#  MASTER CSS + ANIMATIONS
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@300;400;500;600;700&family=Share+Tech+Mono&family=Barlow:wght@300;400;500;600;700&display=swap');

/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"], .stApp {
    font-family: 'Barlow', sans-serif;
    background-color: #040c0c !important;
    color: #b8cfc8;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 0 !important;
    max-width: 100% !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}

/* ── Scanline overlay ── */
.stApp::after {
    content: '';
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent, transparent 2px,
        rgba(0,255,180,0.018) 2px,
        rgba(0,255,180,0.018) 4px
    );
    pointer-events: none;
    z-index: 99998;
    animation: scanMove 8s linear infinite;
}
@keyframes scanMove {
    0%   { background-position: 0 0; }
    100% { background-position: 0 100px; }
}

/* ── Vignette ── */
.stApp::before {
    content: '';
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%);
    pointer-events: none;
    z-index: 99997;
}

/* ════════════════════════════
   PARTICLE CANVAS BACKGROUND
════════════════════════════ */
#particle-canvas {
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 0;
    pointer-events: none;
    opacity: 0.35;
}

/* ════════════════════════════
   NAVBAR
════════════════════════════ */
.navbar {
    background: rgba(4,12,12,0.96);
    border-bottom: 1px solid #0d2e28;
    padding: 0 40px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky; top: 0; z-index: 1000;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}
.navbar::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, #1aff9c60 30%, #1aff9c 50%, #1aff9c60 70%, transparent 100%);
    animation: borderFlow 3s ease-in-out infinite;
}
@keyframes borderFlow {
    0%, 100% { opacity: 0.4; }
    50%       { opacity: 1; }
}

.nav-logo { display: flex; align-items: center; gap: 14px; }
.nav-logo-icon {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #0a3d35, #0d5c4e);
    border: 1px solid #1aff9c50;
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 14px rgba(26,255,156,0.2), inset 0 0 10px rgba(26,255,156,0.05);
    animation: iconPulse 3s ease-in-out infinite;
}
@keyframes iconPulse {
    0%, 100% { box-shadow: 0 0 14px rgba(26,255,156,0.2), inset 0 0 10px rgba(26,255,156,0.05); }
    50%       { box-shadow: 0 0 28px rgba(26,255,156,0.4), inset 0 0 14px rgba(26,255,156,0.1); }
}
.nav-logo-text {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700; font-size: 19px;
    color: #e8f5f0; letter-spacing: 3px; text-transform: uppercase;
}
.nav-logo-text span { color: #1aff9c; text-shadow: 0 0 12px rgba(26,255,156,0.6); }

.nav-links { display: flex; gap: 32px; align-items: center; }
.nav-link {
    font-size: 12px; color: #5a8e80;
    letter-spacing: 1.5px; text-transform: uppercase; font-weight: 500;
    cursor: pointer;
    transition: color 0.25s, text-shadow 0.25s;
    position: relative;
}
.nav-link::after {
    content: '';
    position: absolute; bottom: -4px; left: 0; right: 0;
    height: 1px; background: #1aff9c;
    transform: scaleX(0); transform-origin: left;
    transition: transform 0.25s;
}
.nav-link:hover { color: #1aff9c; text-shadow: 0 0 8px rgba(26,255,156,0.5); }
.nav-link:hover::after { transform: scaleX(1); }

.nav-btn {
    background: transparent;
    border: 1px solid #1aff9c;
    color: #1aff9c;
    padding: 8px 22px;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600; font-size: 13px;
    letter-spacing: 2px; text-transform: uppercase;
    cursor: pointer;
    transition: all 0.25s;
    position: relative; overflow: hidden;
}
.nav-btn::before {
    content: '';
    position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(26,255,156,0.15), transparent);
    transition: left 0.4s;
}
.nav-btn:hover { background: rgba(26,255,156,0.1); box-shadow: 0 0 18px rgba(26,255,156,0.3); color: #fff; }
.nav-btn:hover::before { left: 100%; }

/* ════════════════════════════
   STATUS BAR (ticker)
════════════════════════════ */
.status-bar {
    background: #020808;
    border-bottom: 1px solid #0a1e1c;
    padding: 6px 40px;
    display: flex; align-items: center; gap: 32px;
    overflow: hidden;
}
.status-item {
    display: flex; align-items: center; gap: 8px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px; color: #2a5e50; letter-spacing: 1px;
    white-space: nowrap;
}
.status-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #1aff9c;
    animation: dotBlink 2s ease-in-out infinite;
}
.status-dot.red { background: #ff3333; animation-delay: 0.4s; }
.status-dot.amber { background: #ffaa44; animation-delay: 0.8s; }
@keyframes dotBlink {
    0%, 100% { opacity: 1; box-shadow: 0 0 4px currentColor; }
    50%       { opacity: 0.3; box-shadow: none; }
}
.status-val { color: #1aff9c; }

/* ════════════════════════════
   HERO
════════════════════════════ */
.hero {
    background: linear-gradient(160deg, #071414 0%, #050f0f 45%, #040c0c 100%);
    border-bottom: 1px solid #0d2e28;
    padding: 80px 48px 72px;
    position: relative; overflow: hidden;
}
.hero-grid-bg {
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        linear-gradient(rgba(26,255,156,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(26,255,156,0.03) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    mask-image: radial-gradient(ellipse at 70% 50%, black 20%, transparent 70%);
}
.hero-glow {
    position: absolute; top: -100px; right: -100px;
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(26,255,156,0.07) 0%, transparent 70%);
    pointer-events: none;
    animation: glowPulse 4s ease-in-out infinite;
}
@keyframes glowPulse {
    0%, 100% { transform: scale(1); opacity: 0.7; }
    50%       { transform: scale(1.15); opacity: 1; }
}

.hero-eyebrow {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px; color: #1aff9c; letter-spacing: 5px; text-transform: uppercase;
    margin-bottom: 22px;
    display: flex; align-items: center; gap: 14px;
    animation: fadeSlideUp 0.6s ease both;
}
.hero-eyebrow::before {
    content: '';
    display: inline-block; width: 36px; height: 1px;
    background: linear-gradient(90deg, transparent, #1aff9c);
}
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}

.hero-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 62px; font-weight: 700;
    line-height: 1.02; color: #e8f5f0;
    margin-bottom: 28px; max-width: 720px;
    animation: fadeSlideUp 0.6s 0.1s ease both;
}
.hero-title span {
    color: #1aff9c;
    text-shadow: 0 0 24px rgba(26,255,156,0.4), 0 0 48px rgba(26,255,156,0.15);
}

.hero-subtitle {
    font-size: 16px; color: #6a9e90;
    max-width: 560px; line-height: 1.75;
    margin-bottom: 40px; font-weight: 300;
    animation: fadeSlideUp 0.6s 0.2s ease both;
}

.hero-warn {
    display: inline-flex; align-items: center; gap: 12px;
    background: rgba(255,107,53,0.07);
    border: 1px solid rgba(255,107,53,0.3);
    border-left: 3px solid #ff6b35;
    padding: 11px 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px; color: #ff9a6b; letter-spacing: 1px;
    animation: fadeSlideUp 0.6s 0.3s ease both;
}
.warn-pulse {
    width: 8px; height: 8px; border-radius: 50%; background: #ff6b35;
    animation: dotBlink 1.2s ease-in-out infinite;
    flex-shrink: 0;
}

.hero-stats {
    display: flex; gap: 56px;
    margin-top: 56px; padding-top: 40px;
    border-top: 1px solid #0d2e28;
    animation: fadeSlideUp 0.6s 0.4s ease both;
}
.hero-stat { position: relative; }
.hero-stat::after {
    content: '';
    position: absolute; right: -28px; top: 8px; bottom: 8px;
    width: 1px; background: #0d2e28;
}
.hero-stat:last-child::after { display: none; }
.hero-stat-value {
    font-family: 'Rajdhani', sans-serif; font-size: 40px; font-weight: 700;
    color: #1aff9c; line-height: 1;
    text-shadow: 0 0 20px rgba(26,255,156,0.35);
}
.hero-stat-label {
    font-size: 11px; color: #4a7f70; letter-spacing: 2px;
    text-transform: uppercase; margin-top: 8px;
}

/* ════════════════════════════
   3-STEP ROW
════════════════════════════ */
.steps-row {
    display: flex; gap: 0;
    border: 1px solid #0d2e28;
    overflow: hidden; margin: 48px 48px 0;
}
.step-card {
    flex: 1; padding: 36px 32px;
    background: #060e0e;
    border-right: 1px solid #0d2e28;
    position: relative; overflow: hidden;
    transition: background 0.3s;
}
.step-card:last-child { border-right: none; }
.step-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #1aff9c, transparent);
    transform: scaleX(0); transform-origin: left;
    transition: transform 0.4s;
}
.step-card:hover { background: #080f0f; }
.step-card:hover::before { transform: scaleX(1); }

.step-num {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px; color: #1aff9c; letter-spacing: 2px; margin-bottom: 16px;
}
.step-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 19px; font-weight: 600; color: #c8e0d8; margin-bottom: 12px;
}
.step-body { font-size: 13px; color: #4a7f70; line-height: 1.65; }
.step-checks { margin-top: 18px; display: flex; flex-direction: column; gap: 8px; }
.step-check {
    font-size: 12px; color: #6a9e90;
    display: flex; align-items: center; gap: 10px;
}
.step-check::before {
    content: '✓'; color: #1aff9c; font-size: 10px; flex-shrink: 0;
    text-shadow: 0 0 6px rgba(26,255,156,0.6);
}

/* ════════════════════════════
   SECTION WRAPPER
════════════════════════════ */
.section { padding: 60px 48px; border-bottom: 1px solid #0a1e1c; }
.section-eyebrow {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px; color: #1aff9c; letter-spacing: 5px;
    text-transform: uppercase; margin-bottom: 14px;
}
.section-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 42px; font-weight: 700; color: #e8f5f0;
    margin-bottom: 18px; line-height: 1.1;
}
.section-body {
    font-size: 14px; color: #5a8e80;
    max-width: 520px; line-height: 1.75; margin-bottom: 36px;
}

/* ════════════════════════════
   ATTACK CARDS
════════════════════════════ */
.attack-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; margin-top: 8px; }
.attack-card {
    background: #060e0e;
    border: 1px solid #0d2e28;
    border-top: 2px solid #1aff9c;
    padding: 30px 26px;
    position: relative; overflow: hidden;
    transition: transform 0.3s, box-shadow 0.3s, background 0.3s;
    cursor: default;
}
.attack-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at 80% 10%, rgba(26,255,156,0.05) 0%, transparent 60%);
    pointer-events: none;
    transition: opacity 0.3s;
}
.attack-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(26,255,156,0.1), 0 0 0 1px rgba(26,255,156,0.15);
    background: #08110f;
}
.attack-card:hover::before { opacity: 2; }
.attack-card-icon {
    width: 48px; height: 48px;
    background: rgba(26,255,156,0.07);
    border: 1px solid rgba(26,255,156,0.2);
    border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; margin-bottom: 20px;
    transition: box-shadow 0.3s;
}
.attack-card:hover .attack-card-icon {
    box-shadow: 0 0 20px rgba(26,255,156,0.25);
}
.attack-card-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 20px; font-weight: 600; color: #c8e0d8; margin-bottom: 10px;
}
.attack-card-body { font-size: 13px; color: #4a7f70; line-height: 1.65; margin-bottom: 20px; }
.attack-card-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px; color: #1aff9c;
    background: rgba(26,255,156,0.06);
    border: 1px solid rgba(26,255,156,0.18);
    padding: 3px 9px; letter-spacing: 1px;
    transition: background 0.2s, box-shadow 0.2s;
}
.tag:hover { background: rgba(26,255,156,0.12); box-shadow: 0 0 8px rgba(26,255,156,0.2); }

/* ════════════════════════════
   PROTECTION CARDS
════════════════════════════ */
.protect-card {
    background: #060e0e;
    border: 1px solid #0d2e28;
    border-left: 3px solid #1aff9c;
    padding: 22px 26px; margin-bottom: 16px;
    transition: transform 0.25s, box-shadow 0.25s, border-color 0.25s;
    position: relative; overflow: hidden;
}
.protect-card::after {
    content: '';
    position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(26,255,156,0.03), transparent);
    transition: left 0.5s;
}
.protect-card:hover { transform: translateX(4px); box-shadow: -4px 0 20px rgba(26,255,156,0.1); border-left-color: #4affb0; }
.protect-card:hover::after { left: 100%; }
.protect-icon { font-size: 22px; margin-bottom: 12px; }
.protect-title { font-family: 'Rajdhani', sans-serif; font-size: 17px; font-weight: 600; color: #c8e0d8; margin-bottom: 7px; }
.protect-body { font-size: 13px; color: #4a7f70; line-height: 1.6; }

/* ════════════════════════════
   ACCOUNT CREDENTIAL CARDS
════════════════════════════ */
.cred-card {
    background: #060e0e;
    border: 1px solid #0d2e28;
    padding: 16px 18px; margin-bottom: 12px;
    font-family: 'Share Tech Mono', monospace;
    transition: border-color 0.25s, box-shadow 0.25s;
    cursor: default;
}
.cred-card:hover { border-color: #1aff9c40; box-shadow: 0 0 16px rgba(26,255,156,0.07); }
.cred-user { font-size: 13px; color: #1aff9c; margin-bottom: 5px; }
.cred-pass { font-size: 11px; color: #2a5e50; }

/* ════════════════════════════
   METRICS ROW
════════════════════════════ */
.metrics-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin: 24px 0; }
.metric-box {
    background: #060e0e;
    border: 1px solid #0d2e28;
    border-bottom: 2px solid rgba(26,255,156,0.25);
    padding: 22px 26px;
    position: relative; overflow: hidden;
    transition: border-color 0.3s, box-shadow 0.3s;
}
.metric-box::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, #1aff9c30, transparent);
}
.metric-box:hover { border-bottom-color: #1aff9c; box-shadow: 0 4px 20px rgba(26,255,156,0.08); }
.metric-box-value {
    font-family: 'Share Tech Mono', monospace;
    font-size: 34px; color: #1aff9c; line-height: 1;
    text-shadow: 0 0 16px rgba(26,255,156,0.3);
}
.metric-box-label { font-size: 10px; color: #4a7f70; letter-spacing: 2px; text-transform: uppercase; margin-top: 10px; }

/* ════════════════════════════
   MINI STAT CARDS (dict/bf page)
════════════════════════════ */
.mini-stat {
    background: #060e0e;
    border: 1px solid #0d2e28;
    border-top: 2px solid #1aff9c;
    padding: 22px 26px; margin-bottom: 20px;
    transition: box-shadow 0.3s;
}
.mini-stat:hover { box-shadow: 0 -2px 16px rgba(26,255,156,0.15); }
.mini-stat-value { font-family: 'Share Tech Mono', monospace; font-size: 30px; color: #1aff9c; }
.mini-stat-label { font-size: 11px; color: #4a7f70; letter-spacing: 2px; text-transform: uppercase; margin-top: 7px; }

/* ════════════════════════════
   COMBO ESTIMATE BAR
════════════════════════════ */
.combo-bar {
    background: #060e0e;
    border: 1px solid #0d2e28;
    padding: 14px 20px; margin: 8px 0 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 12px; color: #4a7f70;
    display: flex; align-items: center; gap: 10px;
}
.combo-bar-val { color: #1aff9c; font-size: 14px; text-shadow: 0 0 8px rgba(26,255,156,0.4); }

/* ════════════════════════════
   RESULT BOXES
════════════════════════════ */
.result-success {
    background: linear-gradient(135deg, #051a0f, #061408);
    border: 1px solid rgba(26,255,156,0.3);
    border-left: 4px solid #1aff9c;
    padding: 22px 26px;
    font-family: 'Share Tech Mono', monospace;
    color: #1aff9c; font-size: 13px; line-height: 2;
    margin: 16px 0;
    box-shadow: 0 0 24px rgba(26,255,156,0.1), inset 0 0 24px rgba(26,255,156,0.03);
    animation: successFlash 0.4s ease;
}
@keyframes successFlash {
    0%   { box-shadow: 0 0 60px rgba(26,255,156,0.5); }
    100% { box-shadow: 0 0 24px rgba(26,255,156,0.1); }
}
.result-fail {
    background: linear-gradient(135deg, #140505, #100404);
    border: 1px solid rgba(255,51,51,0.25);
    border-left: 4px solid #ff3333;
    padding: 22px 26px;
    font-family: 'Share Tech Mono', monospace;
    color: #ff6666; font-size: 13px; line-height: 2;
    margin: 16px 0;
    animation: shake 0.3s ease;
}
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25%       { transform: translateX(-4px); }
    75%       { transform: translateX(4px); }
}
.result-locked {
    background: linear-gradient(135deg, #120a04, #100904);
    border: 1px solid rgba(255,140,0,0.25);
    border-left: 4px solid #ff8c00;
    padding: 22px 26px;
    font-family: 'Share Tech Mono', monospace;
    color: #ffaa44; font-size: 13px; line-height: 2;
    margin: 16px 0;
}

/* ════════════════════════════
   INFO BOX (enumeration)
════════════════════════════ */
.info-box {
    background: #060e0e;
    border: 1px solid #0d2e28;
    border-left: 4px solid #1aff9c;
    padding: 22px 26px; margin-bottom: 24px;
    font-size: 13px; color: #4a7f70; line-height: 1.75;
}

/* ════════════════════════════
   LOG TERMINAL
════════════════════════════ */
.log-terminal {
    background: #020a08;
    border: 1px solid #0d2e28;
    border-top: 2px solid #1aff9c;
    padding: 26px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 12px; max-height: 500px;
    overflow-y: auto; line-height: 1.9;
    position: relative;
}
.log-terminal::before {
    content: '> ATTACK LOG — LIVE FEED';
    display: block;
    font-size: 10px; color: #1aff9c40; letter-spacing: 3px;
    margin-bottom: 16px; padding-bottom: 12px;
    border-bottom: 1px solid #0d2e28;
}
.log-terminal::-webkit-scrollbar { width: 4px; }
.log-terminal::-webkit-scrollbar-track { background: #020a08; }
.log-terminal::-webkit-scrollbar-thumb { background: rgba(26,255,156,0.2); border-radius: 2px; }
.log-success { color: #1aff9c; }
.log-fail    { color: #ff5050; }
.log-locked  { color: #ffaa44; }
.log-comment { color: #1a3e30; }

/* ════════════════════════════
   ACCOUNT STATUS CARDS
════════════════════════════ */
.acct-card {
    background: #060e0e;
    border: 1px solid #0d2e28;
    padding: 16px 18px; margin-bottom: 12px;
    font-family: 'Share Tech Mono', monospace;
    transition: border-color 0.25s;
}
.acct-card.locked { border-top: 2px solid #ff3333; }
.acct-card.active { border-top: 2px solid #1aff9c; }
.acct-name { font-size: 13px; }
.acct-status { font-size: 11px; color: #4a7f70; margin-top: 5px; }

/* ════════════════════════════
   SIDEBAR
════════════════════════════ */
section[data-testid="stSidebar"] {
    background: #030a0a !important;
    border-right: 1px solid #0d2e28 !important;
}
.sidebar-logo {
    padding: 28px 0 22px; text-align: center;
    border-bottom: 1px solid #0d2e28; margin-bottom: 24px;
    position: relative;
}
.sidebar-logo::after {
    content: '';
    position: absolute; bottom: 0; left: 20%; right: 20%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #1aff9c40, transparent);
}
.sidebar-skull {
    font-size: 40px; margin-bottom: 10px;
    filter: drop-shadow(0 0 10px rgba(26,255,156,0.4));
    animation: skullFloat 3s ease-in-out infinite;
}
@keyframes skullFloat {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-4px); }
}
.sidebar-title {
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700; font-size: 17px;
    color: #e8f5f0; letter-spacing: 3px; text-transform: uppercase;
}
.sidebar-title span { color: #1aff9c; text-shadow: 0 0 10px rgba(26,255,156,0.5); }
.sidebar-sub { font-family: 'Share Tech Mono', monospace; font-size: 10px; color: #1a3e30; letter-spacing: 2px; margin-top: 5px; }

.sidebar-section {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10px; color: #1aff9c; letter-spacing: 3px;
    text-transform: uppercase;
    padding-bottom: 8px; border-bottom: 1px solid #0d2e28;
    margin-bottom: 16px; margin-top: 26px;
    display: flex; align-items: center; gap: 8px;
}
.sidebar-section::before { content: '//'; color: #0d3828; }

.sys-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 9px 0; border-bottom: 1px solid #080f0f;
    font-family: 'Share Tech Mono', monospace;
}
.sys-key { font-size: 10px; color: #3a6e5e; letter-spacing: 1px; }
.sys-val { font-size: 11px; color: #1aff9c; }

/* ════════════════════════════
   STREAMLIT WIDGET OVERRIDES
════════════════════════════ */
div[data-testid="stSelectbox"] > label,
div[data-testid="stSlider"] > label,
div[data-testid="stTextInput"] > label,
div[data-testid="stNumberInput"] > label,
div[data-testid="stCheckbox"] > label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 10px !important; color: #3a6e5e !important;
    letter-spacing: 2px !important; text-transform: uppercase !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: #060e0e !important;
    border: 1px solid #0d2e28 !important;
    border-radius: 2px !important;
    color: #c8e0d8 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 13px !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus {
    border-color: #1aff9c80 !important;
    box-shadow: 0 0 0 1px rgba(26,255,156,0.15), 0 0 12px rgba(26,255,156,0.1) !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: #060e0e !important;
    border: 1px solid #0d2e28 !important;
    color: #c8e0d8 !important;
}
.stButton > button {
    background: transparent !important;
    border: 1px solid #1aff9c !important;
    color: #1aff9c !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important; font-size: 14px !important;
    letter-spacing: 3px !important; text-transform: uppercase !important;
    padding: 11px 24px !important; border-radius: 2px !important;
    width: 100% !important;
    transition: all 0.25s !important;
    position: relative !important; overflow: hidden !important;
}
.stButton > button:hover {
    background: rgba(26,255,156,0.08) !important;
    box-shadow: 0 0 24px rgba(26,255,156,0.2), inset 0 0 20px rgba(26,255,156,0.04) !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #0a3d35, #0d5c4e) !important;
    border: 1px solid #1aff9c50 !important;
    color: #1aff9c !important;
}
div[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #0d5c4e, #0f7060) !important;
    box-shadow: 0 0 20px rgba(26,255,156,0.25) !important;
}
div[data-testid="metric-container"] {
    background: #060e0e !important;
    border: 1px solid #0d2e28 !important;
    padding: 16px !important;
    transition: box-shadow 0.25s !important;
}
div[data-testid="metric-container"]:hover {
    box-shadow: 0 0 16px rgba(26,255,156,0.06) !important;
}
div[data-testid="metric-container"] label { color: #3a6e5e !important; font-family: 'Share Tech Mono', monospace !important; font-size: 10px !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-family: 'Share Tech Mono', monospace !important;
    color: #1aff9c !important;
    text-shadow: 0 0 10px rgba(26,255,156,0.3) !important;
}
div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #0d5c4e, #1aff9c, #4affb0) !important;
    box-shadow: 0 0 8px rgba(26,255,156,0.4) !important;
    animation: progressGlow 1.5s ease-in-out infinite alternate !important;
}
@keyframes progressGlow {
    from { box-shadow: 0 0 6px rgba(26,255,156,0.3); }
    to   { box-shadow: 0 0 14px rgba(26,255,156,0.6); }
}
hr { border-color: #0d2e28 !important; }
.stCaption { color: #1a3e30 !important; font-family: 'Share Tech Mono', monospace !important; font-size: 10px !important; letter-spacing: 1px !important; }
div[data-testid="stAlert"] { background: #060e0e !important; border: 1px solid #0d2e28 !important; color: #5a8e80 !important; }

/* ════════════════════════════
   FOOTER
════════════════════════════ */
.site-footer {
    background: #030a0a;
    border-top: 1px solid #0d2e28;
    padding: 40px 48px;
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 24px;
    margin-top: 40px;
    position: relative;
}
.site-footer::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, #1aff9c30, transparent);
}
.footer-brand { font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 16px; color: #e8f5f0; letter-spacing: 2px; text-transform: uppercase; }
.footer-brand span { color: #1aff9c; }
.footer-sub { font-family: 'Share Tech Mono', monospace; font-size: 10px; color: #1a3e30; margin-top: 5px; letter-spacing: 1px; }
.footer-links { display: flex; gap: 32px; }
.footer-link { font-size: 11px; color: #1a3e30; font-family: 'Share Tech Mono', monospace; transition: color 0.2s; }
.footer-link:hover { color: #1aff9c; }
.footer-copy { font-family: 'Share Tech Mono', monospace; font-size: 10px; color: #1a3e30; }
</style>
""", unsafe_allow_html=True)

# ── Particle canvas JS ──────────────────────────────────────────────────
st.markdown("""
<canvas id="particle-canvas"></canvas>
<script>
(function(){
    var canvas = document.getElementById('particle-canvas');
    if(!canvas) return;
    var ctx = canvas.getContext('2d');
    var W, H, particles = [], lines = [];
    function resize(){ W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
    resize(); window.addEventListener('resize', resize);
    for(var i=0;i<70;i++){
        particles.push({
            x: Math.random()*2000, y: Math.random()*2000,
            vx:(Math.random()-0.5)*0.3, vy:(Math.random()-0.5)*0.3,
            r: Math.random()*1.5+0.5, a: Math.random()
        });
    }
    function draw(){
        ctx.clearRect(0,0,W,H);
        particles.forEach(function(p){
            p.x+=p.vx; p.y+=p.vy;
            if(p.x<0||p.x>W) p.vx*=-1;
            if(p.y<0||p.y>H) p.vy*=-1;
            ctx.beginPath();
            ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
            ctx.fillStyle='rgba(26,255,156,'+p.a*0.6+')';
            ctx.fill();
        });
        for(var i=0;i<particles.length;i++){
            for(var j=i+1;j<particles.length;j++){
                var dx=particles[i].x-particles[j].x;
                var dy=particles[i].y-particles[j].y;
                var d=Math.sqrt(dx*dx+dy*dy);
                if(d<140){
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x,particles[i].y);
                    ctx.lineTo(particles[j].x,particles[j].y);
                    ctx.strokeStyle='rgba(26,255,156,'+(1-d/140)*0.08+')';
                    ctx.lineWidth=0.5;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    draw();
})();
</script>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════
if "login_system" not in st.session_state:
    st.session_state.login_system = LoginSystem()

# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════
def load_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [l.strip() for l in path.read_text().splitlines()
            if l.strip() and not l.startswith("#")]

def read_logs(n: int = 80) -> list[str]:
    if not LOGS_FILE.exists():
        return []
    return LOGS_FILE.read_text(encoding="utf-8").splitlines()[-n:]

def render_metrics(attempts, found, speed, elapsed):
    st.markdown(f"""
    <div class="metrics-row">
        <div class="metric-box">
            <div class="metric-box-value">{attempts:,}</div>
            <div class="metric-box-label">Total Attempts</div>
        </div>
        <div class="metric-box">
            <div class="metric-box-value" style="color:#1aff9c">{found}</div>
            <div class="metric-box-label">Credentials Found</div>
        </div>
        <div class="metric-box">
            <div class="metric-box-value" style="color:#ffaa44;text-shadow:0 0 16px rgba(255,170,68,0.3)">{speed:.1f}</div>
            <div class="metric-box-label">Attempts / sec</div>
        </div>
        <div class="metric-box">
            <div class="metric-box-value" style="color:#c8e0d8;text-shadow:none">{elapsed:.1f}s</div>
            <div class="metric-box-label">Time Elapsed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# NAVBAR
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="navbar">
    <div class="nav-logo">
        <div class="nav-logo-icon">💀</div>
        <div class="nav-logo-text">BRUTE<span>FORCE</span> SIMULATOR</div>
    </div>
    <div class="nav-links">
        <span class="nav-link">Dictionary</span>
        <span class="nav-link">Brute Force</span>
        <span class="nav-link">Enumeration</span>
        <span class="nav-link">Logs</span>
        <span class="nav-btn">GET STARTED</span>
    </div>
</div>
""", unsafe_allow_html=True)

# STATUS BAR
st.markdown(f"""
<div class="status-bar">
    <div class="status-item"><div class="status-dot"></div><span>SYSTEM <span class="status-val">ONLINE</span></span></div>
    <div class="status-item"><div class="status-dot amber"></div><span>ACCOUNTS <span class="status-val">{len(st.session_state.login_system.db.list_usernames())}</span></span></div>
    <div class="status-item"><div class="status-dot"></div><span>LOCKOUT <span class="status-val">{LoginConfig.MAX_ATTEMPTS_BEFORE_LOCKOUT} ATTEMPTS</span></span></div>
    <div class="status-item"><div class="status-dot red"></div><span>CAPTCHA <span class="status-val">ACTIVE</span></span></div>
    <div class="status-item"><div class="status-dot"></div><span>RATE LIMITING <span class="status-val">ENABLED</span></span></div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-skull">💀</div>
        <div class="sidebar-title">BRUTE<span>FORCE</span></div>
        <div class="sidebar-sub">SIMULATOR v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Attack Mode</div>', unsafe_allow_html=True)
    page = st.selectbox("Mode", [
        "🏠  Overview",
        "🗂  Dictionary Attack",
        "💥  Brute Force Attack",
        "🕵️  Username Enumeration",
        "📋  View Logs",
        "🔓  Reset Lockouts",
        "🔑  Manual Login Test",
    ], label_visibility="collapsed")

    st.markdown('<div class="sidebar-section">Parameters</div>', unsafe_allow_html=True)
    thread_count = st.slider("Thread Count", 1, 16, 4)
    delay        = st.slider("Delay Between Attempts (s)", 0.0, 1.0, 0.0, 0.05)
    max_attempts = st.number_input("Max Attempts", 100, 100000, 1000, step=500)

    st.markdown('<div class="sidebar-section">System Status</div>', unsafe_allow_html=True)
    ls = st.session_state.login_system
    users = ls.db.list_usernames()
    st.markdown(f"""
    <div class="sys-row"><span class="sys-key">ACCOUNTS</span><span class="sys-val">{len(users)}</span></div>
    <div class="sys-row"><span class="sys-key">LOCKOUT AT</span><span class="sys-val">{LoginConfig.MAX_ATTEMPTS_BEFORE_LOCKOUT} FAILS</span></div>
    <div class="sys-row"><span class="sys-key">LOCKOUT DUR</span><span class="sys-val">{LoginConfig.LOCKOUT_DURATION_SECONDS}S</span></div>
    <div class="sys-row"><span class="sys-key">CAPTCHA AT</span><span class="sys-val">{LoginConfig.CAPTCHA_THRESHOLD} FAILS</span></div>
    <div class="sys-row"><span class="sys-key">RATE LIMIT</span><span class="sys-val">20 / 10S</span></div>
    """, unsafe_allow_html=True)

# ── Shared objects ──────────────────────────────────────────────────────────
login = st.session_state.login_system
cfg   = AttackConfig(delay_between_attempts=delay, thread_count=thread_count, max_attempts=int(max_attempts))

# ══════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
if "Overview" in page:
    st.markdown("""
    <div class="hero">
        <div class="hero-grid-bg"></div>
        <div class="hero-glow"></div>
        <div class="hero-eyebrow">Cybersecurity Educational Tool</div>
        <h1 class="hero-title">Simulate<br><span>Login Attacks</span><br>In Real Time</h1>
        <p class="hero-subtitle">
            A full brute-force attack simulator with both attacker and defender sides.
            Learn how rate limiting, lockouts, and hashing protect against automated credential attacks.
        </p>
        <div class="hero-warn">
            <div class="warn-pulse"></div>
            EDUCATIONAL USE ONLY — all simulation runs in-process, no real network traffic generated
        </div>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-value">6</div>
                <div class="hero-stat-label">Attack Modes</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value">8</div>
                <div class="hero-stat-label">Protected Accounts</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value">5</div>
                <div class="hero-stat-label">Defender Layers</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-value">∞</div>
                <div class="hero-stat-label">Combinations</div>
            </div>
        </div>
    </div>

    <div class="steps-row">
        <div class="step-card">
            <div class="step-num">01 — SELECT ATTACK</div>
            <div class="step-title">Choose Your Attack Vector</div>
            <div class="step-body">Pick from dictionary, brute force, or username enumeration to probe the simulated login system.</div>
            <div class="step-checks">
                <div class="step-check">Dictionary Attack</div>
                <div class="step-check">Brute Force Combinations</div>
                <div class="step-check">Username Enumeration</div>
            </div>
        </div>
        <div class="step-card">
            <div class="step-num">02 — CONFIGURE &amp; LAUNCH</div>
            <div class="step-title">Set Parameters &amp; Run</div>
            <div class="step-body">Tune threads, delay, charset, and max attempts. Watch the progress bar and live metrics as the attack runs.</div>
            <div class="step-checks">
                <div class="step-check">Multi-threaded execution</div>
                <div class="step-check">Real-time progress bar</div>
                <div class="step-check">Live attempts/sec counter</div>
            </div>
        </div>
        <div class="step-card">
            <div class="step-num">03 — ANALYSE RESULTS</div>
            <div class="step-title">Study Defender Responses</div>
            <div class="step-body">Observe how rate limiting, lockouts, CAPTCHA, and hashing respond to attacks. Review the full log.</div>
            <div class="step-checks">
                <div class="step-check">View credentials found</div>
                <div class="step-check">See lockout triggers</div>
                <div class="step-check">Analyse timing data</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section">
        <div class="section-eyebrow">Attack Modes</div>
        <div class="section-title">Comprehensive Attack Simulation</div>
        <div class="section-body">Every attack mode is implemented with real threading, progress tracking, and full logging — mirroring how actual automated attacks operate.</div>
        <div class="attack-grid">
            <div class="attack-card">
                <div class="attack-card-icon">📖</div>
                <div class="attack-card-title">Dictionary Attack</div>
                <div class="attack-card-body">Tries every password from a wordlist against target usernames. The most common real-world attack vector.</div>
                <div class="attack-card-tags"><span class="tag">THREADED</span><span class="tag">WORDLIST</span><span class="tag">FAST</span></div>
            </div>
            <div class="attack-card">
                <div class="attack-card-icon">💥</div>
                <div class="attack-card-title">Brute Force</div>
                <div class="attack-card-body">Generates every possible character combination up to a maximum length. Exhaustive but guaranteed.</div>
                <div class="attack-card-tags"><span class="tag">COMBINATORIAL</span><span class="tag">CHARSET</span><span class="tag">EXHAUSTIVE</span></div>
            </div>
            <div class="attack-card">
                <div class="attack-card-icon">🕵️</div>
                <div class="attack-card-title">User Enumeration</div>
                <div class="attack-card-body">Measures response-time variance per username to identify valid accounts through timing side-channels.</div>
                <div class="attack-card-tags"><span class="tag">TIMING</span><span class="tag">SIDE-CHANNEL</span><span class="tag">RECON</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section">
        <div class="section-eyebrow">Reasons to Study This</div>
        <div class="section-title">Experienced &amp;<br>Hardened Defender</div>
        <div class="section-body">The target login system implements five layers of protection. Each one is visible in action as attacks run.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    protections = [
        ("🔒", "Account Lockout", f"Locks after {LoginConfig.MAX_ATTEMPTS_BEFORE_LOCKOUT} failed attempts for {LoginConfig.LOCKOUT_DURATION_SECONDS}s"),
        ("⏱", "Rate Limiting", "Sliding-window per-IP throttling blocks flooding"),
        ("🤖", "CAPTCHA Simulation", f"Triggered after {LoginConfig.CAPTCHA_THRESHOLD} failures — adds realistic friction"),
        ("#️⃣", "Password Hashing", "SHA-256 with salt — plain-text never stored"),
        ("⏰", "Random Timing", "Jittered responses resist timing-based analysis"),
        ("🛡", "Generic Errors", "No 'bad user' vs 'bad pass' — prevents enumeration"),
    ]
    for i, (icon, title, body) in enumerate(protections):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div class="protect-card">
                <div class="protect-icon">{icon}</div>
                <div class="protect-title">{title}</div>
                <div class="protect-body">{body}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="section">
        <div class="section-eyebrow">Demo Credentials</div>
        <div class="section-title">Seeded Accounts</div>
        <div class="section-body">These accounts are pre-loaded. The dictionary attack will find several automatically.</div>
    </div>
    """, unsafe_allow_html=True)
    accounts = [("admin","secure123"),("alice","Alicepass!2"),("bob","b0bR0cks!"),("john","john1234"),
                ("root","toor"),("guest","guest"),("superuser","Sup3r@User"),("manager","Manage2024!")]
    cols = st.columns(4)
    for i, (u, p) in enumerate(accounts):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="cred-card">
                <div class="cred-user">{u}</div>
                <div class="cred-pass">{p}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: DICTIONARY ATTACK
# ══════════════════════════════════════════════════════════════════════════
elif "Dictionary" in page:
    st.markdown("""
    <div class="hero" style="padding:56px 48px 48px">
        <div class="hero-grid-bg"></div>
        <div class="hero-glow"></div>
        <div class="hero-eyebrow">Attack Mode 01</div>
        <h1 class="hero-title" style="font-size:44px">Dictionary <span>Attack</span></h1>
        <p class="hero-subtitle" style="margin-bottom:0">
            Tries passwords from a wordlist against target usernames.
            Multi-threaded, stops on first success.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    usernames_all = load_file(USERNAMES_FILE)
    passwords_all = load_file(PASSWORDS_FILE)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="mini-stat">
            <div class="mini-stat-value">{len(passwords_all)}</div>
            <div class="mini-stat-label">Passwords Loaded</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="mini-stat">
            <div class="mini-stat-value">{len(usernames_all)}</div>
            <div class="mini-stat-label">Usernames Loaded</div>
        </div>
        """, unsafe_allow_html=True)

    target_user = st.text_input("Target Username (blank = try all usernames)", placeholder="e.g. admin")
    stop_first  = st.checkbox("Stop on first success", value=True)

    if st.button("▶  LAUNCH DICTIONARY ATTACK"):
        usernames = [target_user.strip()] if target_user.strip() else usernames_all
        passwords = passwords_all
        if not usernames or not passwords:
            st.error("Wordlists missing. Check usernames.txt and passwords.txt.")
        else:
            total        = len(usernames) * len(passwords)
            progress_bar = st.progress(0, text="Initialising attack…")
            metrics_area = st.empty()
            results_area = st.empty()
            attacker     = DictionaryAttacker(login, cfg)
            done         = [0]

            def _dict_run():
                from bruteforce import AttackStats
                attacker.stats = AttackStats(); attacker._stop.clear()
                cracked = set()
                single_user = len(usernames) == 1
                for u in usernames:
                    if u in cracked:
                        continue
                    for p in passwords:
                        # If single-user and stop_first, honour global stop
                        if single_user and attacker._stop.is_set():
                            break
                        while True:
                            result = attacker._try_once(u, p, "DICTIONARY")
                            if result.status == "LOCKED":
                                wait = login.lockout_mgr.lockout_remaining(u)
                                time.sleep(max(wait, 0.5) + 0.2)
                                continue
                            done[0] += 1
                            break
                        if result.is_success():
                            cracked.add(u)
                            if single_user and stop_first:
                                attacker._stop.set()
                            break   # Move to next username

            t = threading.Thread(target=_dict_run, daemon=True); t.start()
            while t.is_alive():
                pct = min(done[0] / total, 1.0) if total else 0
                progress_bar.progress(pct, text=f"Attempting {done[0]:,} / {total:,}")
                with metrics_area.container():
                    render_metrics(attacker.stats.total_attempts, attacker.stats.successful_hits,
                                   attacker.stats.attempts_per_second, attacker.stats.elapsed)
                time.sleep(0.3)
            t.join()
            progress_bar.progress(1.0, text="Attack complete")
            s = attacker.stats
            render_metrics(s.total_attempts, s.successful_hits, s.attempts_per_second, s.elapsed)
            if s.found_credentials:
                for u, p in s.found_credentials:
                    results_area.markdown(
                        f'<div class="result-success">'
                        f'✔ &nbsp;CREDENTIALS FOUND<br>'
                        f'USERNAME &nbsp;→ &nbsp;<b>{u}</b><br>'
                        f'PASSWORD &nbsp;→ &nbsp;<b>{p}</b><br>'
                        f'ATTEMPTS &nbsp;→ &nbsp;{s.total_attempts:,} &nbsp;|&nbsp; TIME → {s.elapsed:.2f}s'
                        f'</div>',
                        unsafe_allow_html=True)
            else:
                results_area.markdown(
                    '<div class="result-fail">✘ &nbsp;No credentials discovered in this run.</div>',
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: BRUTE FORCE ATTACK
# ══════════════════════════════════════════════════════════════════════════
elif "Brute Force" in page:
    st.markdown("""
    <div class="hero" style="padding:56px 48px 48px">
        <div class="hero-grid-bg"></div>
        <div class="hero-glow"></div>
        <div class="hero-eyebrow">Attack Mode 02</div>
        <h1 class="hero-title" style="font-size:44px">Brute Force <span>Attack</span></h1>
        <p class="hero-subtitle" style="margin-bottom:0">
            Generates every possible character combination. Exhaustive
            and guaranteed to crack any password within the search space.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    target_user = st.text_input("Target Username (required)", placeholder="e.g. root")

    col1, col2 = st.columns(2)
    with col1:
        charset_opt = st.selectbox("Character Set", ["Lowercase (a-z)", "Digits (0-9)", "Lowercase + Digits", "Custom"])
    charsets_map = {
        "Lowercase (a-z)":    string.ascii_lowercase,
        "Digits (0-9)":       string.digits,
        "Lowercase + Digits": string.ascii_lowercase + string.digits,
    }
    charset = charsets_map.get(charset_opt, string.ascii_lowercase + string.digits)
    with col2:
        if charset_opt == "Custom":
            charset = st.text_input("Custom Charset", value="abcdef0123456789")
        else:
            st.text_input("Active Charset", value=charset[:40] + ("…" if len(charset) > 40 else ""), disabled=True)

    col3, col4 = st.columns(2)
    with col3: min_len = st.number_input("Min Password Length", 1, 4, 1)
    with col4: max_len = st.number_input("Max Password Length", 1, 6, 4)

    cfg.charset             = charset
    cfg.min_password_length = int(min_len)
    cfg.max_password_length = int(max_len)
    total_est = sum(len(charset) ** l for l in range(int(min_len), int(max_len) + 1))

    st.markdown(f"""
    <div class="combo-bar">
        <span>ESTIMATED COMBINATIONS:</span>
        <span class="combo-bar-val">{total_est:,}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("▶  LAUNCH BRUTE FORCE"):
        if not target_user.strip():
            st.error("Enter a target username.")
        else:
            progress_bar = st.progress(0, text="Generating combinations…")
            metrics_area = st.empty()
            results_area = st.empty()
            attacker     = BruteForceAttacker(login, cfg)
            done         = [0]

            def _bf_run():
                import itertools
                from bruteforce import AttackStats
                attacker.stats = AttackStats(); attacker._stop.clear()
                def gen():
                    for ln in range(cfg.min_password_length, cfg.max_password_length + 1):
                        for c in itertools.product(cfg.charset, repeat=ln):
                            yield "".join(c)
                for pwd in gen():
                    if attacker.should_stop:
                        break
                    while True:
                        result = attacker._try_once(target_user.strip(), pwd, "BRUTE_FORCE")
                        if result.status == "LOCKED":
                            wait = login.lockout_mgr.lockout_remaining(target_user.strip())
                            time.sleep(max(wait, 0.5) + 0.2)
                            continue
                        done[0] += 1
                        break
                    if result.is_success():
                        attacker._stop.set()
                        break

            t = threading.Thread(target=_bf_run, daemon=True); t.start()
            while t.is_alive():
                pct = min(done[0] / total_est, 1.0) if total_est else 0
                progress_bar.progress(pct, text=f"Trying {done[0]:,} / {total_est:,}")
                with metrics_area.container():
                    render_metrics(attacker.stats.total_attempts, attacker.stats.successful_hits,
                                   attacker.stats.attempts_per_second, attacker.stats.elapsed)
                time.sleep(0.3)
            t.join()
            progress_bar.progress(1.0, text="Complete")
            s = attacker.stats
            render_metrics(s.total_attempts, s.successful_hits, s.attempts_per_second, s.elapsed)
            if s.found_credentials:
                for u, p in s.found_credentials:
                    results_area.markdown(
                        f'<div class="result-success">'
                        f'✔ &nbsp;PASSWORD CRACKED<br>'
                        f'USERNAME &nbsp;→ &nbsp;<b>{u}</b><br>'
                        f'PASSWORD &nbsp;→ &nbsp;<b>{p}</b><br>'
                        f'ATTEMPTS &nbsp;→ &nbsp;{s.total_attempts:,} &nbsp;|&nbsp; TIME → {s.elapsed:.2f}s'
                        f'</div>',
                        unsafe_allow_html=True)
            else:
                results_area.markdown(
                    '<div class="result-fail">✘ &nbsp;Password not found within this search space.</div>',
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: USERNAME ENUMERATION
# ══════════════════════════════════════════════════════════════════════════
elif "Enumeration" in page:
    st.markdown("""
    <div class="hero" style="padding:56px 48px 48px">
        <div class="hero-grid-bg"></div>
        <div class="hero-glow"></div>
        <div class="hero-eyebrow">Attack Mode 03</div>
        <h1 class="hero-title" style="font-size:44px">Username <span>Enumeration</span></h1>
        <p class="hero-subtitle" style="margin-bottom:0">
            Measures response-time differences per username to identify
            valid accounts via timing side-channels.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <b style="color:#c8e0d8">How it works:</b> Each username is probed with a deliberately wrong password.
        Response times are measured across multiple samples. In a poorly-hardened system, valid usernames
        respond slightly slower. This simulator uses randomised jitter to
        <b style="color:#1aff9c">resist</b> this attack — demonstrating best practice.
    </div>
    """, unsafe_allow_html=True)

    usernames = load_file(USERNAMES_FILE)
    st.caption(f"Probing {len(usernames)} usernames × 5 samples each")

    if st.button("▶  START ENUMERATION PROBE"):
        enumerator = UsernameEnumerator(login, cfg)
        enumerator.config.delay_between_attempts = 0
        total_probes = len(usernames) * enumerator.SAMPLES_PER_USER
        progress_bar = st.progress(0, text="Probing…")
        result_ref   = [None]

        def _enum_run():
            _, timing = enumerator.run(usernames); result_ref[0] = timing

        t = threading.Thread(target=_enum_run, daemon=True); t.start()
        while t.is_alive():
            pct = min(enumerator.stats.total_attempts / total_probes, 1.0)
            progress_bar.progress(pct, text=f"Probing {enumerator.stats.total_attempts} / {total_probes}")
            time.sleep(0.3)
        t.join()
        progress_bar.progress(1.0, text="Analysis complete")

        timing = result_ref[0]
        if timing:
            import pandas as pd
            median = sorted(timing.values())[len(timing) // 2]
            rows   = sorted(timing.items(), key=lambda x: x[1], reverse=True)
            df = pd.DataFrame([{
                "Username":   u,
                "Avg (ms)":   f"{v:.2f}",
                "Delta (ms)": f"{v - median:+.2f}",
                "Signal":     "⚠ Slower — possible hit" if v - median > 5 else "✓ Baseline",
            } for u, v in rows])
            st.markdown("### Response Time Analysis")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption("In a hardened system (like this one), no signal should be > 5ms above baseline.")


# ══════════════════════════════════════════════════════════════════════════
# PAGE: VIEW LOGS
# ══════════════════════════════════════════════════════════════════════════
elif "Logs" in page:
    st.markdown("""
    <div class="hero" style="padding:56px 48px 48px">
        <div class="hero-grid-bg"></div>
        <div class="hero-glow"></div>
        <div class="hero-eyebrow">Forensics</div>
        <h1 class="hero-title" style="font-size:44px">Attack <span>Log</span></h1>
        <p class="hero-subtitle" style="margin-bottom:0">Full timestamped record of every attempt, result, IP, and timing.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("🔄  REFRESH LOG"): st.rerun()

    lines = read_logs(80)
    if not lines:
        st.markdown('<div class="result-locked">No log entries yet. Run an attack first.</div>', unsafe_allow_html=True)
    else:
        html = []
        for line in lines:
            e = line.replace("<", "&lt;").replace(">", "&gt;")
            if "SUCCESS" in line:       html.append(f'<div class="log-success">{e}</div>')
            elif "LOCKED"  in line:     html.append(f'<div class="log-locked">{e}</div>')
            elif line.startswith("#"):  html.append(f'<div class="log-comment">{e}</div>')
            else:                       html.append(f'<div class="log-fail">{e}</div>')
        st.markdown(f'<div class="log-terminal">{"".join(html)}</div>', unsafe_allow_html=True)
        st.caption(f"Showing last {len(lines)} entries from logs.txt")
        success_n = sum(1 for l in lines if "SUCCESS" in l)
        locked_n  = sum(1 for l in lines if "LOCKED"  in l)
        total_n   = sum(1 for l in lines if l.strip() and not l.startswith("#"))
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Logged", total_n)
        c2.metric("Successes",    success_n)
        c3.metric("Lockouts Hit", locked_n)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: RESET LOCKOUTS
# ══════════════════════════════════════════════════════════════════════════
elif "Reset" in page:
    st.markdown("""
    <div class="hero" style="padding:56px 48px 48px">
        <div class="hero-grid-bg"></div>
        <div class="hero-glow"></div>
        <div class="hero-eyebrow">Admin Panel</div>
        <h1 class="hero-title" style="font-size:44px">Reset <span>Lockouts</span></h1>
        <p class="hero-subtitle" style="margin-bottom:0">Clear in-memory lockout state to re-run attacks from a clean slate.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔓  RESET ALL LOCKOUTS"):
            login.reset_all_lockouts(); st.success("All account lockouts cleared.")
    with col2:
        specific = st.text_input("Reset a specific account")
        if st.button("Reset This Account") and specific:
            login.reset_lockout(specific); st.success(f"Lockout cleared for **{specific}**.")

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Share Tech Mono\',monospace;font-size:10px;color:#1aff9c;letter-spacing:3px;text-transform:uppercase;border-bottom:1px solid #0d2e28;padding-bottom:8px;margin-bottom:16px">// Account Status</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, u in enumerate(login.db.list_usernames()):
        locked = login.lockout_mgr.is_locked(u)
        fails  = login.lockout_mgr.failure_count(u)
        color  = "#ff3333" if locked else "#1aff9c"
        status = "LOCKED" if locked else "ACTIVE"
        cls    = "locked" if locked else "active"
        with cols[i % 4]:
            st.markdown(f"""
            <div class="acct-card {cls}">
                <div class="acct-name" style="color:{color}">{u}</div>
                <div class="acct-status">{status} · {fails} fail(s)</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE: MANUAL LOGIN TEST
# ══════════════════════════════════════════════════════════════════════════
elif "Manual" in page:
    st.markdown("""
    <div class="hero" style="padding:56px 48px 48px">
        <div class="hero-grid-bg"></div>
        <div class="hero-glow"></div>
        <div class="hero-eyebrow">Live Demo</div>
        <h1 class="hero-title" style="font-size:44px">Manual <span>Login Test</span></h1>
        <p class="hero-subtitle" style="margin-bottom:0">
            Test credentials directly and observe rate limiting, lockouts,
            and CAPTCHA friction triggering in real time.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    with st.form("login_form"):
        col1, col2, col3 = st.columns(3)
        with col1: username  = st.text_input("Username",     placeholder="admin")
        with col2: password  = st.text_input("Password",     type="password", placeholder="••••••••")
        with col3: ip        = st.text_input("Simulated IP", value="192.168.1.100")
        submitted = st.form_submit_button("🔐  ATTEMPT LOGIN")

    if submitted:
        result = login.attempt_login(username, password, ip=ip)
        ts     = result.timestamp.strftime("%H:%M:%S.%f")[:-3]
        if result.status == LoginResult.SUCCESS:
            st.markdown(
                f'<div class="result-success">'
                f'✔ &nbsp;AUTHENTICATION SUCCESS &nbsp;|&nbsp; {ts}<br>'
                f'Welcome, <b>{username}</b>. Access granted.'
                f'</div>', unsafe_allow_html=True)
        elif result.status == LoginResult.LOCKED:
            st.markdown(
                f'<div class="result-locked">'
                f'🔒 &nbsp;ACCOUNT LOCKED &nbsp;|&nbsp; {ts}<br>'
                f'{result.message}<br>'
                f'RETRY IN: <b>{result.lockout_remaining:.1f}s</b>'
                f'</div>', unsafe_allow_html=True)
        elif result.status == LoginResult.RATE_LIMITED:
            st.markdown(
                f'<div class="result-locked">'
                f'⛔ &nbsp;RATE LIMITED &nbsp;|&nbsp; {ts}<br>'
                f'{result.message}'
                f'</div>', unsafe_allow_html=True)
        else:
            fails     = login.lockout_mgr.failure_count(username)
            remaining = LoginConfig.MAX_ATTEMPTS_BEFORE_LOCKOUT - fails
            st.markdown(
                f'<div class="result-fail">'
                f'✘ &nbsp;AUTHENTICATION FAILED &nbsp;|&nbsp; {ts}<br>'
                f'Invalid credentials. &nbsp;|&nbsp; Failures: <b>{fails}</b> / {LoginConfig.MAX_ATTEMPTS_BEFORE_LOCKOUT}'
                f' &nbsp;|&nbsp; Lockout in: <b>{remaining}</b> more attempt(s)'
                f'</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="site-footer">
    <div>
        <div class="footer-brand">BRUTE<span>FORCE</span> SIMULATOR</div>
        <div class="footer-sub">EDUCATIONAL USE ONLY · NO REAL NETWORK TRAFFIC</div>
    </div>
    <div class="footer-links">
        <span class="footer-link">targetlogin.py</span>
        <span class="footer-link">bruteforce.py</span>
        <span class="footer-link">logs.txt</span>
        <span class="footer-link">README.md</span>
    </div>
    <div class="footer-copy">© 2024 BRUTEFORCE-SIMULATOR</div>
</div>
""", unsafe_allow_html=True)
