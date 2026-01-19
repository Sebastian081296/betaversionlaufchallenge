import streamlit as st
import time as time_sleep
import random
import math
import string
import json
import os
import traceback
import threading
import pandas as pd

NAVY = "#0a2240"
WHITE = "#ffffff"

DEFAULT_WEEK = 1
DEFAULT_ADMIN_PASSWORD = "admin123"
ADMIN_PASSWORD_FILE = "lotterie_admin_pw.txt"
ADMIN_SESSION_TIMEOUT = 600
ALLOWED_CHARS = string.ascii_letters + string.digits + " äöüÄÖÜß-"
PERSIST_FILE = "lotterie_laufchallenge_participants.json"
ERROR_LOG_FILE = "lotterie_error.log"

file_lock = threading.Lock()

st.set_page_config(page_title="Lotterie Laufchallenge Woche", layout="centered")

def log_error(msg):
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception as e:
        st.error("Fehler beim Schreiben des Fehlerprotokolls. Stelle sicher, dass das Programm Schreibrechte auf das Verzeichnis hat.")

def check_unique_names(teilnehmer):
    names = [t.get("name","").strip() for t in teilnehmer]
    lower_names = [n.lower() for n in names]
    name_set = set()
    for n in lower_names:
        if n in name_set:
            return False
        name_set.add(n)
    if any(n == "" for n in names):
        return False
    return True

def validate_name(name):
    name = str(name).strip()
    if not (1 <= len(name) <= 32):
        return False
    for c in name:
        if c not in ALLOWED_CHARS:
            return False
    return True

def fix_invalid_participants(teilnehmer):
    seen = set()
    new_teilnehmer = []
    for t in teilnehmer:
        name = t.get("name", "")
        chance = t.get("chance", 1)
        if not validate_name(name):
            continue
        n_low = name.strip().lower()
        if n_low in seen or name.strip() == "":
            continue
        seen.add(n_low)
        try:
            chance = float(chance)
        except Exception:
            chance = 1
        try:
            chance = max(0.0, min(100.0, float(chance)))
        except Exception:
            chance = 1
        new_teilnehmer.append({
            "name": name.strip(),
            "chance": chance,
        })
    return new_teilnehmer

def load_admin_password():
    if os.path.isfile(ADMIN_PASSWORD_FILE):
        try:
            with open(ADMIN_PASSWORD_FILE, "r", encoding="utf-8") as f:
                pw = f.read().strip()
                if 1 <= len(pw) <= 64:
                    return pw
        except Exception:
            st.warning("Fehler beim Laden des Admin-Passworts.")
            log_error("Admin password file load error:\n" + traceback.format_exc())
    return DEFAULT_ADMIN_PASSWORD

def save_admin_password(new_pw):
    try:
        with open(ADMIN_PASSWORD_FILE, "w", encoding="utf-8") as f:
            f.write(new_pw.strip())
    except Exception:
        st.error("Speichern des neuen Admin-Passworts fehlgeschlagen! Prüfe bitte Dateiberechtigungen für den Arbeitsordner.")
        log_error("Fehler beim Speichern des Admin-Passworts:\n" + traceback.format_exc())

def reset_persistent_data():
    defaults = {
        "teilnehmer": [
            {'name': 'Anna', 'chance': 1},
            {'name': 'Ben', 'chance': 1},
            {'name': 'Chris', 'chance': 1},
            {'name': 'Dana', 'chance': 1},
            {'name': 'Eva', 'chance': 1}
        ],
        "week_nr": DEFAULT_WEEK
    }
    try:
        with file_lock:
            with open(PERSIST_FILE, "w", encoding="utf-8") as f:
                json.dump(defaults, f, ensure_ascii=False)
    except Exception as e:
        log_error("Fehler beim Zurücksetzen der Persistent-File:\n" + traceback.format_exc())
    return defaults

def load_persistent_data():
    with file_lock:
        if os.path.isfile(PERSIST_FILE):
            try:
                with open(PERSIST_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise Exception("Persistenzdaten kein Dict!")
                teilnehmer = data.get("teilnehmer", [])
                week_nr = int(data.get("week_nr", DEFAULT_WEEK))
                teilnehmer_fixed = fix_invalid_participants(teilnehmer)
                if len(teilnehmer_fixed) == 0:
                    teilnehmer_fixed = [
                        {'name': 'Anna', 'chance': 1},
                        {'name': 'Ben', 'chance': 1},
                        {'name': 'Chris', 'chance': 1},
                        {'name': 'Dana', 'chance': 1},
                        {'name': 'Eva', 'chance': 1}
                    ]
                if len(teilnehmer_fixed) != len(teilnehmer):
                    log_error("Warnung: Fehlerhafte oder doppelte/leere Namen im JSON entfernt.")
                return {"teilnehmer": teilnehmer_fixed, "week_nr": week_nr}
            except Exception as ex:
                st.error("Daten konnten nicht geladen werden. Die Standardwerte werden eingesetzt. Deine Lotterie-Daten waren offenbar beschädigt oder nicht lesbar.")
                st.warning("Tipp: Falls ein Datenverlust aufgetreten ist, prüfe bitte, ob eine Sicherungskopie der Datei 'lotterie_laufchallenge_participants.json' oder ein Backup verfügbar ist. Die Anwendung hat Standarddaten geladen.")
                log_error("Persistenz-File Ladefehler:\n" + traceback.format_exc())
                try:
                    defaults = reset_persistent_data()
                    return defaults
                except Exception as exc2:
                    st.error("Kritischer Fehler: Die Lotterie-Anwendungsdaten konnten nicht wiederhergestellt werden. Bitte überprüfe Dateirechte/Plattenplatz.")
                    st.warning("Die Lotterie kann erst nach Wiederherstellung einer gültigen Datendatei oder erneuter Anlage von Teilnehmern genutzt werden.")
                    log_error("Kritischer Fehler beim Wiederherstellen der Lotterie-Daten:\n" + traceback.format_exc())
                    return {"teilnehmer": [], "week_nr": DEFAULT_WEEK}
        else:
            return {
                "teilnehmer": [
                    {'name': 'Anna', 'chance': 1},
                    {'name': 'Ben', 'chance': 1},
                    {'name': 'Chris', 'chance': 1},
                    {'name': 'Dana', 'chance': 1},
                    {'name': 'Eva', 'chance': 1}
                ],
                "week_nr": DEFAULT_WEEK
            }

def save_persistent_data(teilnehmer, week_nr):
    fixed = fix_invalid_participants(teilnehmer)
    if not check_unique_names(fixed) or any(not validate_name(t["name"]) for t in fixed):
        return
    with file_lock:
        try:
            with open(PERSIST_FILE, "w", encoding="utf-8") as f:
                json.dump({"teilnehmer": fixed, "week_nr": week_nr}, f, ensure_ascii=False)
            st.success("Daten erfolgreich gespeichert.", icon="✅")
        except Exception as e:
            st.error("Fehler beim Speichern! Prüfe, ob die Datei ggf. schreibgeschützt ist oder von einem anderen Programm genutzt wird. Hilfe: Beende alle Programme, die die Datei blockieren könnten, prüfe die Dateiberechtigungen und versuche es erneut.")
            st.warning("Speichern der Daten fehlgeschlagen! Änderungen wurden möglicherweise nicht übernommen.")
            log_error("Fehler beim Speichern der Teilnehmerdaten:\n" + traceback.format_exc())

if "admin_password" not in st.session_state:
    st.session_state.admin_password = load_admin_password()

if "initialized" not in st.session_state:
    persistent = load_persistent_data()
    st.session_state.teilnehmer = persistent["teilnehmer"]
    st.session_state.week_nr = persistent.get("week_nr", DEFAULT_WEEK)
    st.session_state.initialized = True

if 'view' not in st.session_state:
    st.session_state.view = 'user'
if 'winner' not in st.session_state:
    st.session_state.winner = None
if 'admin_pw_entered' not in st.session_state:
    st.session_state.admin_pw_entered = False
if 'drawing' not in st.session_state:
    st.session_state.drawing = False
if "admin_last_active" not in st.session_state:
    st.session_state.admin_last_active = None
if "font_size" not in st.session_state:
    st.session_state.font_size = "Normal"
if "error_field" not in st.session_state:
    st.session_state.error_field = None
if "add_participant_error" not in st.session_state:
    st.session_state.add_participant_error = None
if "user_mode_locked" not in st.session_state:
    st.session_state.user_mode_locked = False
if "draw_history" not in st.session_state:
    st.session_state.draw_history = []

def sanitize_teilnehmer():
    valid_teilnehmer = []
    for entry in st.session_state.teilnehmer:
        name = entry.get("name", "")
        try:
            chance = float(entry.get("chance", 1.0))
            chance = max(0.0, min(100.0, chance))
        except Exception:
            chance = 1
        chance = max(0, min(100, chance))
        name = name if isinstance(name, str) else ""
        valid_teilnehmer.append({"name": name, "chance": chance})
    st.session_state.teilnehmer = fix_invalid_participants(valid_teilnehmer)

sanitize_teilnehmer()

def check_admin_session():
    if not st.session_state.get("admin_pw_entered", False):
        st.session_state.view = "user"
        st.session_state.admin_last_active = None
        st.session_state.error_field = None
        return False
    now = time_sleep.time()
    if st.session_state.admin_last_active is None:
        st.session_state.admin_last_active = now
    elif now - st.session_state.admin_last_active > ADMIN_SESSION_TIMEOUT:
        st.session_state.admin_pw_entered = False
        st.session_state.view = "user"
        st.session_state.admin_last_active = None
        st.session_state.error_field = None
        st.session_state.admin_timeout_banner = True
        return False
    else:
        st.session_state.admin_last_active = now
    return True

def set_fontsize_class():
    fs = st.session_state.font_size
    if fs == "Klein":
        return "html, body, .main, .block-container, .stApp { font-size: 15px !important; }"
    elif fs == "Normal":
        return "html, body, .main, .block-container, .stApp { font-size: 17px !important; }"
    elif fs == "Groß":
        return "html, body, .main, .block-container, .stApp { font-size: 20px !important; }"
    return ""

st.markdown(f"""
    <style>
    html, body, .main, .block-container, .stApp {{
        background-color: {NAVY} !important;
        color: {WHITE} !important;
    }}
    h1, h2, h3, h4 {{
        color: {WHITE} !important;
    }}
    .stButton>button {{
        background-color: {WHITE} !important;
        color: {NAVY} !important;
        border: none !important;
        border-radius: 4px;
        font-weight: bold;
        font-size: 1.18em;
        transition: background 0.2s;
    }}
    .stButton>button:hover {{
        background-color: #e2e2e2 !important;
        color: {NAVY} !important;
    }}
    .admin_hint {{
        font-weight:900;
        color:#fff;
        border:3px solid #ffd700;
        background:#18366ed7;
        border-radius:6px;
        padding:0.32em 1.1em;
        font-size:1.09em;
        filter:drop-shadow(0 0 6px #ffd700B0);
        margin-bottom:1.4em;
        margin-top:0.6em;
        text-align:center;
        letter-spacing:0.02em;
        box-shadow:0 0 9px #ffd70044;
    }}
    .admin_hint_button {{
        font-weight:900;
        color:#ffd700;
        border:2px solid #ffd700;
        background:#1e336a;
        border-radius:8px;
        padding:0.39em 1.2em;
        font-size:1.18em;
        filter:drop-shadow(0 0 3px #ffd700c0);
        margin-bottom:0.7em;
        text-align:center;
        margin-top:1.1em;
        cursor:pointer;
        transition:.15s background;
        display: inline-block;
    }}
    .admin_hint_button:hover {{
        background: #ffd700;
        color: #0a2240;
        border:2px solid #ffd700;
    }}
    .st-bb, .st-ce {{
        color: {WHITE} !important;
    }}
    .stAlert, .st-error, .st-warning, .st-info, .st-success, .stToast, .stToast-content, .stAlert-content, .stModal, .stToast .e1zj397y0, .stAlert, .stException {{
        background: {NAVY} !important;
        color: {WHITE} !important;
        border: 1px solid {WHITE} !important;
        box-shadow: 0 0 8px {WHITE}33 !important;
    }}
    .stAlert {{
        border-left: 0.4rem solid {WHITE} !important;
        background: rgba(255,255,255,0.03) !important;
        color: {WHITE} !important;
    }}
    .stTextInput>div>input, .stNumberInput input {{
        background-color: {WHITE} !important;
        color: {NAVY} !important;
    }}
    ::placeholder {{
        color: #fff !important;
        opacity: 1!important;
    }}
    .stTooltipContent {{
        color: #fff !important;
    }}
    .navy-warning {{
        background: rgba(10,34,64,0.97);
        color: #fff !important;
        padding: 0.5em 0.8em;
        border-left: 0.4rem solid #fff;
        border-radius: 4px;
        margin-bottom:0.7em;
        font-size:1.05em;
        font-weight:600;
    }}
    .winner-pfeil-blink {{
        animation: blinkwinner 1.06s 3;
        font-size:2.03em;
        color: gold;
        font-weight: 900;
        margin-left: 0.49em;
        margin-right: 0.23em;
        filter: drop-shadow(0 0 14px #ffe066aa);
    }}
    @keyframes blinkwinner {{
        0%   {{color: gold; filter: drop-shadow(0 0 12px #ffe066aa); opacity: 1;}}
        35%  {{color: #fffc; filter: drop-shadow(0 0 21px #ffe066); opacity: .18;}}
        65%  {{color: #ffd700; filter: drop-shadow(0 0 3px #fffcb2); opacity: 1;}}
        100% {{color: gold; filter: drop-shadow(0 0 18px #ffe066aa); opacity: 1;}}
    }}
    .teilnehmer-legend-flex {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.18em 0.18em;
        justify-content:center;
        align-items: flex-start;
        margin-top:0.25em;
        margin-bottom:0.25em;
        overflow-x:auto;
        background: {NAVY} !important;
    }}
    .teilnehmer-legend-flex::-webkit-scrollbar {{
        height: 11px;
    }}
    .teilnehmer-legend-flex::-webkit-scrollbar-thumb {{
        background: #33518899;
        border-radius: 8px;
    }}
    .trennlinie {{
        border-top: 3px solid {WHITE};
        margin: 2em 0 1.3em 0;
    }}
    .disabled-button-custom {{
        background: #ccc !important;
        color: #888 !important;
        border: none!important;
        cursor: not-allowed !important;
        opacity: 0.64!important;
        pointer-events: none !important;
        font-weight: normal !important;
    }}
    .dataframe tbody tr {{
        background-color: {NAVY} !important;
    }}
    .dataframe thead th {{
        background-color: #011848 !important;
        color: #fff !important;
        font-weight: bold;
    }}
    .dataframe td, .dataframe th {{
        color: #fff !important;
        border-color: #333 !important;
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)
st.markdown(f"<style>{set_fontsize_class()}</style>", unsafe_allow_html=True)

def name_colors(num):
    base_colors = [
        "#4896ff", "#40c57b", "#f7c023", "#ef5668", "#195998", "#8962c7", "#f88b30", "#188566", "#e22f80", "#ae1947",
        "#3988b3", "#7eac2f", "#d1a413", "#d65e28", "#683eb7", "#318c59", "#f060b7", "#ca374c", "#0579a2", "#43972b",
        "#e8bb5c", "#ff6f43", "#5b45ad", "#16a086", "#f86bca", "#be2744", "#176ca4", "#6abc1a", "#ffd700", "#ce5d3d", "#524ebe"
    ]
    if num <= len(base_colors):
        return base_colors[:num]
    else:
        colors = []
        for i in range(num):
            base = base_colors[i % len(base_colors)]
            factor = 1 - 0.11*(i // len(base_colors))
            r = int(int(base[1:3],16)*factor)
            g = int(int(base[3:5],16)*factor)
            b = int(int(base[5:7],16)*factor)
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        return colors

def _luminance(hexcol):
    r = int(hexcol[1:3], 16)/255
    g = int(hexcol[3:5], 16)/255
    b = int(hexcol[5:7], 16)/255
    return 0.2126*r + 0.7152*g + 0.0722*b

def get_duplicate_name_index_list(teilnehmer):
    names = [t.get("name","").strip().lower() for t in teilnehmer]
    seen = {}
    index_set = set()
    for idx, n in enumerate(names):
        if n == "" or n in seen:
            index_set.add(idx)
        seen[n] = seen.get(n, 0)+1
    for name, count in seen.items():
        if count > 1:
            matches = [i for i,x in enumerate(names) if x == name]
            index_set.update(matches)
    return sorted(list(index_set))

def get_colorblind_symbols(idx):
    symbols = [
        "●", "■", "▲", "◆", "★", "⬤", "⬟", "⬢", "◼", "⬘", "⬖", "⬗",
        "◉", "◍", "◒", "◐", "◑", "◒", "☀", "☁", "☂", "☉", "✶", "✳"
    ]
    return symbols[idx % len(symbols)]

def compute_angle_for_index(chances, winner_idx):
    total = sum(chances)
    angle_start = 0
    for idx, c in enumerate(chances):
        angle_span = 360 * c/total
        a0 = angle_start
        a1 = angle_start + angle_span
        if idx == winner_idx:
            target_angle = (a0 + a1) / 2
            return target_angle
        angle_start = a1
    return 0

def find_winner_by_pointer(names, chances, angle):
    total = sum(chances)
    if total <= 0:
        return None
    angle %= 360
    pointer_angle = (360 - angle) % 360
    cum_angle = 0
    for idx, c in enumerate(chances):
        seg_span = 360.0 * c / total
        seg_start = cum_angle
        seg_end = cum_angle + seg_span
        if seg_start <= pointer_angle < seg_end or (abs(pointer_angle - seg_end) < 1e-6 and idx == len(chances) - 1):
            return idx
        cum_angle += seg_span
    if pointer_angle == 0 and len(chances) > 0:
        return 0
    min_dist = 9999
    min_idx = 0
    cum_angle = 0
    for idx, c in enumerate(chances):
        seg_span = 360.0 * c / total
        seg_start = cum_angle
        seg_end = cum_angle + seg_span
        seg_center = (seg_start + seg_end) / 2
        d = abs(((pointer_angle - seg_center + 540) % 360) - 180)
        if d < min_dist:
            min_dist = d
            min_idx = idx
        cum_angle += seg_span
    return min_idx

def exact_rotation_for_winner(names, chances, winner_idx):
    total = sum(chances)
    angle_start = 0
    for idx, c in enumerate(chances):
        angle_span = 360 * c / total
        a0 = angle_start
        a1 = angle_start + angle_span
        if idx == winner_idx:
            center_angle = (a0 + a1) / 2
            rotation_angle =  (center_angle) % 360
            return rotation_angle
        angle_start = a1
    return 0

def get_wheel_svg_html(names, chances, colors, rotation, winner_idx=None, use_symbols_param=None, force_highlight_idx=None, draw_winner_line=False, winner_line_angle=None):
    base_rad = 175
    if len(names) > 36:
        RAD = 90
    elif len(names) > 30:
        RAD = 100
    elif len(names) > 24:
        RAD = 125
    elif len(names) > 18:
        RAD = 145
    elif len(names) > 14:
        RAD = 175
    else:
        RAD = base_rad
    X0, Y0 = RAD+10, RAD+10
    total = sum(chances)
    angle_start = 0
    svg_parts = []

    if use_symbols_param is not None:
        use_symbols = use_symbols_param
    else:
        use_symbols = len(names) >= 30

    if len(names) >= 30:
        suppress_svg_labels = True
        force_legend = True
        use_symbols = True
    else:
        suppress_svg_labels = False
        force_legend = False
        use_symbols = False

    if len(names) > 48:
        font_scaling = 0.36
    elif len(names) > 44:
        font_scaling = 0.38
    elif len(names) > 40:
        font_scaling = 0.40
    elif len(names) > 36:
        font_scaling = 0.42
    elif len(names) > 32:
        font_scaling = 0.45
    elif len(names) > 28:
        font_scaling = 0.53
    elif len(names) > 24:
        font_scaling = 0.60
    elif len(names) > 20:
        font_scaling = 0.70
    elif len(names) > 14:
        font_scaling = 0.83
    else:
        font_scaling = max(0.73, 1.28 - (0.03*len(names)))
    text_rad = RAD*0.74 if len(names) < 16 else RAD*0.88

    width = 2*RAD+40
    height = 2*RAD+100
    svg_parts.append(f"<svg width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'>")
    svg_parts.append("""
    <defs>
        <filter id="dropShadow" height="130%">
          <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
          <feBlend in="SourceGraphic" in2="SourceAlpha" mode="normal"/>
        </filter>
        <linearGradient id="radfade" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="40%" style="stop-color:#fff;stop-opacity:0.16;" />
            <stop offset="80%" style="stop-color:#aaa;stop-opacity:0.04;" />
            <stop offset="100%" style="stop-color:#fff;stop-opacity:0;" />
        </linearGradient>
        <radialGradient id="winnerhighlight" cx="50%" cy="50%" r="80%">
            <stop offset="40%" style="stop-color:#ffe066; stop-opacity:0.91;" />
            <stop offset="90%" style="stop-color:#ffe06600; stop-opacity:0;" />
        </radialGradient>
        <radialGradient id="extra_highlight" cx="50%" cy="50%" r="80%">
            <stop offset="30%" style="stop-color:#74b9ff88; stop-opacity:0.90;" />
            <stop offset="90%" style="stop-color:#6c5ce711; stop-opacity:0;" />
        </radialGradient>
    </defs>
    """)
    svg_parts.append(f"<g transform='rotate({rotation},{X0},{Y0})'>")
    segment_mid_angles = []
    winner_highlight_drawn = False
    winner_found = False
    angle_list = []
    winner_start_angle = None
    winner_end_angle = None
    winner_text_angle = None
    for i,(n,c,col) in enumerate(zip(names,chances,colors)):
        angle_span = 360 * c/total if total > 0 else 0
        a0 = angle_start
        a1 = angle_start + angle_span
        large = 1 if (a1-a0)>180 else 0
        x1 = X0 + RAD*math.cos(math.radians(a0-90))
        y1 = Y0 + RAD*math.sin(math.radians(a0-90))
        x2 = X0 + RAD*math.cos(math.radians(a1-90))
        y2 = Y0 + RAD*math.sin(math.radians(a1-90))
        fillcol = col
        extra_svg = ""
        highlight_this = False
        if winner_idx is not None and i == winner_idx:
            highlight_this = True
            winner_start_angle = a0
            winner_end_angle = a1
            winner_text_angle = (a0 + a1)/2
        if force_highlight_idx is not None and i == force_highlight_idx:
            highlight_this = True
            winner_start_angle = a0
            winner_end_angle = a1
            winner_text_angle = (a0 + a1)/2

        if highlight_this:
            svg_parts.append(
                f"<path d='M{X0},{Y0} L{x1},{y1} A{RAD},{RAD} 0 {large},1 {x2},{y2} z' "
                f"fill='{fillcol}' stroke='#fff' stroke-width='2'/>"
            )
            winner_highlight_drawn = True
            winner_found = True
        else:
            svg_parts.append(
                f"<path d='M{X0},{Y0} L{x1},{y1} A{RAD},{RAD} 0 {large},1 {x2},{y2} z' "
                f"fill='{fillcol}' stroke='#fff' stroke-width='2'/>"
            )
        am = (a0+a1)/2
        segment_mid_angles.append(am)
        tx = X0 + text_rad*math.cos(math.radians(am-90))
        ty = Y0 + text_rad*math.sin(math.radians(am-90))
        txtcolor = WHITE if _luminance(fillcol) < 0.33 else NAVY
        label = n
        if use_symbols:
            label = get_colorblind_symbols(i) + " " + n
        if not suppress_svg_labels:
            font_weight = "bold"
            text_decoration = ""
            text_shadow = ""
            name_extra = ""
            if highlight_this:
                font_weight = "900"
                text_decoration = ";text-decoration:underline"
                text_shadow = "text-shadow:0 0 12px #ffd700,0 0 2px #000;"
                name_extra = " 🏆"
            svg_parts.append(
                f"<text x='{tx}' y='{ty}' text-anchor='middle' dominant-baseline='middle' "
                f"fill='{txtcolor}' font-size='{19*font_scaling}' font-family='Arial' font-weight='{font_weight}' "
                f"transform='rotate({am-90},{tx},{ty})' "
                f"style='font-weight:{font_weight};{text_decoration}{text_shadow}'>"
                    f"{label if not highlight_this else (label + name_extra)}"
                f"</text>"
            )
        angle_start = a1

    if draw_winner_line and winner_found and winner_text_angle is not None:
        wx = X0 + (RAD+25)*math.cos(math.radians(winner_text_angle-90))
        wy = Y0 + (RAD+25)*math.sin(math.radians(winner_text_angle-90))
        svg_parts.append(
            f"<line x1='{X0}' y1='{Y0}' x2='{wx}' y2='{wy}' stroke='#ffd700' stroke-width='6' opacity='0.93' filter='url(#dropShadow)' />"
        )

    svg_parts.append(f"</g>")

    svg_parts.append(f"<circle cx='{X0}' cy='{Y0}' r='{RAD}' fill='url(#radfade)' />")

    pointer_html = f"<polygon points='{X0-14},{Y0-12} {X0+14},{Y0-12} {X0},{Y0-47}' fill='{WHITE}' stroke='{NAVY}' stroke-width='3' />"
    svg_parts.append(pointer_html)
    svg_parts.append(f"<circle cx='{X0}' cy='{Y0}' r='15' fill='{NAVY}' stroke='{WHITE}' stroke-width='3' />")
    svg_parts.append(f"<text x='{X0}' y='{Y0+5}' text-anchor='middle' fill='{WHITE}' font-size='22' font-family='Arial' font-weight='bold'></text>")
    svg_parts.append("</svg>")

    legend_items = []
    for i,(n, c, col) in enumerate(zip(names, chances, colors)):
        txtc = WHITE if _luminance(col)<0.33 else NAVY
        legend_label = n
        if use_symbols:
            legend_label = get_colorblind_symbols(i) + " " + n
        winner_style = ""
        winner_emoji = ""
        winner_arrow = ""
        if (winner_idx is not None and i == winner_idx) or (force_highlight_idx is not None and i == force_highlight_idx):
            winner_style = "background:linear-gradient(92deg,#ffd700cc 60%,#fff9e288 100%)!important;color:#112!important;font-weight:900;border: 2px solid #ffd700; box-shadow: 0 0 18px #ffd700b0;"
            winner_emoji = "🏆 "
            winner_arrow = "<span class='winner-pfeil-blink'>↑</span>"

        legend_items.append(
            f"{winner_arrow}<span style='background:{col};color:{txtc};padding:0.33em 0.52em; margin:0.07em 0.22em 0.07em 0; border-radius:17px; font-size:1.04em; display:inline-block;min-width:54px;"
            f"{winner_style}'>"
            f"{winner_emoji}{legend_label} <span style='font-size:0.69em;font-weight:300;'>&times;{c}</span></span>"
        )
    warning_html = ""
    if use_symbols or force_legend:
        warning_html = "<div class='navy-warning'>⚠️ Info: Bei vielen Teilnehmern werden die Namen nur <b>in der Legende</b> angezeigt. Die Zuordnung erfolgt eindeutig über Symbole.</div>"
    #accessibility_html = "<div style='margin-bottom:0.5em;font-size:1.04em;color:#fff;'>Barrierefreiheit: Jeder Name erhält ein eindeutiges Symbol (hilft bei Farbschwäche). Die Legende ist immer eindeutig und vollständig. Mindestens WCAG-Kontrast wird für Farben geprüft; zu helle Farben werden nachgedunkelt.</div>"
    if len(names) > 15:
        legend_scroll_hint_html = "<div class='navy-warning' style='background: #143876; color: #fff; font-size:0.95em; margin-bottom:.4em;'>ℹ️ Tipp: Bei vielen Teilnehmern ist die <b>Legende horizontal scrollbar</b>. Nutze ggf. Wischgesten oder das Scrollrad, um alle Namen/Symbole zu sehen.</div>"
    else:
        legend_scroll_hint_html = ""
    #legend_html = warning_html + legend_scroll_hint_html + "<div class='teilnehmer-legend-flex'>" + "".join(legend_items) + "</div>"

    winner_arrow_box = ""
    if winner_idx is not None or force_highlight_idx is not None:
        # winner_arrow_box = (
        #     "<div style='text-align:center;margin-top:0.9em;margin-bottom:1em;'>"
        #     "<span style='color:gold;font-weight:900;font-size:2.2em;margin-bottom:1.5em;letter-spacing:.1em;'>"
        #     "↑"
        #     "</span>"
        #     "<div style='color:#ffd700;font-weight:900;font-size:1.17em;margin-bottom:0;margin-top:0.33em;'>"
        #     "Der Gewinner ist immer der Name, <b>auf den der weiße Pfeil zeigt!</b>"
        #     "</div>"
        #     "</div>"
        # )
        if winner_found and draw_winner_line:
            Test=1
            winner_arrow_box += "<div style='text-align:center;color:#ffd700;font-weight:900;'>Goldene Linie verbindet Gewinnersegment mit Legende.</div>"
    return  "<div style='text-align:center;'>" + "".join(svg_parts) + "</div>" #+ legend_html

def get_draw_context_from_session():
    ctx_keys = [
        "names_drawn", "chances_drawn", "colors_drawn", "winner_idx_drawn",
        "use_symbols_drawn", "final_angle"
    ]
    ctx = {}
    has_all = all(k in st.session_state and st.session_state[k] is not None for k in ctx_keys[:-1])
    if not has_all:
        return None
    for k in ctx_keys:
        ctx[k] = st.session_state.get(k)
    return ctx

def clear_draw_context():
    keys = [
        "winner_idx_drawn", "names_drawn", "chances_drawn", "colors_drawn",
        "use_symbols_drawn", "final_angle", "winner"
    ]
    for k in keys:
        if k in st.session_state:
            st.session_state[k] = None
    st.session_state.draw_state = "pre_draw"

def show_winner_panel_from_context(draw_context, show_consistency_hint=True):
    names = draw_context["names_drawn"]
    colors = draw_context["colors_drawn"]
    chances = draw_context["chances_drawn"]
    final_angle = draw_context.get("final_angle", 0)
    winner_idx = find_winner_by_pointer(names, chances, final_angle)
    use_symbols = draw_context.get("use_symbols_drawn", False)
    n = len(names)
    if n == 0 or winner_idx is None or winner_idx >= n:
        return
    winner_label = names[winner_idx]
    winner_color = colors[winner_idx]
    winner_chance = chances[winner_idx]
    txtc = WHITE if _luminance(winner_color) < 0.33 else NAVY
    legend_label = winner_label
    if use_symbols:
        winner_symbol = get_colorblind_symbols(winner_idx)
        legend_label = f"{winner_symbol} {winner_label}"
    legend_style = "background:linear-gradient(94deg,#ffd700bb 70%,#fff7d099 100%)!important;color:#112!important;font-weight:900;border: 2.5px solid #ffd700;padding:0.39em 0.52em;margin:0.18em 0;border-radius:18px;box-shadow: 0 0 7px #ffd70080;"
    legend_html = (
        f"<div style='margin-top:1em;margin-bottom:0.3em;display:flex;justify-content:center;'>"
        f"<span style='background:{winner_color};{legend_style};color:{txtc};font-size:1.23em;min-width:64px;display:inline-flex;align-items:center;'>"
        #f"{legend_label} <span style='font-size:0.77em;font-weight:300;margin-left:9px;'>&times;{winner_chance}</span> <span style='margin-left:9px;'>🏆</span></span></div>"
    )
    # explanation = (
    #     "<div style='color:gold;font-weight:900;font-size:1.13em;margin-bottom:0.7em;margin-top:0.1em;padding:0.7em 1.1em 0.7em 1.1em; background: #1a3c6d;border-radius:6px;'>"
    #     "🎯 <b>Der Gewinner ist exakt der Name, auf den der <u>weiße Pfeil (12 Uhr Richtung)</u> zeigt!</b> (siehe Rad und gelbe Markierung unten) "
    #     "<br>Bedenke: Bei extremen Losunterschieden (z.B. 99:1) kann der Gewinner ein sehr kleines Segment haben."
    #     "</div>"
    # )
    prob_list = []
    try:
        fc = sum(float(x) for x in chances)
        for c in chances:
            v = float(c)
            prob = (v/fc*100.0) if fc>0 else 0
            prob_list.append(prob)
    except Exception:
        prob_list = []
    warn_risk = False
    maxprob = max(prob_list) if prob_list else 0
    minprob = min([p for p in prob_list if p > 0]) if prob_list else 0
    if maxprob > 80 and minprob < 2 and minprob > 0:
        warn_risk = True
    risk_html = ""
    if warn_risk and show_consistency_hint:
        risk_html = "<div style='color:#fff; background: #b92337; font-weight:900; border-radius:7px;padding:.6em 1.1em;margin:.7em 0 0.7em 0;'>⚠️ Hinweis: Extrem asymmetrische Lose (z.B. 99:1) führen zu sehr kleinen Segmenten. In seltenen Fällen kann das Verhalten/Umlauf wegen Rundungsfehler abweichen. Entscheidend ist immer nur der Name am WEIßEN PFEIL!</div>"
    style = f"""
        background: linear-gradient(97deg, #ffd70032 0 70%, #3a65af99 100%);
        color: #fffa;
        border-radius: 13px;
        border:3px solid #ffd700;
        margin: 1.2em auto 1.2em auto;
        padding: 1.1em 1.8em 1.1em 1.8em;
        max-width: 500px;
        text-align:center;
        font-size:2.1em;
        font-weight:800;
        text-shadow:1px 1px 9px #333, 0 0 17px #ffd700;
        box-shadow: 0 0 19px #ffd70080;
        display:flex; flex-direction: row; align-items:center; justify-content:center;
        position:relative;
    """
    colorbox_html = f"<span style='display:inline-block;width:28px;height:28px;background:{winner_color};border-radius:5px;margin-right:17px;border:2.5px solid #fff;box-shadow:0 0 7px #222;'>&nbsp;</span>"
    html = legend_html + risk_html + f"<div style='{style}'>{colorbox_html}🎉 Gewinner: <span style='color:gold;'>{legend_label}</span> 🎉</div>"
    #st.markdown(html, unsafe_allow_html=True)

def winner_history_context_still_valid(dctx):
    if dctx is None:
        return False
    names = dctx.get("names_drawn", [])
    chances = dctx.get("chances_drawn", [])
    colors = dctx.get("colors_drawn", [])
    if not isinstance(names, list) or not isinstance(chances, list) or not isinstance(colors, list):
        return False
    if len(names) == 0 or len(chances) == 0 or len(names) != len(chances) or len(names) != len(colors):
        return False
    for n in names:
        if not isinstance(n, str) or n.strip() == "":
            return False
    for c in chances:
        try:
            ctest = float(c)
            if not (0 <= ctest <= 100):
                return False
        except Exception:
            return False
    try:
        if not any(float(c) > 0 for c in chances):
            return False
    except Exception:
        return False
    final_angle = dctx.get("final_angle", None)
    winner_idx = find_winner_by_pointer(names, chances, final_angle if final_angle is not None else 0)
    if winner_idx is None or winner_idx >= len(names):
        return False
    for color in colors:
        if not isinstance(color, str) or not color.startswith("#") or len(color) < 7:
            return False
    return True

def show_draw_history():
    if not st.session_state.draw_history:
        st.info("Es gibt noch keine historischen Ziehungen in dieser Session.")
        return
    st.markdown("<div style='font-size:1.15em;color:#fff;font-weight:bold;margin-top:1.1em;margin-bottom:.6em;'>Ziehungshistorie / Letzte Gewinner (nur diese Session):</div>", unsafe_allow_html=True)
    for i, draw_ctx in enumerate(reversed(st.session_state.draw_history[-8:])):
        if not winner_history_context_still_valid(draw_ctx):
            st.warning("⚠️ Historische Ziehung ist nicht mehr konsistent oder Teilnehmer/Daten sind beschädigt oder unvollständig. Gewinner ist nicht mehr rekonstruierbar. (z.B. durch Datenänderung/import außerhalb der App oder Fehler im Dateisystem)", icon="❗")
            continue
        names = draw_ctx.get("names_drawn", [])
        chances = draw_ctx.get("chances_drawn", [])
        colors = draw_ctx.get("colors_drawn", [])
        final_angle = draw_ctx.get("final_angle", 0)
        use_symbols = draw_ctx.get("use_symbols_drawn", False)
        winner_idx = find_winner_by_pointer(names, chances, final_angle)
        winner_rotation = exact_rotation_for_winner(names, chances, winner_idx)
        st.markdown(f"<div style='font-size:0.98em;color:#ffd700;font-weight:700;margin-top:.33em;'>Ziehung (letzte #{len(st.session_state.draw_history)-i})</div>", unsafe_allow_html=True)

        st.markdown(
            get_wheel_svg_html(
                names,
                chances,
                colors,
                rotation=winner_rotation,
                winner_idx=winner_idx,
                use_symbols_param=use_symbols,
                force_highlight_idx=winner_idx,
                draw_winner_line=False
            ),
            unsafe_allow_html=True
        )
        hist_ctx = draw_ctx.copy()
        hist_ctx["winner_idx_drawn"] = winner_idx
        show_winner_panel_from_context(hist_ctx, show_consistency_hint=True)
        st.markdown(
            "<div style='margin-top:0.7em;margin-bottom:1.2em;font-size:1.01em;color:#ffd700;background: #1a3c6d;padding: 0.7em 1.1em 0.7em 1.1em; border-radius:6px;font-weight:800;'>🏆 <b>Zur Erinnerung:</b> Der Gewinner ist immer <u>der Name, auf den der weiße Pfeil im Rad zeigt</u> (siehe oben gelbe Markierung / Pfeil).<br>Auch bei extrem kleinen Segmenten (z.B. 99:1) entscheidet immer der Pfeil!</div>",
            unsafe_allow_html=True
        )
        st.markdown("<hr>", unsafe_allow_html=True)

if "draw_state" not in st.session_state:
    st.session_state.draw_state = "pre_draw"
if "winner" not in st.session_state:
    st.session_state.winner = None
if "teilnehmer" not in st.session_state:
    st.session_state.teilnehmer = [
        {"name": "Alice", "chance": 1},
        {"name": "Bob", "chance": 2},
        {"name": "Charlie", "chance": 3}
    ]
if "admin_timeout_banner" not in st.session_state:
    st.session_state.admin_timeout_banner = False
    
def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def show_wheel_animation(teilnehmer, placeholder):
    st.session_state.drawing = True

    # -------------------------
    # 1) Validierung
    # -------------------------
    valid_teilnehmer = [
        t for t in teilnehmer
        if t.get("chance", 0) > 0
        and isinstance(t.get("name", ""), str)
        and t.get("name", "").strip() != ""
    ]

    if not valid_teilnehmer:
        st.session_state.drawing = False
        st.error("Kein gültiger Teilnehmer für die Ziehung vorhanden!")
        return

    names = [t["name"] for t in valid_teilnehmer]
    chances = [t["chance"] for t in valid_teilnehmer]
    colors = name_colors(len(names))
    use_symbols_drawn = len(names) >= 30

    # -------------------------
    # 2) Animationsparameter
    # -------------------------
    import secrets

    steps = random.randint(50, 250)
    step_duration = 0.11  # ~6 Sekunden gesamt
    BASE_ROUNDS = secrets.choice([6, 7, 8])
    RANDOM_REST = secrets.randbelow(360)

    FINAL_ROTATION = BASE_ROUNDS * 360 + RANDOM_REST

    fancy_angles = [
        math.sin(math.pi * step / steps) * 4
        for step in range(steps + 1)
    ]

    angle_list = []
    progress_placeholder = st.empty()
    winner_placeholder = st.empty()
    
    for step in range(steps + 1):
        linear = step / steps
        progress = ease_out_cubic(linear)
        angle = FINAL_ROTATION * progress #+ fancy_angles[step]
    
        angle_list.append(angle % 360)
    
        progress_placeholder.progress(
            progress,
            text=f"Ziehung läuft ..."
        )
    
        placeholder.markdown(
            get_wheel_svg_html(
                names,
                chances,
                colors,
                rotation=angle % 360,   # Animation
                winner_idx=None,
                use_symbols_param=use_symbols_drawn
            ),
            unsafe_allow_html=True
        )
    
        time_sleep.sleep(step_duration)

    # -------------------------
    # 4) Gewinner aus dem finalen Winkel bestimmen
    # -------------------------
    final_angle = angle_list[-1] % 360
    winner_idx = find_winner_by_pointer(names, chances, final_angle)

    
    placeholder.markdown(
        get_wheel_svg_html(
            names,
            chances,
            colors,
            rotation=final_angle,           # exakte Endposition
            winner_idx=winner_idx,          # Gewinnersegment hervorheben
            use_symbols_param=use_symbols_drawn,
            force_highlight_idx=winner_idx,
            draw_winner_line=False          # optional: goldene Linie zum Gewinnersegment
        ),
        unsafe_allow_html=True
    )
        
    

    #st.experimental_rerun()
    #time_sleep.sleep(5)
    # -------------------------
    # 5) Speicherung
    # -------------------------
    drawn_context = {
        "winner": names[winner_idx],
        "winner_idx_drawn": winner_idx,
        "names_drawn": names,
        "chances_drawn": chances,
        "colors_drawn": colors,
        "use_symbols_drawn": use_symbols_drawn,
        "final_angle": final_angle
    }
    for k, v in drawn_context.items():
        st.session_state[k] = v
    st.session_state.draw_history.append(drawn_context)
    
    # -------------------------
    # 6) Finale Anzeige
    # -------------------------
    # placeholder.markdown(
    #     get_wheel_svg_html(
    #         names,
    #         chances,
    #         colors,
    #         rotation=final_angle,        # exakte Endposition
    #         winner_idx=winner_idx,       # Gewinner auf 12 Uhr markieren
    #         use_symbols_param=use_symbols_drawn,
    #         force_highlight_idx=winner_idx
    #     ),
    #     unsafe_allow_html=True
    # )


def winner_context_still_valid(dctx, teilnehmer_now):
    if dctx is None:
        return False
    names_drawn = dctx.get("names_drawn", [])
    chances_drawn = dctx.get("chances_drawn", [])
    colors_drawn = dctx.get("colors_drawn", [])
    winner_idx_saved = dctx.get("winner_idx_drawn", None)
    final_angle = dctx.get("final_angle", None)
    if winner_idx_saved is None or winner_idx_saved >= len(names_drawn) or final_angle is None:
        return False
    now_names = [t["name"] for t in teilnehmer_now if t.get("chance",0) > 0 and isinstance(t.get("name",""),str) and t.get("name","").strip()!=""]
    now_chances = [t["chance"] for t in teilnehmer_now if t.get("chance",0) > 0 and isinstance(t.get("name",""),str) and t.get("name","").strip()!=""]
    if len(now_names) != len(names_drawn):
        return False
    for i in range(len(now_names)):
        if now_names[i] != names_drawn[i]:
            return False
        try:
            if float(now_chances[i]) != float(chances_drawn[i]):
                return False
        except:
            return False
    if len(names_drawn) == 0 or len(chances_drawn) == 0:
        return False
    if not all(isinstance(n, str) and n.strip() for n in names_drawn):
        return False
    if any(float(c) < 0 or float(c) > 100 for c in chances_drawn):
        return False
    if not any(float(c) > 0 for c in chances_drawn):
        return False
    # Hier: Prüfe, dass mit dem gespeicherten final_angle auch der "richtige" Gewinnerindex gezogen ist!
    winner_idx_final = find_winner_by_pointer(names_drawn, chances_drawn, final_angle)
    if winner_idx_final is None or winner_idx_final != winner_idx_saved:
        return False
    return True

def show_user_view():
    if st.session_state.get("admin_timeout_banner", False):
        st.markdown("<div class='navy-warning' style='font-size:1.25em;margin-bottom:1.2em;background:#b92337;color:#ffeedd;font-weight:900;'>Deine Admin-Session ist abgelaufen. Bitte erneut einloggen, falls du wieder Einstellungen ändern willst.</div>", unsafe_allow_html=True)
        st.session_state.admin_timeout_banner = False

    if st.session_state.get("user_mode_locked", False):
        st.info("Die Ansicht wurde auf User-Modus gesperrt, nachdem ein Admin-Login stattgefunden hat. Um wieder zu wechseln, bitte die App neu laden.", icon="🔒")
        return

    st.markdown(f"<h1>Lotterie Laufchallenge Woche {st.session_state.week_nr}</h1>", unsafe_allow_html=True)

    # with st.expander("🖍️ Schriftgröße anpassen", expanded=False):
    #     fs = st.radio(
    #         "Schriftgröße wählen",
    #         ["Klein","Normal","Groß"],
    #         index=["Klein","Normal","Groß"].index(st.session_state.font_size),
    #         key="fontsize_selector_user",
    #         disabled=st.session_state.drawing
    #     )
    #     st.session_state.font_size = fs
    #     st.markdown(f"<style>{set_fontsize_class()}</style>", unsafe_allow_html=True)

    # st.markdown("<div class='admin_hint'>Admins: <b>Hier geht's zum Login!</b></div>", unsafe_allow_html=True)
    # col_btns = st.columns([1,1,1])
    # with col_btns[1]:
    #     admin_hint_btn_clicked = st.button("🔐 Zum Admin-Login", key="goto_admin_user_prominent")
    #     if admin_hint_btn_clicked:
    #         st.session_state.view = "login"
    #         st.experimental_rerun()
    st.markdown("<br>", unsafe_allow_html=True)

    if len(st.session_state.teilnehmer) >= 30:
        st.info("⚠️ Hinweis: Bei vielen Teilnehmern werden Namen zur Übersichtlichkeit nur unter dem Rad in der Legende angezeigt. Die Zuordnung ist immer eindeutig über Symbol & Farbe. Die Legende ist ggf. auf Mobilgeräten horizontal scrollbar.", icon="ℹ️")
        st.markdown(
            "<div class='navy-warning' style='font-size:1.12em;background: #ffde66;color:#0a2240;'>"
            "🔔 <b>Wichtiger Hinweis:</b> Um den Gewinner eindeutig zu erkennen: "
            "Der Gewinner ist immer <b>exakt der Name, auf den der weiße Pfeil nach der Ziehung zeigt!</b> "
            "Die Zuordnung erfolgt farblich und mit Symbol in der Legende rechts unter dem Rad. "
            "Falls du die Legende nicht komplett siehst: Bitte horizontal scrollen (z.B. mit Wischgeste oder Scrollrad)."
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div style='background:#18366ed7;border-radius:7px;margin-bottom:.7em;padding:.6em 1.1em;font-size:1.1em;color:#fff;'>🌐 Tipp: Auf mobilen Geräten oder bei vielen Teilnehmern kann die Legende <b>horizontal gescrollt</b> werden!</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"""
    <div style='margin-bottom:0.8em;color:{WHITE}'>
    Willkommen zur <b>Laufchallenge-Lotterie</b> der Woche {st.session_state.week_nr}!<br>
    Jede Woche wird unter den Teilnehmern entsprechend ihrer Gewinnwahrscheinlichkeit per Zufall ein Gewinner gezogen.<br>

    <br><br>
    </div>
    """, unsafe_allow_html=True)

    teilnehmer_safe = st.session_state.teilnehmer
    week_nr_safe = st.session_state.week_nr
    valid_teilnehmer = [t for t in teilnehmer_safe if t.get("chance",0) > 0 and isinstance(t.get("name",""),str) and t.get("name","").strip()!=""]

    drawn_context = get_draw_context_from_session()

    if st.session_state.draw_state == "post_draw":
        if not winner_context_still_valid(drawn_context, teilnehmer_safe):
            clear_draw_context()
            st.markdown(
                "<div class='navy-warning' style='font-size:1.25em;margin-bottom:1.2em;'>⚠️ Die Teilnehmerliste wurde nach der letzten Ziehung verändert. Das vergangene Ziehungsergebnis kann <b>aus Sicherheits- und Fairnessgründen nicht mehr erneut angezeigt</b> werden. Führe eine neue Ziehung durch!</div>",
                unsafe_allow_html=True
            )
            drawn_context = None



    wheel_placeholder = st.empty()
    valid_teilnehmer = [t for t in st.session_state.teilnehmer if t.get("chance",0) > 0 and isinstance(t.get("name",""),str) and t.get("name","").strip()!=""]

    if not valid_teilnehmer:
        wheel_placeholder.info("Keine gültigen Teilnehmer vorhanden. Ziehung nicht möglich.", icon="🚫")
        return

    names = [t["name"] for t in valid_teilnehmer]
    chances = [t["chance"] for t in valid_teilnehmer]
    colors = name_colors(len(names))

    show_draw_svg = None
    winner_idx_for_svg = None
    winner_rotation = None
    winner_line_angle = None
    use_symbols_for_svg = len(names) >= 30

    if not (drawn_context and winner_context_still_valid(drawn_context, st.session_state.teilnehmer)):
        wheel_placeholder.markdown(
            get_wheel_svg_html(
                names, chances, colors, rotation=0, winner_idx=None, use_symbols_param=use_symbols_for_svg
            ),
            unsafe_allow_html=True
        )
    winner_placeholder = st.empty()
    drawn_context = get_draw_context_from_session()
    if drawn_context and winner_context_still_valid(drawn_context, st.session_state.teilnehmer):
        wheel_placeholder.markdown(
            get_wheel_svg_html(
                drawn_context["names_drawn"],
                drawn_context["chances_drawn"],
                drawn_context["colors_drawn"],
                rotation=drawn_context["final_angle"],
                winner_idx=drawn_context["winner_idx_drawn"],
                use_symbols_param=drawn_context["use_symbols_drawn"],
                force_highlight_idx=drawn_context["winner_idx_drawn"],
                draw_winner_line=False
            ),
            unsafe_allow_html=True
        )
        show_winner_panel_from_context(drawn_context)
        winner_idx=drawn_context["winner_idx_drawn"]
        winner = names[winner_idx]
        # Gewinnertext unter dem Rad
        winner_placeholder.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #4a69bd 0%, #6c5ce7 100%);
                color: #fff;
                font-size: 1.5em;
                font-weight: 700;
                padding: 0.8em 1.6em;
                border-radius: 16px;
                text-align: center;
                box-shadow: 0 0 15px #4a69bd66, 0 0 30px #6c5ce733;
                text-shadow: 1px 1px 4px #222;
                margin: 1em auto;
                max-width: 500px;
            ">
                🎉🏆 <span style='color:#f1f1f1;'>Der Gewinner ist: {winner}</span> 🏆🎉
            </div>
            """,
            unsafe_allow_html=True
        )



    # st.markdown(
    #     "<div style='margin-top:.5em;color:#ffd700;font-weight:700;font-size:1.13em;font-family:sans-serif;'>Der Gewinner ist immer exakt <u>der Name, auf den nach der Ziehung der weiße Pfeil zeigt.</u></div>",
    #     unsafe_allow_html=True
    # )
    #elif st.session_state.draw_state == "post_draw" and winner_context_still_valid(drawn_context, valid_teilnehmer):
        #test=1
        # dnames = drawn_context["names_drawn"]
        # dchances = drawn_context["chances_drawn"]
        # dcolors = drawn_context["colors_drawn"]
        # #final_angle = drawn_context.get("final_angle", 0)
        # duse_symbols = drawn_context.get("use_symbols_drawn", False)
        # winner_idx_for_svg = drawn_context["winner_idx_drawn"]
        # # Der Drehwinkel zur Anzeige = exakte Rotation, so dass Gewinner auf 12 Uhr steht!
        # winner_rotation = exact_rotation_for_winner(dnames, dchances, winner_idx_for_svg)-90
        # total = sum(dchances)
        # angle_start = 0
        # for idx, c in enumerate(dchances):
        #     angle_span = 360 * c / total if total > 0 else 0
        #     a0 = angle_start
        #     a1 = angle_start + angle_span
        #     if idx == winner_idx_for_svg:
        #         winner_line_angle = (a0 + a1) / 2
        #         break
        #     angle_start = a1

        # wheel_placeholder.markdown(
        #     get_wheel_svg_html(
        #         dnames,
        #         dchances,
        #         dcolors,
        #         rotation=winner_rotation,
        #         winner_idx=winner_idx_for_svg,
        #         use_symbols_param=duse_symbols,
        #         force_highlight_idx=winner_idx_for_svg,
        #         draw_winner_line=False,
        #         winner_line_angle=winner_line_angle
        #     ),
        #     unsafe_allow_html=True
        # )
        # st.markdown(
        #     "<div style='margin-top:.5em;color:#ffd700;font-weight:700;font-size:1.13em;font-family:sans-serif;'>🎯 Der Gewinner ist <b>genau der Name am weißen Pfeil (12 Uhr Richtung)!</b> Das Gewinnerfeld und die Zuordnung mit Symbol ist unten gelb markiert. Die goldene Linie markiert das Gewinnersegment und den Namen in der Legende.</div>",
        #     unsafe_allow_html=True
        # )
        # st.markdown(
        #     f"<div style='margin-top:0.77em;margin-bottom:1em;background:#18366ed7;padding:0.7em 1.1em;font-size:1.09em;color:#fff;border-radius:0.7em;'>"
        #     "🔎 Hinweis: Bei sehr vielen Teilnehmern/kleinen Segmenten bitte auf die <b>Pfeilmarkierung und gelbes Gewinnerfeld</b> achten.<br>Wer auf das Segment gezeigt wird, ist immer <b>entscheidend</b> – siehe auch Legende unten!"
        #     "</div>", unsafe_allow_html=True
        # )

    if st.session_state.draw_state == "post_draw" and drawn_context is not None and winner_context_still_valid(drawn_context, valid_teilnehmer):
        test=1
        #fixed_ctx = drawn_context.copy()
        #fixed_ctx["winner_idx_drawn"] = find_winner_by_pointer(
        #    drawn_context["names_drawn"],
        #    drawn_context["chances_drawn"],
        #    drawn_context.get("final_angle", 0)
        #)
        #show_winner_panel_from_context(fixed_ctx, show_consistency_hint=True)


    if st.session_state.draw_state == "pre_draw" or drawn_context is None:
        valid_teilnehmer_for_draw = [t for t in valid_teilnehmer if t.get("chance", 0) > 0 and isinstance(t.get("name",""),str) and t.get("name","").strip()!=""]
        if st.button("Ziehung starten"):
            if not valid_teilnehmer_for_draw:
                st.error("Die Ziehung kann nicht gestartet werden, da keine gültigen Teilnehmenden vorhanden sind.", icon="🚫")
                return
            clear_draw_context()
            st.session_state.draw_state = "drawing"
            show_wheel_animation(valid_teilnehmer_for_draw, wheel_placeholder)
            st.session_state.draw_state = "post_draw"
            st.experimental_rerun()
            
    st.subheader("Teilnehmer & Gewinnwahrscheinlichkeiten:")
    valid_teilnehmer = [t for t in st.session_state.teilnehmer if t.get("chance",0) > 0 and isinstance(t.get("name",""),str) and t.get("name","").strip()!=""]


    table_data = {
        "Teilnehmer": [t["name"] for t in valid_teilnehmer],
        "Gewinnwahrscheinlichkeit": [t["chance"] for t in valid_teilnehmer]
    }
    df = pd.DataFrame(table_data)
    df["Gewinnwahrscheinlichkeit"] = df["Gewinnwahrscheinlichkeit"].apply(
        lambda x: f"{x:.1f}" if x > 0 else "-"
    )
    st.dataframe(df.style.set_properties(**{
            "background-color": "#000000",
            "color": "white",
            "border-color": "#333",
            "text-align": "center"
        }).set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#011848"),
                ("color", "white"),
                ("font-weight", "bold"),
                ("text-align", "center")
            ]}
        ]), use_container_width=True, hide_index=True)
    
    cols = st.columns([1,1,1])
    with cols[0]:
        if not st.session_state.get("admin_pw_entered", False) and not st.session_state.get("user_mode_locked", False):
            if st.button("🔧 Zum Admin-Login", key="goto_admin_user", help="Logge dich hier als Admin ein."):
                st.session_state.view = "login"
                st.experimental_rerun()
    with cols[1]:
        pass
    with cols[2]:
        if st.session_state.get("admin_pw_entered", False):
            if st.button("Abmelden (Admin)", key="logout_btn_user"):
                st.session_state.view = "user"
                st.session_state.admin_pw_entered = False
                st.session_state.admin_last_active = None
                st.session_state.user_mode_locked = True
                st.experimental_rerun()

def _set_view_to_login():
    st.session_state.view = "login"
    st.experimental_rerun()

def admin_login():
    st.subheader("🔒 Admin-Login")
    pw = st.text_input("Passwort", type="password", key="pwinput")
    cols = st.columns([1,1])
    with cols[0]:
        if st.button("Login", key="login_btn"):
            if pw == st.session_state.admin_password:
                st.session_state.admin_pw_entered = True
                st.session_state.admin_last_active = time_sleep.time()
                st.session_state.view = "admin"
                st.session_state.error_field = None
                st.session_state.user_mode_locked = True
                st.success("Admin-Login erfolgreich. Nach dem Login kann nur durch einen manuellen Reload wieder zwischen User-/Admin-Rolle gewechselt werden!", icon="🔒")
                st.experimental_rerun()
            else:
                st.error("Falsches Passwort!")
    with cols[1]:
        if st.button("Zurück zur User-Ansicht", key="login_cancel"):
            st.session_state.view = "user"
            st.session_state.admin_pw_entered = False
            st.session_state.admin_last_active = None
            st.session_state.user_mode_locked = False

def show_admin_view():
    session_ok = check_admin_session()
    if not session_ok:
        st.stop()

    if "admin_timeout_banner" in st.session_state and st.session_state.admin_timeout_banner:
        st.markdown("<div class='navy-warning' style='font-size:1.25em;background:#b92337;color:#ffeedd;font-weight:900;'>Deine Admin-Session ist abgelaufen. Bitte erneut einloggen, falls du wieder Einstellungen ändern möchtest.</div>", unsafe_allow_html=True)
        st.session_state.admin_timeout_banner = False

    info_list = []
    if len(st.session_state.teilnehmer) > 17:
        info_list.append("ℹ️ Tipp: Bei vielen Teilnehmenden kannst du über das Seitenmenü oder die Browser-Suchfunktion (Strg+F) schneller nach Namen suchen oder die Ansicht filtern.")
    if len(st.session_state.teilnehmer) >= 30:
        info_list.append("⚠️ Info: Bei vielen Teilnehmern werden Namen am Rad nicht angezeigt, sondern nur in der scrollbaren Legende unter dem Rad. Die Zuordnung bleibt immer eindeutig über Farben und Symbole.")

    if st.session_state.drawing:
        info_list.append("⚠️ Es läuft gerade eine Ziehung oder das Rad wird animiert. Speichern, Löschen oder Bearbeiten ist währenddessen aus Sicherheitsgründen gesperrt.")
    if len(info_list) > 0:
        st.info(" ".join(info_list), icon="ℹ️")

    week_tag = f"<div style='font-size:2em;color:{WHITE};font-weight:700;margin-bottom:-0.2em;margin-top:0.2em;'>Woche {st.session_state.week_nr}</div>"
    st.markdown(week_tag, unsafe_allow_html=True)
    st.markdown(f"<h1 style='margin-bottom:0.2em;'>Verwaltung – Lotterie Laufchallenge</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='margin-bottom:0.8em;color:{WHITE}'>"
        "<b>Teilnehmende und Los-Wert (Gewichtung) verwalten</b><br>"
        "Jede:r Teilnehmer:in erhält je nach Laufleistung einen eigenen Los-Wert (sein Gewicht/Einsatz). "
        "<ul style='margin-bottom:0;margin-top:0.6em;'><li>Ein höherer Wert bedeutet eine größere Gewinnchance. "
        "Die Werte sind z.B. <b>1</b>, <b>2.5</b>, <b>10</b> – sie müssen <b>keine Prozentzahlen sein</b>. "
        "Die 'Wahrscheinlichkeit = eigener Wert geteilt durch Summe aller Werte'</li></ul>"
        "Namen dürfen nur lateinische Buchstaben (a-z, A-Z), Zahlen (0-9), Leerzeichen, deutsche Umlaute, sowie Bindestrich enthalten, "
        "keine ausschließlich Whitespaces."
        "<br><span style='color:#ffd700;font-weight:700;font-size:1.05em;'>Gewinner ist immer <b>der Name, auf den der weiße Pfeil zeigt!</b></span>"
        "</div>",
        unsafe_allow_html=True
    )

    st.info("💡 Um zur Ziehung zurück zu wechseln (Ansicht wie für normale Nutzer:innen), klicke auf „Zurück zur User-Ansicht” unten. Dort kannst du die Gewinnerziehung starten!", icon="ℹ️")

    with st.expander("🖍️ Schriftgröße anpassen"):
        fs = st.radio(
            "Schriftgröße wählen",
            ["Klein","Normal","Groß"],
            index=["Klein","Normal","Groß"].index(st.session_state.font_size),
            key="fontsize_selector_admin",
            disabled=st.session_state.drawing
        )
        st.session_state.font_size = fs
        st.markdown(f"<style>{set_fontsize_class()}</style>", unsafe_allow_html=True)

    teilnehmer = st.session_state.teilnehmer
    del_idx = None
    remove_err = None
    validation_states = []
    dupes = get_duplicate_name_index_list(teilnehmer)
    st.subheader("Teilnehmende verwalten")
    MAX_TEILNEHMER = 32
    focus_index = None

    drawn_context = get_draw_context_from_session()
    if drawn_context is not None:
        if not winner_context_still_valid(drawn_context, teilnehmer):
            clear_draw_context()
            st.info("⚠️ Hinweis: Nach Bearbeitung der Liste ist das vergangene Ziehungsergebnis aus Fairnessgründen nicht mehr abrufbar. Bitte führe eine neue Ziehung im User-Bereich durch.", icon="ℹ️")

    confirm_delete = {}
    min_participants_reached = (len(teilnehmer) <= 1)
    last_idx = None
    to_disable_delete = (len(teilnehmer) <= 1)
    for idx, t in enumerate(teilnehmer):
        cols = st.columns([3, 2, 1])
        key_name = f"name_{idx}"
        key_chance = f"chance_{idx}"
        key_remove = f"remove_{idx}"
        key_confirm = f"confirm_{idx}"

        with cols[0]:
            name = st.text_input(
                f"Name {idx+1}",
                value=t.get("name",""),
                key=key_name,
                max_chars=32,
                help="Nur Buchstaben, Ziffern, Leerzeichen, deutsche Umlaute (äöüÄÖÜß) und Bindestrich erlaubt (max. 32 Zeichen).",
                autocomplete="off",
                disabled=st.session_state.drawing,
                label_visibility="visible"
            )
        with cols[1]:
            try:
                pre_val = float(t.get("chance",1))
            except:
                pre_val = 1
            chance = st.number_input(
                f"Loswert für {name.strip() or 'Teilnehmer'}",
                min_value=0.0, max_value=100.0, value=pre_val,
                step=0.1,
                help="Wert für die Ziehung/Gewichtung. Je höher, desto wahrscheinlicher der Gewinn. Kein Prozent!",
                disabled=st.session_state.drawing
            )
        with cols[2]:
            btn_help = None
            if st.session_state.drawing:
                btn_help = "Bearbeiten und Entfernen ist während einer laufenden Ziehung aus Sicherheitsgründen gesperrt."
            elif len(teilnehmer) <= 1:
                btn_help = "Mindestens ein Teilnehmer muss verbleiben."
            if st.session_state.get(f"confirm_{idx}"):
                btn_disabled = (len(teilnehmer) <= 1 or st.session_state.drawing)
                st.button("Wirklich löschen?", key=f"really_remove_{idx}", disabled=btn_disabled, help=btn_help)
                if not btn_disabled:
                    if st.session_state[f"really_remove_{idx}"]:
                        del_idx = idx
                        st.session_state[f"confirm_{idx}"] = False
            else:
                btn_disabled = (len(teilnehmer) <= 1 or st.session_state.drawing)
                st.button(
                    "Entfernen",
                    key=key_remove,
                    disabled=btn_disabled,
                    help=btn_help
                )
                if not btn_disabled:
                    if st.session_state[key_remove]:
                        st.session_state[f"confirm_{idx}"] = True

        validated = validate_name(name)
        t["name"] = name
        t["chance"] = chance
        validation_states.append(validated)
        if chance == 0:
            cols[1].info(
                "Loswert 0: Dieser Teilnehmer kann aktuell NICHT gewinnen und wird bei der Ziehung ausgeblendet.",
                icon="🚫"
            )
        if not validated or idx in dupes:
            field_problem = True
            msg = ""
            if idx in dupes:
                msg += f"Nicht eindeutig oder leer! "
            if not validated:
                msg += "Ungültiger Name (nur Buchstaben, Ziffern, Umlaute, Bindestrich, Leerzeichen, max. 32 Zeichen)!"
            if field_problem:
                cols[0].warning(msg.strip())
        if chance < 0 or chance > 100:
            cols[1].warning("Lose müssen zwischen 0 und 100 liegen!")
    if del_idx is not None and len(teilnehmer) > 1:
        teilnehmer.pop(del_idx)
        if check_unique_names(st.session_state.teilnehmer) and all(validate_name(t["name"]) for t in st.session_state.teilnehmer):
            save_persistent_data(st.session_state.teilnehmer, st.session_state.week_nr)
            st.success("Teilnehmer:in entfernt.", icon="✅")
        else:
            st.warning("Daten konnten nicht gespeichert werden. Korrigiere Fehler bei Namen/Duplikaten.", icon="⚠️")
        clear_draw_context()
        for i in range(len(teilnehmer)+1):
            if f"confirm_{i}" in st.session_state:
                del st.session_state[f"confirm_{i}"]
        st.experimental_rerun()
    elif not remove_err is None:
        st.warning(remove_err)

    if st.session_state.add_participant_error:
        st.warning(st.session_state.add_participant_error)
        st.session_state.add_participant_error = None

    add_disabled = len(teilnehmer) >= MAX_TEILNEHMER or st.session_state.drawing
    add_button = st.button(
        "Teilnehmer:in hinzufügen",
        key="add_participant",
        disabled=add_disabled,
        help="Maximal 32 Teilnehmende erlaubt." if len(teilnehmer) >= MAX_TEILNEHMER else ("Bearbeiten/Neu hinzufügen während Ziehung gesperrt." if st.session_state.drawing else None)
    )
    if add_button and not add_disabled:
        if len(teilnehmer) >= MAX_TEILNEHMER:
            st.session_state.add_participant_error = f"Limit erreicht! Maximal {MAX_TEILNEHMER} Teilnehmende erlaubt."
        else:
            defaultname = f"Teilnehmer{len(teilnehmer)+1}"
            n = 1
            proposed_name = defaultname
            existing_names = [t.get("name","") for t in teilnehmer]
            while proposed_name in existing_names:
                n += 1
                proposed_name = f"{defaultname}_{n}"
            teilnehmer.append({"name": proposed_name, "chance": 1})
            st.session_state.last_added_idx = len(teilnehmer)-1
            if check_unique_names(st.session_state.teilnehmer) and all(validate_name(t["name"]) for t in st.session_state.teilnehmer):
                save_persistent_data(st.session_state.teilnehmer, st.session_state.week_nr)
                st.success("Teilnehmer:in hinzugefügt.", icon="✅")
            else:
                st.warning("Teilnehmer konnte nicht gespeichert werden. Bitte korrigiere Namens- oder Duplikatsfehler.", icon="⚠️")
            clear_draw_context()
            st.experimental_rerun()

    all_ok = True
    if len(dupes):
        all_ok = False
        dnames = [teilnehmer[i].get("name","") for i in dupes if teilnehmer[i].get("name","") == "" or teilnehmer[i].get("name","").strip() == ""]
        ddnames = [teilnehmer[i].get("name","") for i in dupes if teilnehmer[i].get("name","").strip() != ""]
        if dnames:
            st.warning("Es gibt mindestens ein leeres Namensfeld.")
        if ddnames:
            nm = ",".join([f"'{n}'" for n in ddnames])
            st.warning(f"Nicht eindeutiger Name: {nm} – bitte korrigieren!")
    elif not all(validation_states):
        all_ok = False
        st.warning("Einige Namen sind ungültig (nur Buchstaben, Ziffern, Bindestrich, Leerzeichen, deutsche Umlaute, max. 32 Zeichen)!")

    if all_ok and all(validation_states):
        save_persistent_data(st.session_state.teilnehmer, st.session_state.week_nr)

    if len(st.session_state.teilnehmer) == 0:
        st.warning(
            "Aktuell sind keine Teilnehmer mehr eingetragen. "
            "Füge mindestens eine(n) neue(n) Teilnehmer:in hinzu, um die Lotterie wieder zu aktivieren. "
            "Die Standard-Teilnehmerliste kann ggf. manuell im System (Datei) wiederhergestellt werden.",
            icon="⚠️"
        )

    st.markdown("<div class='trennlinie'></div>", unsafe_allow_html=True)
    st.subheader("Weitere Einstellungen")
    new_week = st.number_input(
        "Aktuelle Woche einstellen",
        min_value=1, max_value=52, value=int(st.session_state.week_nr),
        key="week_nr_admin",
        help="Die gewählte Woche wird als Überschrift in der User-Ansicht angezeigt."
    )
    if new_week != st.session_state.week_nr:
        st.session_state.week_nr = new_week
        if check_unique_names(st.session_state.teilnehmer) and all(validate_name(t["name"]) for t in st.session_state.teilnehmer):
            save_persistent_data(st.session_state.teilnehmer, st.session_state.week_nr)
            st.success("Woche geändert!", icon="✅")
        else:
            st.warning("Woche konnte nicht gespeichert werden wegen Namens/Duplikatsfehlern. Bitte korrigiere diese zuerst.")
        clear_draw_context()
        st.experimental_rerun()
    st.markdown("<div class='trennlinie'></div>", unsafe_allow_html=True)

    bcols = st.columns([1,1,1])
    with bcols[0]:
        if st.button("Zurück zur User-Ansicht", key="admin2user", disabled=st.session_state.drawing):
            st.session_state.view = 'user'
            st.session_state.admin_pw_entered = False
            st.session_state.admin_last_active = None
            st.session_state.user_mode_locked = True
            st.experimental_rerun()
    with bcols[1]:
        if st.button("Abmelden (Admin)", key="logout_btn", disabled=st.session_state.drawing):
            st.session_state.view = "user"
            st.session_state.admin_pw_entered = False
            st.session_state.admin_last_active = None
            st.session_state.user_mode_locked = True
            st.experimental_rerun()
    with bcols[2]:
        change_pw = st.button("Admin-Passwort ändern", key="pwchange_btn", disabled=st.session_state.drawing)
        if change_pw:
            st.session_state.view = "changepw"
            st.experimental_rerun()

def show_pwchange_view():
    st.subheader("Admin-Passwort ändern")
    old_pw = st.text_input("Altes Passwort", type="password", key="pw_old")
    new_pw = st.text_input("Neues Passwort", type="password", key="pw_new")
    new_pw2 = st.text_input("Neues Passwort wiederholen", type="password", key="pw_new2")
    change_clicked = st.button("Passwort ändern", key="do_change_pw")
    cancel_clicked = st.button("Abbrechen", key="pwchange_cancel")
    if change_clicked:
        if old_pw != st.session_state.admin_password:
            st.error("Das alte Passwort ist falsch.")
        elif not (1 <= len(new_pw) <= 64):
            st.error("Neues Passwort muss 1-64 Zeichen haben.")
        elif new_pw != new_pw2:
            st.error("Die beiden neuen Passwörter stimmen nicht überein.")
        else:
            st.session_state.admin_password = new_pw
            save_admin_password(new_pw)
            st.success("Passwort geändert.", icon="✅")
            st.session_state.view = "admin"
            st.experimental_rerun()
    elif cancel_clicked:
        st.session_state.view = "admin"
        st.experimental_rerun()

def is_admin():
    return bool(st.session_state.get("admin_pw_entered", False))

def _main_dispatcher():
    v = st.session_state.view
    admin_pw = st.session_state.get("admin_pw_entered", False)
    if v == "login":
        st.session_state.admin_pw_entered = False
        admin_login()
    elif v == "changepw" and admin_pw:
        show_pwchange_view()
    elif v == "admin" and admin_pw:
        session_ok = check_admin_session()
        if session_ok:
            show_admin_view()
    elif v == "user":
        show_user_view()
    else:
        st.session_state.view = "user"
        st.session_state.error_field = None
        show_user_view()

_main_dispatcher()

if not st.session_state.get("admin_pw_entered", False):
    st.session_state.admin_last_active = None
    st.session_state.error_field = None
