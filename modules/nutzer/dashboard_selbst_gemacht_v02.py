#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 29 16:46:48 2025

@author: sebastianschuch
"""

    

def show_dashboard():


    
    import streamlit as st
    import pandas as pd
    from datetime import datetime, timedelta, time
    import html
    import streamlit.components.v1 as components
    import textwrap
    from streamlit_autorefresh import st_autorefresh 
    import time as time_sleep
    import json
    import os
    import re
    
    
    # Session-State für einmaligen Hinweis



    # st.markdown("""
    # <style>
    # /* Nachricht nur auf Bildschirmen <= 768px anzeigen */
    # @media (min-width: 769px) {
    #     .mobile-only {
    #         display: none !important;
    #     }
    # }
    # </style>
    # """, unsafe_allow_html=True)
    
    # # Session-State für mobile Hinweis initialisieren
    # if "mobile_notice_start" not in st.session_state:
    #     st.session_state["mobile_notice_start"] = datetime.now()
    
    # # 7 Sekunden Dauer definieren
    # notice_duration = timedelta(seconds=7)
    
    # # Nachricht anzeigen, wenn Zeit noch nicht abgelaufen
    # if datetime.now() - st.session_state["mobile_notice_start"] < notice_duration:
    #     st.markdown("""
    #     <div class="mobile-only" style="padding: 10px; border-radius: 8px; background-color: #ffe066; color: #011848; font-weight: 600; text-align:center; margin-bottom: 12px;">
    #         ⚠️ Bei Nutzung übers Smartphone kann es hilfreich sein, den Bildschirm für eine bessere Darstellung zu drehen.
    #     </div>
    #     """, unsafe_allow_html=True)
    
    #     # Autorefresh alle 1 Sekunde, damit die Nachricht verschwindet
    #     from streamlit_autorefresh import st_autorefresh
    #     st_autorefresh(interval=1000, limit=8, key="mobile_notice_refresh")  # refresh bis max. 8x
    
    # Session-State für mobile Hinweis initialisieren
    if "mobile_notice_start" not in st.session_state:
        st.session_state["mobile_notice_start"] = datetime.now()
    
    # 7 Sekunden Dauer definieren
    notice_duration = timedelta(seconds=7)
    
    # Nachricht anzeigen, wenn Zeit noch nicht abgelaufen
    if datetime.now() - st.session_state["mobile_notice_start"] < notice_duration:
        st.markdown('<div class="mobile-only">', unsafe_allow_html=True)
        st.warning("⚠️ Bei Smartphone-Nutzung kann es hilfreich sein den Bildschirm für eine bessere Darstellung zu drehen.")
        st.markdown('</div>', unsafe_allow_html=True)
    
        # Autorefresh alle 1 Sekunde, damit die Nachricht verschwindet
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=1000, limit=8, key="mobile_notice_refresh")





        
    GESAMT_WOCHEN = 5  # oder später aus Session/Admin konfigurierbar
    
    COMMON_TILE_HEIGHT = 230  # Höhe aller Kacheln
    COMMON_BAR_HEIGHT = 26    # Höhe der Fortschrittsbalken
    COMMON_BAR_BORDER = 2      # Rahmenstärke der Balken
    COMMON_TILE_HEIGHT = 180  # Höhe der Kachel
    
        # ---------- ADMIN-KONFIGURATION ----------
        # jeweils nur in KLEINBUCHSTABEN unabhängig vom eigentlichen Nutzernamen. 
    ADMIN_USERS = {
        "sebastian",
        "tobi",
        "sergej"
    }
 
     
    SETTINGS_FILE = "settings.json"
    
    def load_settings():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_settings(settings):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    
    user = st.session_state.get("user")
    all_users = st.session_state.get("active_users_this_week", [])
    
    runs_by_user = st.session_state.get("runs_by_user", {})
    WOCHENZIEL = st.session_state.get("WOCHENZIEL",5000)
    WOCHENNUMMER = st.session_state.get("WOCHENNUMMER",1)
    RUNS_FILE = "data/runs_by_user.json"


    def normalize_name(name):
        import unicodedata
        name = unicodedata.normalize("NFKC", name.strip().lower())
        name = ''.join(name.split())
        name = ''.join(c for c in name if c.isalnum())
        return name

    def load_runs():
        if not os.path.exists(RUNS_FILE):
            return {}
    
        try:
            with open(RUNS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                raw = json.loads(content)
                if isinstance(raw, dict):
                    # Konvertiere ggf. Strings zu datetime, falls du das brauchst
                    for user, runs in raw.items():
                        for run in runs:
                            if "time" in run and isinstance(run["time"], str):
                                from datetime import datetime
                                run["time"] = datetime.fromisoformat(run["time"])
                    return raw
                else:
                    return {}
        except json.JSONDecodeError:
            return {}
        except Exception as e:
            st.error(f"Ladefehler für Läufe: {e}")
            return {}

    
        def parse_time(t):
            """
            Konvertiert alte Python-datetime Strings oder ISO-Strings in datetime-Objekte
            """
            from datetime import datetime
            import re
        
            if isinstance(t, datetime):
                return t
        
            if isinstance(t, str):
                # Alte Form: datetime.datetime(2025, 12, 30, 18, 31, 26, 266647)
                m = re.match(
                    r"datetime\.datetime\(\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\)",
                    t
                )
                if m:
                    y, mo, d, h, mi, s, us = map(int, m.groups())
                    return datetime(y, mo, d, h, mi, s, us)
                else:
                    # ISO-Format versuchen
                    try:
                        return datetime.fromisoformat(t)
                    except Exception:
                        pass
        
            # Fallback: aktuelles Datum
            return datetime.now()

    
        normalized = {}
        for user, runs in raw.items():
            norm_user = normalize_name(user)
            normalized[norm_user] = []
            for r in runs:
                r_copy = r.copy()
                r_copy["time"] = parse_time(r.get("time"))
                normalized[norm_user].append(r_copy)
    
        return normalized




    
    def robust_init_state(key, default):
        if key not in st.session_state:
            st.session_state[key] = default
    
    # Initialisierung
    robust_init_state("user", None)
    robust_init_state("user_name", "")
    robust_init_state("all_usernames", [])
    if "runs_by_user" not in st.session_state:
        st.session_state["runs_by_user"] = load_runs()
    robust_init_state("WOCHENNUMMER", 1)
    robust_init_state("WOCHENZIEL", 5000)
    robust_init_state("BATTERIE_SCHWELLE", 50)
    robust_init_state("admin_info_text", "")
    robust_init_state("admin_erklaer_text", "")
    robust_init_state("CHALLENGE_END_DATETIME", datetime.now() + timedelta(days=7))
    if "TEAMZIEL_WOCHEN_ERREICHT" not in st.session_state:
        st.session_state["TEAMZIEL_WOCHEN_ERREICHT"] = 0
    # Liste aller angemeldeten Nutzer, die für die aktuelle Woche aktiv sind
    if "active_users_this_week" not in st.session_state:
        st.session_state["active_users_this_week"] = list(st.session_state.get("all_usernames", []))


    # Session-State mit gespeicherten Settings füllen
    stored = load_settings()
    st.session_state["WOCHENNUMMER"] = stored.get("WOCHENNUMMER", 1)
    st.session_state["WOCHENZIEL"] = stored.get("WOCHENZIEL", 5000)
    st.session_state["BATTERIE_SCHWELLE"] = stored.get("BATTERIE_SCHWELLE", 50)
    st.session_state["CHALLENGE_START_DATETIME"] = stored.get("CHALLENGE_START_DATETIME", datetime.now())
    st.session_state["CHALLENGE_END_DATETIME"] = stored.get("CHALLENGE_END_DATETIME", datetime.now())
    st.session_state["TEAMZIEL_WOCHEN_ERREICHT"] = stored.get("TEAMZIEL_WOCHEN_ERREICHT", 0)
    st.session_state["admin_info_text"] = stored.get("admin_info_text", "")
    st.session_state["admin_erklaer_text"] = stored.get("admin_erklaer_text", "")
    st.session_state["active_users_this_week"] = stored.get("active_users_this_week", [])
    st.session_state["lotterie_preise"] = stored.get("lotterie_preise", [
        {"icon": "🎁", "text": "Tolles Buchpaket"},
        {"icon": "🎁", "text": "Café-Gutschein"},
        {"icon": "🎁", "text": "Cooles Gadget"},
    ])
    if "runs_expander_open" not in st.session_state:
        st.session_state["runs_expander_open"] = False
    
    # Laden
    # CHALLENGE_START_DATETIME
    start = st.session_state.get("CHALLENGE_START_DATETIME")
    if start and isinstance(start, str):
        st.session_state["CHALLENGE_START_DATETIME"] = datetime.fromisoformat(start)
    
    # CHALLENGE_END_DATETIME
    ende = st.session_state.get("CHALLENGE_END_DATETIME")
    if ende and isinstance(ende, str):
        st.session_state["CHALLENGE_END_DATETIME"] = datetime.fromisoformat(ende)
    
    st.markdown(
        """
        <style>
        html, body, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] { background:#011848 !important; color:#fff;}
        .page-wrap-custom { max-width:98vw; margin:0 auto; background:none;}
        /* Kachel-Farben */
        .tile-blue-1 { background:#173985 !important; }
        .tile-blue-2 { background:#24428a !important; }
        .tile-blue-3 { background:#082053 !important; }
        .dashboard-tiles-bar {
            display: flex; flex-direction: row; gap: 24px; align-items: stretch; margin-bottom: 5px; flex-wrap: wrap;
            justify-content: space-between;
        }
        .dashboard-tile {
            flex: 1 1 0; min-width:210px; max-width:100vw; border-radius:13px; margin:0 0 0 0;
            box-shadow: 0 8px 33px #01184844, 0 1px 0 #fff2 inset;
            padding: 19px 18px 18px 18px;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            border: 2.5px solid #133073;
            position:relative;
            transition:box-shadow .2s;
        }
        .dashboard-tile[aria-current="true"] {box-shadow:0 0 0 2px #ffe06699 !important;border:3.5px solid #ffe066;}
        .dashboard-tile .tile-title { font-size: 1.14em; font-weight: 700; color: #fff; margin-bottom: 11px; text-align:center;}
        .dashboard-tile .tile-content { color: #fff; font-size: 1.27em; font-weight:700; text-align:center;}
        .tile-action-btn { margin-top:13px;width:100%; }
        .tile-action-btn button { font-size: 1.04em; padding: 8px 0; width: 100%; }
        /* Countdown Tile */
        .countdown-box-main-tile {margin-bottom:0;}
        .countdown-inner-tile {
        font-size: 1.27em; /* gleiche Größe wie .tile-content */
        color: #fff;
        display: flex;
        flex: 1;                 /* Füllt die Höhe aus */
        align-items: center;
        justify-content: center;
        width: 100%;
        }
        .dashboard-tile .tile-sandglass {display:inline-block;vertical-align:middle;}
        .sandglass-outer {display: inline-block; vertical-align: middle; line-height: 1;}
        .sandglass-svg {width:20px;height:20px;vertical-align:middle;} /* <--- Angepasstes Default-Icon kleiner */
        @media only screen and (max-width:920px){
            .dashboard-tiles-bar {flex-direction: column;gap:14px;align-items:stretch;}
            .flex-header-bar {flex-direction: column;gap:7px;}
        }
        @media only screen and (max-width:720px){
            .dashboard-tiles-bar{flex-direction:column;}
            .dashboard-tile{margin-bottom:8px;}
            .page-wrap-custom{padding:1px;}
            .sandglass-svg{width:16px;height:16px;}
        }
        @media only screen and (max-width:500px){
            .dashboard-tile{padding:9px 2px !important;}
            .dashboard-tiles-bar{gap:7px;}
            .batterie-box-main{font-size:14px;}
            .challenge-title{font-size:15px;}
            .countdown-inner-tile{font-size:13px;}
            .rangliste-table-html{font-size:13px;}
            .rl-bodyrow{min-height:28px;}
            .sandglass-svg{width:13px;height:13px;}
        }
        /* Rest: Unverändert aus Original */
        .explain-box-main{background:#001338;padding:20px 17px;border-radius:11px;color:#fff;font-size:16px;margin:35px 0 18px 0;}
        .infotext-admin-box{background:#001338;color:#fff;border-radius:7px;box-shadow:0 2px 7px #0005;padding:10px 12px;margin-bottom:5px;}
        .admin-infobox-main{background:#000 !important;border-left:8px solid #fff;border-radius:9px;padding:18px 12px;color:#fff;font-size:15px;margin-top: 5px; margin-bottom: 5px;}
        .challenge-title {font-size:27px;font-weight:800; color:#fff;letter-spacing:0.6px;}
        .challenge-titlebox {padding:13px 0 3px 0;}
        .batterie-box-main {
            display: flex;
            align-items: center;
            flex-direction:column;
            margin-bottom:2px;
            width:100%;
        }
        .batterie-icon-outer {
            display: flex;
            align-items: center;
            width: 73vw; max-width:82px; min-width:38px;
            height: 32px;
            margin-bottom: 2px;
            position:relative;
        }
        .batterie-body {
            width: 95%; height: 16px;
            border-radius: 7px;
            background: #303342;
            border: 2px solid #fff;
            position: relative;
            overflow: hidden;
        }
        .batterie-tip {
            width: 6px; height: 9px;
            background: #fff;
            border-radius:2px;
            position: absolute; right: -7px; top: 5px;
        }
        .batterie-fill {height:100%;transition:.5s all; border-radius:7px;}
        .batterie-fill-gruen { background: linear-gradient(90deg,#7befb4 10%, #91be6a 90%);}
        .batterie-fill-rot { background: linear-gradient(90deg,#fa6d3c 10%, #e1d2a0 90%);}
        .batterie-fill-extreme0 { background: repeating-linear-gradient(90deg, #c51e1e 0%, #fd1313 100%);}
        .batterie-fill-extreme100 { background: repeating-linear-gradient(90deg, #ffe066 0%, #7befb4 80%);}
        .batterie-label-success, .batterie-label-danger, .batterie-label-extreme0, .batterie-label-extreme100{
            font-size:13px;margin-top:1px;font-weight:700;background:rgba(255,255,255,0.12);color:#fff;
            padding:2px 9px; border-radius:8px;text-align:center;
        }
        .batterie-headtxt {color: #fff; font-size: 18px; font-weight: 700; margin-bottom: 5px;}
        .bilder-upload-wrap { background: #182256dd; border-radius:12px; padding:10px; margin-bottom:7px;}
        .rangliste-pager {margin:10px 0 17px 0;display:flex;justify-content:center;gap:8px;}
        .rangliste-pager-btn[aria-current="true"]{background:#ffe066;color:#021648;font-weight:900;}
        .rangliste-table-html { width:100%; background:#000 !important; border-radius:17px; margin:0 auto 13px auto; padding:0; box-shadow:0 7px 29px #000c, 0 1px 0 #ffe06633 inset; border:2px solid #fff; color:#fff !important; font-family:inherit; overflow-x:auto;}
        .rl-headrow { display:flex; flex-direction:row; font-size:1.14em; font-weight:900; border-bottom:2px solid #fff; color:#fff;background:#00142a;padding:7px 0;border-radius:13px 13px 0 0;}
        .rl-bodyrow { display:flex; flex-direction:row; align-items:center; border-bottom:1px solid #191e34; background:#111 !important;min-height:54px; font-size:1.08em;}
        .rl-my { background: linear-gradient(90deg,#155bc0b0 12%,#00142acc 90%) !important; font-weight: 900; border-left:8px solid #fff; color:#fff !important;}
        .rl-podium1 { border-left:10px solid #a6a6a6; background:linear-gradient(92deg,#45421d 60%,#fff5e099 100%) !important; color:#fff;}
        .rl-podium2 { border-left:10px solid #dfdfdf; background:linear-gradient(92deg,#191223 60%,#ffe06644 100%) !important;color:#fff;}
        .rl-podium3 { border-left:10px solid #a24404; background:linear-gradient(92deg,#4c2a09 60%,#ffa30033 100%) !important;color:#fff;}
        .rl-losers{background: linear-gradient(90deg,#27151b 10%,#c0363441 100%) !important; border-left:7px dashed #fff !important;color:#fff;}
        .rl-cell { flex:1 1 80px; text-align:center; font-size:1em; overflow:hidden; white-space:nowrap;}
        .rl-platz { width:56px;justify-content:center;align-items:center;display:flex;font-size:1.2em;font-weight:800;}
        .rl-name { min-width:0; max-width:180px; flex:2 1 100px; font-weight:700; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; text-align:left; padding-left:6px;}
        .rl-me { color:#fff;background:inherit !important;font-weight:900;}
        .rl-lotto { font-weight: bold;}
        .rl-zielok { background:#108f44; color:#fff; border-radius:7px; font-weight:bold;padding:2px 10px;}
        .rl-zielno { background:#c51e1e; color:#fff; border-radius:7px; font-weight:bold;padding:2px 10px;}
        .podium-star { font-size: 1.8em; color:#fff; text-shadow:0px 2px 8px #fff; padding-left:6px;}
        .lotterieicon { font-size:1.35em; margin-right:4px; vertical-align:middle;}
        @media only screen and (max-width:720px){
            .rangliste-table-html{padding:0;border-radius:13px;}
            .rl-headrow{display:none;}
            .rl-bodyrow {
                display:block !important;
                border-radius:11px;
                border:2px solid #fff2;
                margin:10px 7px 15px 7px !important;
                min-height:auto;
            }
            .rl-cell, .rl-platz, .rl-name{display:block;width:100%;min-width:0;max-width:none;text-align:left;margin:0 0 2px 0;padding:2px 0;}
            .rl-bodyrow > .rl-platz{font-size:21px;margin-left:-1px;}
            .rl-bodyrow > .rl-name{font-weight:800;font-size:17px;}
            .rl-cell-label{font-size:11px;font-weight:400;color:#ffe066b8;display:inline-block;width:auto;margin-right:8px;}
            .podium-star{display:inline;font-size:1.18em;}
            .dashboard-tile {padding: 13px 6px !important; font-size:15px;}
            .dashboard-tile .tile-content{font-size:1.09em;}
            .countdown-inner-tile {font-size:15px;}
            .sandglass-svg{width:16px;height:16px;}
        }
        .rl-cell-label{display:none;}
        @media only screen and (max-width:720px){
            .rl-cell-label{display:inline;}
        }
        [data-testid="stImage"] img{border-radius:8px;}
        .bilder-pager {margin:8px 0 16px 0;display:flex;justify-content:center;gap:5px;}
        .bilder-pager-btn[aria-current="true"]{background:#ffe066;color:#021648;font-weight:900;}
        @media only screen and (max-width:420px){
          .challenge-title{font-size:15px;}
        }
        .highlight-lauf-form { animation: highlightform 1.2s 1;}
        @keyframes highlightform {
            0% { box-shadow: 0 0 0 0 #ffe06677;}
            20% { box-shadow: 0 0 7px 6px #ffe066dd;}
            80% { box-shadow: 0 0 7px 6px #ffe066dd;}
            100% { box-shadow: 0 0 0 0 #ffe06600;}
        }
        .lauf-modal-fake-outer {
            position:fixed;z-index:2147483647;left:0;top:0;right:0;bottom:0;
            background:rgba(0,0,30,0.76);
            display:flex;align-items:center;justify-content:center;pointer-events:all;
        }
        .lauf-modal-fake-inner {
            background:#fff; color:#021; border-radius:19px; box-shadow:0 8px 44px #000b, 0 2px 0 #011848 inset;
            padding:42px 25px 25px 25px; min-width:298px; max-width:98vw; width:370px;
            max-height:94vh; overflow-y:auto; position:relative;
            border:7px solid #ffe066;
        }
        .lauf-modal-close-btn {
            background: #ffe066; color:#011848;
            font-weight:800; border-radius:100px; padding:0 13px;
            position:absolute; top:10px;right:14px;font-size:21px;cursor:pointer;border:none;
            z-index:10;
        }
        .lauf-modal-fake-inner label, .lauf-modal-fake-inner input, .lauf-modal-fake-inner select, .lauf-modal-fake-inner textarea {
            color: #011848 !important;
            font-size:1em;
        }
        .lauf-modal-fake-inner:focus-within {
            outline:2.5px solid #196ad8 !important;
            outline-offset:2px;
        }
        @media only screen and (max-width:600px){
            .lauf-modal-fake-inner { padding:20px 6px 13px 6px; min-width:0; width:98vw;}
        }
        .element-container label, .stTextInput label, .stNumberInput label, .stTimeInput label, .stDateInput label, .stTextArea label, .stMultiFileUploader label {
            color: #fff !important;
        }
        .stTextInput input, .stNumberInput input, .stTimeInput input, .stDateInput input, .stTextArea textarea {
            color:#fff !important;
            background-color:#001c42 !important;
            border-radius:6px !important;
            border:1.5px solid #fff !important;
        }
        .stButton>button {
            color: #011848 !important;
            background: #ffffff !important;
            border-radius:8px;
            font-weight:600;
        }
        .stButton>button:hover {
            background: #f1f5f9 !important;
        }
        .stButton>button:disabled {
            color:#999 !important;
            background:#bbb !important;
        }
        .stFileUploader>div>span {color: #fff !important;}
        .stFileUploader {background: #001c42 !important;border-radius:8px !important;border: 1.5px solid #fff;}
        .stProgress > div > div > div {background: #108f44 !important;}
        .stAlert {
            background: #17304a !important;
            color:#ffe066 !important;
            border-left: 8px solid #ffe066 !important;
        }
        .stAlert[data-testid="stAlertError"] {
            background: #300b0b !important;
            color: #ffb4a0 !important;
            border-left: 8px solid #c51e1e !important;
        }
        .stAlert[data-testid="stAlertWarning"] {
            background: #412a00 !important;
            color: #ffe066 !important;
            border-left: 8px solid #ffe066 !important;
        }
        .stAlert[data-testid="stAlertSuccess"] {
            background: #014d29 !important;
            color: #7befb4 !important;
            border-left: 8px solid #7befb4 !important;
        }
        .stAlert[data-testid="stAlertInfo"] {
            background: #01426f !important;
            color: #ffe066 !important;
            border-left: 8px solid #1393d4 !important;
        }
        .stSelectbox [data-baseweb="select"] {background: #001c42 !important;color: #fff !important;}
        .full-black-bg{background:#000 !important;}
        .lottery-btn-wrap {
        display: flex;
        justify-content: center;
        margin: 28px 0 22px 0;
        }
    
        .lottery-btn {
        width: 100%;
        max-width: 520px;
        padding: 16px 24px;
        font-size: 1.25em;
        font-weight: 800;
        color: #011848;
        background: linear-gradient(135deg, #ffe066, #ffd000);
        border: none;
        border-radius: 14px;
        cursor: pointer;
        box-shadow: 0 10px 28px rgba(0,0,0,0.35);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
    
        .lottery-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 34px rgba(0,0,0,0.45);
        }
    
        .lottery-btn span {
        font-size: 1.35em;
        margin-right: 10px;
        vertical-align: middle;
        }

        </style>
        """,
        unsafe_allow_html=True
    )
    
                       
    def user_display_name():
        if not st.session_state["user_name"].strip():
            return ""
        else:
            return st.session_state["user_name"].strip()
    
    
    def escape_html(txt):
        return html.escape(str(txt))
    
    
    def platz_lotterie_prozent(platz, wochenziel_erreicht):
        if not wochenziel_erreicht:
            return 0.0
        if 1 <= platz <= 9:
            table = {
                1: 25.0,
                2: 17.5,
                3: 12.5,
                4: 8.0,
                5: 7.0,
                6: 6.0,
                7: 5.0,
                8: 4.0,
                9: 3.0,
            }
            return table[platz]
        elif 10 <= platz <= 15:
            return 2.0
        return 0.0
    
    
    def get_challenge_end():
        return st.session_state.get("CHALLENGE_END_DATETIME")
    
    def get_challenge_start_end():
        start = st.session_state.get("CHALLENGE_START_DATETIME")
        end = st.session_state.get("CHALLENGE_END_DATETIME")
        if not start:
            # Fallback: Montag dieser Woche
            now = datetime.now()
            start = now - timedelta(days=now.weekday())
        if not end:
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return start, end

    
    from datetime import datetime

    def parse_datetime(t):
        """Versucht, einen Laufzeit-String oder datetime-Objekt korrekt zu parsen."""
        if isinstance(t, datetime):
            return t
        if isinstance(t, str):
            try:
                return datetime.fromisoformat(t)
            except ValueError:
                # Fallback: Mikrosekunden abschneiden
                if "." in t:
                    t = t.split(".")[0]
                    return datetime.fromisoformat(t)
        return None
    
    def filter_runs_for_week(läufe, dt_start, dt_ende):
        result = []
        for lauf in läufe:
            t = parse_datetime(lauf.get("time"))
            if t is not None and dt_start <= t <= dt_ende:
                result.append(lauf)
        return result


    
    from datetime import timedelta

    def get_challenge_week_start_end(week_number=None):
        start = st.session_state.get("CHALLENGE_START_DATETIME")
        end = st.session_state.get("CHALLENGE_END_DATETIME")
        
        if start is None:
            # Default: Montag dieser Woche
            now = datetime.now()
            start = now - timedelta(days=now.weekday())
        
        if week_number is not None and week_number > 1:
            start += timedelta(weeks=week_number - 1)
        
        if end is None:
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        else:
            # Optional: Ende auf 23:59:59 Uhr setzen
            end = datetime.combine(end.date(), datetime.max.time())
        
        return start, end

    
    def show_week_tile():
        import textwrap
        import streamlit as st
        import streamlit.components.v1 as components
    
        gesamt_wochen = st.session_state.get("GESAMT_WOCHEN", 5)
        aktuelle_woche = st.session_state.get("WOCHENNUMMER", 1)
        dt_start, dt_end = get_challenge_week_start_end(aktuelle_woche)
        teamziel_bisher = st.session_state.get("TEAMZIEL_WOCHEN_ERREICHT", 0)
    
        # Gesamtfortschritt dieser Woche
        gesamt_pct, _, _ = calc_overall_progress(
            all_users=st.session_state.get("active_users_this_week", []),
            runs_by_user=st.session_state.get("runs_by_user", {}),
            wochenziel_m=st.session_state.get("WOCHENZIEL", 0),
            dt_start=dt_start,
            dt_end=dt_end
        )
    
        # Schwelle & aktuelles Teamziel
        schwelle = st.session_state.get("BATTERIE_SCHWELLE", 50)
        teamziel_diese_woche = gesamt_pct >= schwelle
        teamziel_anzeige = teamziel_bisher + (1 if teamziel_diese_woche else 0)
        wochen_fortschritt = (aktuelle_woche / gesamt_wochen) * 100 if gesamt_wochen > 0 else 0
        green_width_pct = (teamziel_anzeige / gesamt_wochen) * 100 if gesamt_wochen > 0 else 0
    
        # Motivationstext anpassen, wenn die Challenge noch nicht gestartet ist
        start_datetime = st.session_state.get("CHALLENGE_START_DATETIME", datetime.now())
        now = datetime.now()
    
        if now < start_datetime:
            motivation_text = "⏳ Die Laufchallenge startet bald"
            motivation_color = "#ffe066"
        elif teamziel_diese_woche:
            motivation_text = "🎉 Das Teamziel dieser Woche wurde bereits erreicht."
            motivation_color = "#ffe066"
        else:
            motivation_text = "👥 Das Erreichen des Teamziels steht diese Woche noch aus!"
            motivation_color = "#ffe066"
    
        COMMON_TILE_HEIGHT = st.session_state.get("COMMON_TILE_HEIGHT", 180)
    
        html_code = textwrap.dedent(f"""
        <style>
            .dashboard-tile {{
                background: linear-gradient(135deg, #312e81, #1e3c72);
                color: #ffffff;
                border-radius: 14px;
                padding: 16px;
                height: {COMMON_TILE_HEIGHT}px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.15);
                font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: flex-start; /* alles oben */
                text-align: left;
            }}
    
            .tile-title {{ font-size: 1.2em; font-weight: 800; margin-bottom: 12px; }}
            .progress-container {{
                position: relative;
                background: rgba(255,255,255,0.25);
                border-radius: 8px;
                overflow: hidden;
                height: 14px;
                margin-bottom: 8px;
            }}
            .progress-bar {{
                background: #ffffff;
                height: 100%;
                width: {wochen_fortschritt:.0f}%;
                border-radius: 4px;
                z-index: 1;
            }}
            .progress-green {{
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                width: {green_width_pct:.0f}%;
                background: #7befb4;
                border-radius: 4px 0 0 4px;
                z-index: 2;
            }}
    
            .tile-label {{ font-size: 0.95em; font-weight: 600; margin-bottom: 2px; }}
            .tile-secondary {{ font-size: 0.95em; font-weight: 600; color: #ffffff; }}
            .tile-motivation {{
                font-size: 0.75em;
                font-weight: 600;
                color: {motivation_color};
                margin-top: 10px;  /* kleiner Abstand direkt unter Teamziel */
            }}
        </style>
    
        <div class="dashboard-tile">
            <div class="tile-title">✅ Fortschritt</div>
    
            <div class="progress-container">
                <div class="progress-bar"></div>
                <div class="progress-green"></div>
            </div>
    
            <div class="tile-label">Woche {aktuelle_woche} / {gesamt_wochen}</div>
            <div class="tile-secondary">Teamziel: {teamziel_anzeige} / {gesamt_wochen}</div>
            <div class="tile-motivation">{motivation_text}</div>
        </div>
        """)
    
        components.html(html_code, height=COMMON_TILE_HEIGHT)











    
    
                
    def safe_rerun(force_reload=True):
        st.rerun()
    
    
    
    
    def is_admin():
        user = st.session_state.get("user")
        if not user:
            return False
        return user.lower() in ADMIN_USERS
        
    
    
    
    
    def get_loser_indices_from_alldf(df_full):
        if df_full is not None and df_full.shape[0] >= 1:
            n = df_full.shape[0]
            last3 = set(range(max(n-3,0),n))
            return last3
        return set()
    
    def do_logout():
        st.session_state["user"] = None
        st.session_state["page"] = "login"
        
    
    
    
    def calc_overall_progress(all_users, runs_by_user, wochenziel_m, dt_start=None, dt_end=None):
        dt_start = dt_start or datetime.now()
        dt_end = dt_end or datetime.now()
        
        n_gesamt = len(all_users)
        n_done = 0
    
        for username in all_users:
            norm_user = normalize_name(username)
            runs = runs_by_user.get(norm_user, [])
            laufe_woche = filter_runs_for_week(runs, dt_start, dt_end)
            gesamtdist = sum(l.get("dist", 0) for l in laufe_woche if isinstance(l.get("dist"), (int, float)))
            if gesamtdist >= wochenziel_m:
                n_done += 1
    
        pct = (n_done / n_gesamt * 100.0) if n_gesamt > 0 else 0.0
        return pct, n_done, n_gesamt



    







    
    gesamt_pct, ges_done, ges_count = calc_overall_progress(all_users=all_users,runs_by_user=runs_by_user,wochenziel_m=WOCHENZIEL)
    

    
    def show_batterie_tile():
        import math
        import textwrap
        import streamlit as st
        import streamlit.components.v1 as components
    
        COMMON_TILE_HEIGHT = st.session_state.get("COMMON_TILE_HEIGHT", 180)
        COMMON_BAR_HEIGHT = st.session_state.get("COMMON_BAR_HEIGHT", 20)
        COMMON_BAR_BORDER = st.session_state.get("COMMON_BAR_BORDER", "2px")
    
        # --- Challenge-Woche bestimmen ---
        aktuelle_woche = st.session_state.get("WOCHENNUMMER", 1)
        dt_start, dt_end = get_challenge_week_start_end(aktuelle_woche)

        wochenziel_m = st.session_state.get("WOCHENZIEL", 0) /1000 # Mindest-Wochenziel
    
        # --- Gesamtfortschritt berechnen für die aktuelle Woche ---
        gesamt_pct, ges_done, ges_count = calc_overall_progress(
            all_users=st.session_state.get("active_users_this_week", []),
            runs_by_user=st.session_state.get("runs_by_user", {}),
            wochenziel_m=st.session_state.get("WOCHENZIEL", 0),
            dt_start=dt_start,
            dt_end=dt_end
        )
    
        schwelle = st.session_state.get("BATTERIE_SCHWELLE", 50)
    
        # --- Farbe relativ zur Schwelle ---
        if gesamt_pct == 0:
            fill_class = "fill-extreme0"
        elif gesamt_pct < schwelle:
            fill_class = "fill-rot"
        else:
            fill_class = "fill-gruen"
            
        start_datetime = st.session_state.get("CHALLENGE_START_DATETIME", datetime.now())
        now = datetime.now()
    
        if now < start_datetime:
            
            status_text = "Teamziel noch offen ✖"
            benoetigte_teilnehmer = math.ceil((schwelle / 100) * ges_count)
            fehlende_teilnehmer = max(0, benoetigte_teilnehmer - ges_done)
            info_text = f"ℹ️ Mind. {fehlende_teilnehmer} Spieler müssen das Ziel erreichen!"
            info_color = "#ffe066"
    
        # --- Status & Zusatzinfo ---
        elif gesamt_pct >= schwelle:
            status_text = "Teamziel erreicht ✔"
            info_text = "💪 Starkes Team – weiter so!"
            info_color = "#ffe066"
        else:
            status_text = "Teamziel noch offen ✖"
            benoetigte_teilnehmer = math.ceil((schwelle / 100) * ges_count)
            fehlende_teilnehmer = max(0, benoetigte_teilnehmer - ges_done)
            info_text = f"⚠️ Mind. {fehlende_teilnehmer} Spieler müssen das Ziel noch erreichen!"
            info_color = "#ffe066"
    
        html_code = textwrap.dedent(f"""
        <style>
            .dashboard-tile {{
                background: linear-gradient(135deg, #1e3c72, #1abc9c);
                color: #ffffff;
                border-radius: 14px;
                padding: 16px;
                height: {COMMON_TILE_HEIGHT}px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.15);
                font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
            }}
    
            .tile-title {{
                font-size: 1.4em;
                font-weight: 800;
                margin-bottom: 12px;
            }}
    
            .tile-row {{
                font-size: 0.9em;
                font-weight: 600;
                margin: 3px 0;
            }}
    
            .tile-hint {{
                margin-top: 7px;
                font-size: 0.75em;
                font-weight: 600;
                color: {info_color};
            }}
            .tile-goal {{ font-size: 0.8em; font-weight: 600; margin-bottom: 4px; color: #ffffff; }}
            .bar-body {{
                position: relative;
                width: 100%;
                height: {COMMON_BAR_HEIGHT}px;
                border: {COMMON_BAR_BORDER} solid #ffffff;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 8px;
            }}
    
            .fill-extreme0 {{
                height: 100%;
                background: #ff4d4f;
                transition: width 0.5s;
            }}
    
            .fill-rot {{
                height: 100%;
                background: linear-gradient(90deg, #ff4d4f 10%, #fa6d3c 90%);
                transition: width 0.5s;
            }}
    
            .fill-gruen {{
                height: 100%;
                background: linear-gradient(90deg, #7befb4 10%, #4cd964 90%);
                transition: width 0.5s;
            }}
    
            .threshold-line {{
                position: absolute;
                left: {schwelle}%;
                top: -4px;
                width: 3px;
                height: calc(100% + 8px);
                background: repeating-linear-gradient(
                    to bottom,
                    #000 0 4px,
                    #fff 4px 8px
                );
                opacity: 0.95;
                z-index: 20;
            }}
    
            .threshold-label {{
                position: absolute;
                left: {schwelle}%;
                top: -18px;
                transform: translateX(-50%);
                font-size: 0.7em;
                font-weight: 800;
                color: #ffe066;
                white-space: nowrap;
            }}
        </style>
    
        <div class="dashboard-tile">
            <div class="tile-title">👥 Teamziel</div>
    
            <div class="bar-body">
                <div class="{fill_class}" style="width:{gesamt_pct}%"></div>
                <div class="threshold-line"></div>
                <div class="threshold-label">{schwelle}% Ziel</div>
            </div>
    
            <div class="tile-row">{status_text}</div>
            <div class="tile-goal">Wochenziel: {wochenziel_m} km</div>
            <div class="tile-hint">{info_text}</div>
        </div>
        """)
    
        components.html(html_code, height=COMMON_TILE_HEIGHT)





    

    def show_rank_tile(user):
        import textwrap
        import streamlit as st
        import streamlit.components.v1 as components
    
        rows = st.session_state.get("rangliste_rows", [])
        if not rows or not user:
            st.warning("Rangliste ist noch nicht verfügbar.")
            return
    
        user_row = next((r for r in rows if r["name"] == user), None)
        if not user_row:
            podium_icon=""
            koch_text=""
            ziel_text=""
            platz="Keine Teilnahme"
            lotto_text = "0%"
            html_code = textwrap.dedent(f"""
            <style>
                .dashboard-tile {{
                    background: linear-gradient(135deg, #1e3c72, #2563eb);
                    color: #ffffff;
                    border-radius: 14px;
                    padding: 16px;
                    height: {COMMON_TILE_HEIGHT}px;
                    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-start;
                }}
        
                .tile-title {{
                    font-size: 1.4em;
                    font-weight: 800;
                    margin-bottom: 12px;
                }}
        
                .tile-row {{
                    font-size: 0.9em;
                    font-weight: 600;
                    margin: 3px 0;
                }}
        
                .tile-hint {{
                    margin-top: 10px;
                    font-size: 0.75em;
                    font-weight: 600;
                    color: "#ffe066";
                }}
            </style>
        
            <div class="dashboard-tile">
                <div class="tile-title">{platz} </div>
        
        
                <div class="tile-row">
                    Lotterie: {lotto_text}
                </div>
        
            </div>
            """)
        
            components.html(html_code, height=COMMON_TILE_HEIGHT)
  
        if user_row:
            platz = user_row.get("platz", 0)
            ziel_ok = user_row.get("ziel", False)
            lotto_pct = platz_lotterie_prozent(platz, ziel_ok)
        
            # --- Podest-Icon ---
            if platz == 1:
                podium_icon = "🥇 "
            elif platz == 2:
                podium_icon = "🥈 "
            elif platz == 3:
                podium_icon = "🥉 "
            else:
                podium_icon = "#️⃣ "
        
            # --- Status ---
            unter_den_koechen = platz > len(rows) - 3
        
            ziel_color = "#28a745" if ziel_ok else "#dc3545"
            koch_color = "#dc3545" if unter_den_koechen else "#28a745"
        
            ziel_text = "Beitrag Teamziel ✔" if ziel_ok else "Beitrag Teamziel ✖"
            koch_text = "Koch 🍽️" if unter_den_koechen else "Kein Koch"
        
            lotto_text = f"{lotto_pct:.0f}%" if ziel_ok else "0%"
        
            # --- Optionaler Motivationshinweis ---
            motivation = ""
            if True:
                motivation = "<div class='tile-hint'>🏃‍♂️ Laufe für dich und das Team!</div>"
    
        
            html_code = textwrap.dedent(f"""
            <style>
                .dashboard-tile {{
                    background: linear-gradient(135deg, #1e3c72, #2563eb);
                    color: #ffffff;
                    border-radius: 14px;
                    padding: 16px;
                    height: {COMMON_TILE_HEIGHT}px;
                    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-start;
                }}
        
                .tile-title {{
                    font-size: 1.4em;
                    font-weight: 800;
                    margin-bottom: 12px;
                }}
        
                .tile-row {{
                    font-size: 0.9em;
                    font-weight: 600;
                    margin: 3px 0;
                }}
        
                .tile-hint {{
                    margin-top: 10px;
                    font-size: 0.75em;
                    font-weight: 600;
                    color: #ffe066;
                }}
            </style>
        
            <div class="dashboard-tile">
                <div class="tile-title">{podium_icon}{platz}. Platz</div>
        
                <div class="tile-row" style="color:{ziel_color};">
                    {ziel_text}
                </div>
        
                <div class="tile-row" style="color:{koch_color};">
                    {koch_text}
                </div>
        
                <div class="tile-row">
                    Lotterie: {lotto_text}
                </div>
        
                {motivation}
            </div>
            """)
        
            components.html(html_code, height=COMMON_TILE_HEIGHT)






        
        
    def show_podium_tile():
        import textwrap
        import streamlit as st
        import streamlit.components.v1 as components
    
        rows = st.session_state.get("rangliste_rows", [])
        if not rows:
            st.warning("Rangliste ist noch nicht verfügbar.")
            return
    
        # Top 3
        podium_rows = rows[:3] if len(rows) >= 3 else rows
    
        podium_html = ""
        for user_row in podium_rows:
            name = user_row.get("name", "Unbekannt")
            platz = user_row.get("platz", 0)
    
            if platz == 1:
                platz_text = "1. Platz 🥇"
            elif platz == 2:
                platz_text = "2. Platz 🥈"
            elif platz == 3:
                platz_text = "3. Platz 🥉"
            else:
                platz_text = f"{platz}. Platz"
    
            podium_html += textwrap.dedent(f"""
                <div class="podium-row"><strong>{platz_text}</strong>: {name}</div>
            """)
        start_datetime = st.session_state.get("CHALLENGE_START_DATETIME", datetime.now())
        now = datetime.now()
        # --- Motivation (identisches Pattern wie show_rank_tile) ---
        motivation = ""
        if now < start_datetime:
            motivation = "<div class='tile-hint'>ℹ️ Keine Aussagekraft. Challenge startet bald!</div>"
        else:
            motivation = "<div class='tile-hint'>👑 Ruhm und Ehre!</div>"
    
        html_code = textwrap.dedent(f"""
        <style>
            .dashboard-tile {{
                background: linear-gradient(135deg, #1e40af, #3b82f6);
                color: #ffffff;
                border-radius: 14px;
                padding: 16px;
                height: {COMMON_TILE_HEIGHT}px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.15);
                font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
            }}
    
            .tile-title {{
                font-size: 1.2em;
                font-weight: 800;
                margin-bottom: 12px;
            }}
    
            .podium-row {{
                font-size: 0.95em;
                font-weight: 600;
                margin-bottom: 4px;
            }}
    
            /* IDENTISCH zu show_rank_tile */
            .tile-hint {{
                margin-top: 15px;
                font-size: 0.75em;
                font-weight: 600;
                color: #ffe066;
            }}
        </style>
    
        <div class="dashboard-tile">
            <div class="tile-title">🏆 Lauf-MVPs</div>
    
            {podium_html}
    
            {motivation}
        </div>
        """)
    
        components.html(html_code, height=COMMON_TILE_HEIGHT)




    def show_bottom3_tile():
        import textwrap
        import streamlit as st
        import streamlit.components.v1 as components
    
        rows = st.session_state.get("rangliste_rows", [])
        if not rows:
            st.warning("Rangliste ist noch nicht verfügbar.")
            return
    
        bottom_rows = rows[-3:] if len(rows) >= 3 else rows
    
        bottom_html = ""
        for user_row in bottom_rows:
            name = user_row.get("name", "Unbekannt")
            platz = user_row.get("platz", 0)
    
            platz_text = f"{platz}. Platz"
    
            bottom_html += textwrap.dedent(f"""
                <div class="podium-row"><strong>{platz_text}</strong>: {name}</div>
            """)
    
        # --- Motivation (analog zu den anderen Tiles) ---
        motivation = ""
        start_datetime = st.session_state.get("CHALLENGE_START_DATETIME", datetime.now())
        now = datetime.now()
        # --- Motivation (identisches Pattern wie show_rank_tile) ---
        motivation = ""
        if now < start_datetime:
            motivation = (
                "<div class='tile-hint'>"
                "ℹ️ Keine Aussagekraft. Challenge startet bald!"
                "</div>"
            )
        else:
            motivation = (
                "<div class='tile-hint'>"
                " 🍔 Ein Mannschaftsessen wird Stand jetzt von euch organisiert!"
                "</div>"
            )
    
        html_code = textwrap.dedent(f"""
        <style>
            .dashboard-tile {{
                background: linear-gradient(135deg, #2563eb, #2ecc71);
                color: #ffffff;
                border-radius: 14px;
                padding: 16px;
                height: {COMMON_TILE_HEIGHT}px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.15);
                font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
            }}
    
            .tile-title {{
                font-size: 1.2em;
                font-weight: 800;
                margin-bottom: 12px;
            }}
    
            .podium-row {{
                font-size: 0.95em;
                font-weight: 600;
                margin-bottom: 4px;
            }}
    
            /* IDENTISCH zu Rank- & Podium-Tile */
            .tile-hint {{
                margin-top: 4px;
                font-size: 0.75em;
                font-weight: 600;
                color: #ffe066;
            }}
        </style>
    
        <div class="dashboard-tile">
            <div class="tile-title">🍽️ Köche</div>
    
            {bottom_html}
    
            {motivation}
        </div>
        """)
    
        components.html(html_code, height=COMMON_TILE_HEIGHT)






    
    
    
    
    def show_countdown_tile():
        import textwrap
        import streamlit as st
        import streamlit.components.v1 as components
        from datetime import datetime
    
        COMMON_TILE_HEIGHT = 180
        end_datetime = st.session_state.get("CHALLENGE_END_DATETIME", datetime.now())
        start_datetime = st.session_state.get("CHALLENGE_START_DATETIME", datetime.now())
        end_ts = int(end_datetime.timestamp() * 1000)
        start_ts = int(start_datetime.timestamp() * 1000)
    
        html_code = textwrap.dedent(f"""
        <style>
            .dashboard-tile {{
                background: linear-gradient(135deg, #0f172a, #1e40af);
                color: #ffffff;
                border-radius: 14px;
                padding: 16px;
                height: {COMMON_TILE_HEIGHT}px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.15);
                font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                text-align: left;
            }}
            .tile-title {{
                font-size: 1.2em;
                font-weight: 800;
                margin-bottom: 12px;
            }}
            .countdown-inner-tile {{
                font-size: 0.6em;
                font-weight: 700;
                display: flex;
                justify-content: flex-start;
                gap: 6px;
                margin-bottom: 8px;
            }}
            .countdown-unit {{
                background: rgba(255,255,255,0.15);
                padding: 6px 10px;
                border-radius: 7px;
            }}
            .tile-note {{
                font-size: 0.75em;
                font-weight: 600;
                margin-top: 35px;
                color: #ffe066;
                text-align: left;
            }}
            .tile-note::before {{
                content: "⏳ ";
            }}
        </style>
    
        <div class="dashboard-tile">
            <div class="tile-title">⏱️ Countdown</div>
            <div id="countdown" class="countdown-inner-tile"></div>
            <div id="countdown-note" class="tile-note"></div>
        </div>
    
        <script>
            const startTime = {start_ts};
            const endTime = {end_ts};
    
            function updateCountdown() {{
                const now = new Date().getTime();
                const el = document.getElementById("countdown");
                const noteEl = document.getElementById("countdown-note");
                if (!el || !noteEl) return;
    
                let diff = 0;
                let noteText = "";
    
                if (now < startTime) {{
                    // Countdown bis zum Start
                    diff = startTime - now;
                    noteText = "Die Laufchallenge startet bald!";
                }} else if (now >= startTime && now <= endTime) {{
                    // Countdown bis zum Ende
                    diff = endTime - now;
                    noteText = ((diff / (1000*60*60)) > 72)
                        ? "Noch ausreichend Zeit, Läufe einzureichen und dich zu verbessern."
                        : "Die Zeit läuft! Jetzt noch Läufe einreichen!";
                }} else {{
                    // Challenge vorbei
                    el.innerHTML = "⏰ Challenge beendet!";
                    noteEl.innerHTML = "";
                    return;
                }}
    
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                diff %= (1000 * 60 * 60 * 24);
                const hours = Math.floor(diff / (1000 * 60 * 60));
                diff %= (1000 * 60 * 60);
                const minutes = Math.floor(diff / (1000 * 60));
                diff %= (1000 * 60);
                const seconds = Math.floor(diff / 1000);
    
                el.innerHTML = `
                    <div class="countdown-unit">${{days}}d</div>
                    <div class="countdown-unit">${{hours.toString().padStart(2,"0")}}h</div>
                    <div class="countdown-unit">${{minutes.toString().padStart(2,"0")}}m</div>
                    <div class="countdown-unit">${{seconds.toString().padStart(2,"0")}}s</div>
                `;
                noteEl.innerHTML = noteText;
            }}
    
            updateCountdown();
            setInterval(updateCountdown, 1000);
        </script>
        """)
    
        components.html(html_code, height=COMMON_TILE_HEIGHT)


    def open_run_form():
        st.session_state["show_run_form"] = True
        st.session_state["show_my_runs"] = False
        st.session_state["runs_expander_open"] = True

    def toggle_my_runs():
        st.session_state["show_my_runs"] = not st.session_state.get("show_my_runs", False)
        st.session_state["show_run_form"] = False
        st.session_state["runs_expander_open"] = True




    
    def save_runs(runs_by_user):
        import os
        import json
    
        # Ordner sicherstellen
        os.makedirs(os.path.dirname(RUNS_FILE), exist_ok=True)
    
        serializable = {}
        for user, runs in runs_by_user.items():
            serializable[user] = []
            for r in runs:
                r_copy = r.copy()
                r_copy["time"] = r_copy["time"].isoformat()
                serializable[user].append(r_copy)
    
        with open(RUNS_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)

              
    def add_run_entry():
        import base64
        from datetime import datetime
        
        challenge_start = st.session_state.get("CHALLENGE_START_DATETIME", datetime.now())
        challenge_started = challenge_start and datetime.now() >= challenge_start
    
        user = st.session_state.get("user")
        if not user:
            st.warning("Bitte zuerst einloggen, um einen Lauf einzutragen.")
            return
        

    
        # Session-State Flags initialisieren
        if "show_run_form" not in st.session_state:
            st.session_state["show_run_form"] = False
        if "show_my_runs" not in st.session_state:
            st.session_state["show_my_runs"] = False
    
        # Zwei Buttons nebeneinander
        col1, col2 = st.columns([1, 1], gap="small")
        with col1:
            st.button(
                "➕ Neuen Lauf eintragen",
                key="btn_add_run",
                on_click=open_run_form
            )
        
        with col2:
            st.button(
                "👀 Meine Läufe anzeigen / ausblenden",
                key="btn_toggle_runs",
                on_click=toggle_my_runs
            )

    
        # Formular für neuen Lauf
        if st.session_state["show_run_form"]:
            st.markdown(
            f'<h3 style="color: white;">🏃 Lauf eintragen (Bild/Screenshot als Beleg)</h3>',
            unsafe_allow_html=True
            )

            with st.form("run_form", clear_on_submit=True):
                col1_f, col2_f = st.columns([2, 2])
                with col1_f:
                    dist_km = st.number_input("Distanz (km)", min_value=0.0, step=0.1, format="%.2f")
                with col2_f:
                    c1, c2 = st.columns(2)
                    with c1:
                        minutes = st.number_input("Minuten", min_value=0, step=1)
                    with c2:
                        seconds = st.number_input("Sekunden", min_value=0, max_value=59, step=1)
    
                proof_image = st.file_uploader(
                    "📸 Beweisbild (Screenshot / Foto vom Laufband)",
                    type=["png", "jpg", "jpeg"]
                )
                
                comment = st.text_area(
                "💬 Bei anderen Aktivitäten als klassischen Läufen hier bitte kurz vermerken um welche Aktivität es sich handelt",
                placeholder="z. B. Hallenkick",
                max_chars=300
                )
    
                submit = st.form_submit_button("Eintragen")
                
            if user not in st.session_state.get("active_users_this_week", []):
                st.warning("Du bist diese Woche nicht als Teilnehmer registriert.")
                return
                
            elif submit and not challenge_started:
                st.markdown(
                """
                <div style="
                    background-color: #011848;
                    color: #ffffff;
                    padding: 12px 16px;
                    border-radius: 10px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                ">
                    <span style="font-size: 1.2em;">ℹ️</span>
                    <span>Die Laufchallenge hat noch nicht begonnen. Läufe können erst ab dem Startdatum eingetragen werden.</span>
                </div>
                """,
                unsafe_allow_html=True
                )
    
            elif submit:
                total_seconds = minutes * 60 + seconds
                dist_m = int(dist_km * 1000)
                
    
                if dist_m <= 0 or total_seconds <= 0:
                    st.error("Bitte gültige Distanz und Zeit eingeben.")
                    return
    
                if proof_image is None:
                    st.error("Bitte lade ein Beweisbild hoch.")
                    return
    
                image_b64 = base64.b64encode(proof_image.read()).decode("utf-8")
    
                runs_by_user = load_runs()
                norm_user = normalize_name(user)
                runs_by_user.setdefault(norm_user, [])
    
                runs_by_user[norm_user].append({
                    "dist": dist_m,
                    "duration": total_seconds,
                    "time": datetime.now(),
                    "comment": comment.strip() if comment else "",   # 👈 NEU
                    "proof_image": {
                        "name": proof_image.name,
                        "type": proof_image.type,
                        "data": image_b64
                    },
                    "admin_confirmed": False,  # neu
                    "editable": True           # neu
                })

    
                st.session_state["runs_by_user"] = runs_by_user
                save_runs(runs_by_user)
    
                st.success(f"✅ Lauf gespeichert: {dist_km:.2f} km in {minutes}:{seconds:02d} min")
                import time as time_sleep
                time_sleep.sleep(1)
                st.session_state["show_run_form"] = False
                st.rerun()
    
        # Läufe anzeigen (unabhängig vom Formular)
        if st.session_state.get("show_my_runs", False):
            show_user_runs_overview()



    def edit_run_form(user, run_index, run, admin=False):
        import base64
        from datetime import datetime
    
        with st.form(f"edit_form_{user}_{run_index}"):
            dist_km = st.number_input(
                "Distanz (km)",
                min_value=0.0,
                step=0.1,
                value=run["dist"] / 1000
            )
    
            duration = run.get("duration", 0)
            minutes = st.number_input("Minuten", min_value=0, step=1, value=duration // 60)
            seconds = st.number_input("Sekunden", min_value=0, max_value=59, step=1, value=duration % 60)
    
            # ✅ EDITIERBARER KOMMENTAR
            comment = st.text_area(
                "💬 Kommentar",
                value=run.get("comment", ""),
                max_chars=300
            )
    
            proof = run.get("proof_image")
            if proof and "data" in proof:
                image_bytes = base64.b64decode(proof["data"])
                st.image(image_bytes, caption=f"Aktuelles Beweisbild – {proof.get('name','')}")
    
            proof_image = st.file_uploader(
                "📸 Neues Beweisbild (optional)",
                type=["png", "jpg", "jpeg"]
            )
    
            submit = st.form_submit_button("Speichern")
            if submit:
                total_seconds = minutes * 60 + seconds
                dist_m = int(dist_km * 1000)
        
                runs_by_user = load_runs()
                run_entry = runs_by_user[user][run_index]
        
                run_entry["dist"] = dist_m
                run_entry["duration"] = total_seconds
                run_entry["comment"] = comment.strip() if comment else ""
                run_entry["time"] = datetime.now()
        
                if proof_image is not None:
                    image_b64 = base64.b64encode(proof_image.read()).decode("utf-8")
                    run_entry["proof_image"] = {
                        "name": proof_image.name,
                        "type": proof_image.type,
                        "data": image_b64
                    }
        
                if not admin:
                    run_entry["editable"] = True
        
                save_runs(runs_by_user)
        
                st.success("✅ Lauf erfolgreich bearbeitet!")
                st.session_state["edit_run_index"] = None
                st.session_state["edit_run_user"] = None
                st.rerun()



    def show_user_runs_overview():
        import base64
        from datetime import datetime as dt
        
    
        user = st.session_state.get("user")
        if not user:
            st.warning("Bitte zuerst einloggen, um deine Läufe einzusehen.")
            return
    
        
            st.markdown(
            f'<h3 style="color: white;">🏃 Deine bisher eingetragenen Läufe"</h3>',
            unsafe_allow_html=True
            )
        runs_by_user = load_runs()
        norm_user = normalize_name(user)
        user_runs = runs_by_user.get(norm_user, [])
        
        start_datetime = st.session_state.get("CHALLENGE_START_DATETIME", dt.now())
        now = dt.now()
        
        if start_datetime>now:
            st.markdown(
                        """
                        <div style="
                            background-color: #011848;
                            color: #ffffff;
                            padding: 12px 16px;
                            border-radius: 10px;
                            font-weight: 600;
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                        ">
                            <span style="font-size: 1.2em;">ℹ️</span>
                            <span>Die Challenge beginnt demnächst. Noch keine Läufe vorhanden.
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
    
        elif not user_runs:

            st.markdown(
                        """
                        <div style="
                            background-color: #011848;
                            color: #ffffff;
                            padding: 12px 16px;
                            border-radius: 10px;
                            font-weight: 600;
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                        ">
                            <span style="font-size: 1.2em;">ℹ️</span>
                            <span>Du hast noch keine Läufe eingetragen.
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
            return
    
        dt_start, dt_end = get_challenge_start_end()
    
        edit_index = st.session_state.get("edit_run_index")
        edit_user = st.session_state.get("edit_run_user")
    
        for i, run in enumerate(user_runs, start=1):
            run_time = run.get("time")
            if isinstance(run_time, str):
                from datetime import datetime
                run_time = datetime.fromisoformat(run_time)
    
            if not (dt_start <= run_time <= dt_end):
                continue
    
            dist_km = run.get("dist", 0) / 1000
            duration = run.get("duration", 0)
            minutes = duration // 60
            seconds = duration % 60
    
            admin_confirmed = run.get("admin_confirmed", False)
            editable = run.get("editable", True) and not admin_confirmed
    
            st.markdown(
                f"**#{i}** 📅 {run_time.strftime('%d.%m.%Y %H:%M')} 📏 **{dist_km:.2f} km** ⏱ **{minutes}:{seconds:02d} min**"
            )
            run_comment = run.get("comment", "").strip()
            if run_comment:
                st.markdown(
                    f"""
                    <div style="
                        background: rgba(255,255,255,0.08);
                        padding: 8px 12px;
                        border-radius: 8px;
                        margin-top: 6px;
                        font-size: 0.85em;
                    ">
                        💬 {escape_html(run_comment)}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
            proof = run.get("proof_image")
            if proof and "data" in proof:
                image_bytes = base64.b64decode(proof["data"])
                st.image(image_bytes, caption=f"Beweisbild – {proof.get('name','')}")
    
            if admin_confirmed:
                st.markdown(
                """
                <div style="
                    background-color: #011848;
                    color: #ffffff;
                    padding: 12px 16px;
                    border-radius: 10px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                ">
                    <span style="font-size: 1.2em;">ℹ️</span>
                    <span>✅ Bestätigt durch Admin</span>
                </div>
                """,
                unsafe_allow_html=True
                )
            elif editable:
                # Button zum Bearbeiten
                if st.button(f"Lauf #{i} bearbeiten", key=f"edit_user_{i}"):
                    st.session_state["edit_run_index"] = i-1
                    st.session_state["edit_run_user"] = norm_user
                    st.rerun()
    
            # **Formular direkt unter dem aktuellen Lauf anzeigen**
            if edit_index == i-1 and edit_user == norm_user:
                edit_run_form(
                    edit_user,
                    edit_index,
                    run,
                    admin=False
                )
    
            st.divider()







    import math
    
    def show_lotterie_kacheln():
        preise = st.session_state.get("lotterie_preise", [
            {"icon": "🎁", "text": "VH-Gutschein 75€"},
            {"icon": "🎁", "text": "Mawell-Gutschein 50€"},
            {"icon": "🎁", "text": "11Teamsports-Gutschein 50€"},
        ])
    
        n = len(preise)
        
        # Maximal 3 Kacheln pro Reihe
        max_cols = 3
        rows_needed = math.ceil(n / max_cols)
    
        index = 0
        for r in range(rows_needed):
            cols_in_row = min(max_cols, n - index)
            cols = st.columns(cols_in_row, gap="medium")
            for col in cols:
                preis = preise[index]
                with col:
                    st.markdown(
                        f"""
                        <div style="
                            height: 140px;
                            background: linear-gradient(135deg, #1e3c72, #2a5298);
                            border-radius: 12px;
                            color: white;
                            font-weight: 600;
                            display: flex;
                            flex-direction: column;
                            justify-content: center;
                            align-items: center;
                            text-align: center;
                            padding: 12px 8px;
                        ">
                            <div style="font-size: 2em; margin-bottom: 8px;">{preis['icon']}</div>
                            <div style="font-size: 0.9em; line-height: 1.2em;">{preis['text']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                index += 1
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)















    def show_weekly_ranking_dashboard():
        from datetime import datetime
        import streamlit as st
        import pandas as pd
        import numpy as np
    
        runs_by_user = st.session_state.get("runs_by_user", {})
        all_users = st.session_state.get("active_users_this_week", [])
        wochenziel = st.session_state.get("WOCHENZIEL", 5000)
    
        dt_start, dt_end = get_challenge_start_end()
        rows = []
    
        # ---------- Daten aufbereiten ----------
        for username in all_users:
            norm_user = normalize_name(username)
            runs = runs_by_user.get(norm_user, [])
    
            week_runs = []
            for r in runs:
                t = r.get("time")
                if isinstance(t, str):
                    try:
                        t = datetime.fromisoformat(t)
                    except Exception:
                        continue
                if isinstance(t, datetime) and dt_start <= t <= dt_end:
                    week_runs.append(r)
    
            total_dist = sum(
                r.get("dist", 0)
                for r in week_runs
                if isinstance(r.get("dist"), (int, float))
            )
    
            best_speed = None
            for r in week_runs:
                dist = r.get("dist", 0)
                dur = r.get("duration", 0)
                if dist > 0 and dur > 0:
                    speed = (dist / 1000) / (dur / 3600)
                    if best_speed is None or speed > best_speed:
                        best_speed = speed
    
            ziel_ok = total_dist >= wochenziel
    
            rows.append({
                "Platz": 0,  # wird später gesetzt
                "Name": username,
                "Distanz (km)": total_dist / 1000 if total_dist else np.nan,
                "Top-Speed (km/h)": best_speed if best_speed is not None else np.nan,
                "Wochenziel": "Ja" if ziel_ok else "Nein",
                "Lotterie (%)": 0,  # wird später berechnet
                "Ziel_bool": ziel_ok  # für Styling falls gewünscht
            })
    
        # ---------- Sortieren & Platz ----------
        rows.sort(key=lambda x: x["Distanz (km)"] if not pd.isna(x["Distanz (km)"]) else 0, reverse=True)
        for i, r in enumerate(rows, start=1):
            r["Platz"] = i
            r["Lotterie (%)"] = platz_lotterie_prozent(i, r["Ziel_bool"])
    
        # ---------- DataFrame bauen ----------
        df = pd.DataFrame(rows)
    
        # NaN in "-" umwandeln und Zahlen formatieren
        df["Top-Speed (km/h)"] = df["Top-Speed (km/h)"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
        df["Distanz (km)"] = df["Distanz (km)"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
        df["Lotterie (%)"] = df["Lotterie (%)"].apply(lambda x: f"{x:.1f}" if x > 0 else "-")
        df=df.drop(columns=["Ziel_bool"])
        styled_df = (
            df.style
            .set_properties(**{
                "background-color": "black",
                "color": "white",
                "border-color": "#333"
            })
            .set_table_styles([
                {"selector": "th", "props": [
                    ("background-color", "#011848"),
                    ("color", "white"),
                    ("font-weight", "bold")
                ]}
            ])
        )
        # ---------- Tabelle rendern ----------
        st.dataframe(styled_df, use_container_width=True, hide_index=True)















    


    # Vor dem Aufruf der Kacheln einmal die Rangliste berechnen
    def update_rangliste():
        from datetime import datetime
        runs_by_user = st.session_state.get("runs_by_user", {})
        all_users = st.session_state.get("active_users_this_week", [])
        wochenziel = st.session_state.get("WOCHENZIEL", 5000)
        dt_start, dt_end = get_challenge_start_end()
    
        rows = []
        for username in all_users:
            norm_user = normalize_name(username)
            runs = runs_by_user.get(norm_user, [])
            week_runs = [r for r in runs if isinstance(r.get("time"), datetime) and dt_start <= r["time"] <= dt_end]
            total_dist = sum(r.get("dist",0) for r in week_runs)
            best_speed = None
            for r in week_runs:
                dist = r.get("dist", 0)
                dur = r.get("duration", 0)
                if dist > 0 and dur > 0:
                    speed = (dist / 1000) / (dur / 3600)
                    if best_speed is None or speed > best_speed:
                        best_speed = speed
            ziel_ok = total_dist >= wochenziel
            rows.append({"name": username, "dist": total_dist, "best_speed": best_speed, "ziel": ziel_ok})
    
        rows.sort(key=lambda x: x["dist"], reverse=True)
        for i, r in enumerate(rows, start=1):
            r["platz"] = i
            r["lotto"] = platz_lotterie_prozent(i, r["ziel"])
    
        st.session_state["rangliste_rows"] = rows
        
        
        
    
    # Aktualisieren bevor Kacheln angezeigt werden
    update_rangliste()
    
    # Nutzer aus session_state
    user = st.session_state.get("user")
    
    
    st.markdown('<div class="page-wrap-custom">', unsafe_allow_html=True)
    
    aktuelle_woche = st.session_state.get("WOCHENNUMMER", 1)
    
    st.markdown(
        f"""
        <div class="challenge-titlebox">
            <div class="challenge-title">
                Willkommen zur Laufchallenge des TSV Gerabronn
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("""
        <style>
        .dashboard-tiles-bar {
        background: #011848;
        padding: 16px;
        border-radius: 14px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.expander("Übersicht", expanded=True):
        st.markdown('<div class="dashboard-tiles-bar" role="region" aria-label="Übersicht">', unsafe_allow_html=True)
        col_tile1, col_tile2, col_tile3 = st.columns(3)
        with col_tile1:
            show_rank_tile(user) 
            st.markdown('</section>', unsafe_allow_html=True)
        with col_tile2:
            show_podium_tile()
            st.markdown('</section>', unsafe_allow_html=True)
        with col_tile3:
            show_batterie_tile()
            st.markdown('</section>', unsafe_allow_html=True)
        
        
        col_tile4, col_tile5, col_tile6 = st.columns(3)
        with col_tile4:
            show_bottom3_tile()        
            st.markdown('</section>', unsafe_allow_html=True)
        with col_tile5:
            show_countdown_tile()
            st.markdown('</section>', unsafe_allow_html=True)
        with col_tile6:
            show_week_tile() 
            st.markdown('</section>', unsafe_allow_html=True)
        

    

    with st.expander("Laufrangliste", expanded=False):
        st.markdown(
        f'<h2 style="color: white;">🏆 Laufrangliste – Woche {max(aktuelle_woche,1)}</h2>',
        unsafe_allow_html=True
        )
        show_weekly_ranking_dashboard()
    
        



    with st.expander("Lotterie", expanded=False):
        # ------------------ Preise aus session_state oder Standardliste ------------------
        if "lotterie_preise" not in st.session_state:
           # Standardwerte, falls Admin noch nichts gesetzt hat
           st.session_state["lotterie_preise"] = [
               {"name": "Preis 1", "beschreibung": "Ein tolles Buchpaket", "icon": "🎁"},
               {"name": "Preis 2", "beschreibung": "Gutschein für ein Café", "icon": "☕"},
               {"name": "Preis 3", "beschreibung": "Ein cooles Gadget", "icon": "🛠️"},
           ]
           
        st.markdown(
        f'<h2 style="color: white;">💰 Preise Lotterie – Woche {max(aktuelle_woche,1)}</h2>',
        unsafe_allow_html=True
        )
        st.markdown("Der Gewinner der Lotterie zur Laufchallenge dieser Woche darf einen der folgenden Preise auswählen:")
    
        show_lotterie_kacheln()

    
        
        # Klick auswerten
        # Klick auswerten (NEUE Streamlit-API)
        if st.button(
            "Zur Lotterieansicht wechseln",
            use_container_width=True,
            key="go_lotterie"
        ):
            st.session_state["page"] = "lotterie"
            st.rerun()
    
    with st.expander("Infos", expanded=False):
        st.markdown(
        f'<h2 style="color: white;">💡 Informationen zum Modus – Woche {max(aktuelle_woche,1)}</h2>',
        unsafe_allow_html=True
        )

        
        if st.session_state['admin_info_text']:
            st.markdown(
                f"<div class='infotext-admin-box'>{escape_html(st.session_state['admin_info_text'])}</div>",
                unsafe_allow_html=True
            )
        
        
        st.markdown('</div>', unsafe_allow_html=True)
    add_run_entry()
   
    if is_admin():
        if st.button("🔑 Admin-Bereich"):
            st.session_state["page"] = "admin"
            st.rerun()
    
    if st.button("Abmelden", key="logout_btn_home"):
        do_logout()
        safe_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
def show_admin_page():
    
    import streamlit as st
    import pandas as pd
    from datetime import datetime, timedelta, time
    import html
    import streamlit.components.v1 as components
    import textwrap
    from streamlit_autorefresh import st_autorefresh 
    import time as time_sleep
    import json
    import os
    import re
    
    GESAMT_WOCHEN = 5  # oder später aus Session/Admin konfigurierbar
    
    ADMIN_USERS = {
        "sebastian",
        "tobi",
        "sergej"
    }
    SETTINGS_FILE = "settings.json"
    RUNS_FILE = "data/runs_by_user.json"
    
    def save_settings(settings):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    def load_runs():
        if not os.path.exists(RUNS_FILE):
            return {}
    
        try:
            with open(RUNS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                raw = json.loads(content)
                if isinstance(raw, dict):
                    # Konvertiere ggf. Strings zu datetime, falls du das brauchst
                    for user, runs in raw.items():
                        for run in runs:
                            if "time" in run and isinstance(run["time"], str):
                                from datetime import datetime
                                run["time"] = datetime.fromisoformat(run["time"])
                    return raw
                else:
                    return {}
        except json.JSONDecodeError:
            return {}
        except Exception as e:
            st.error(f"Ladefehler für Läufe: {e}")
            return {}

    
    def is_admin():
        user = st.session_state.get("user")
        if not user:
            return False
        return user.lower() in ADMIN_USERS

    if not is_admin():
        st.error("⛔ Keine Berechtigung.")
        return


    st.markdown("## 🔑 Admin-Bereich")
    

    if st.button("⬅️ Zurück zum Dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()

    tab_settings, tab_runs = st.tabs([
        "⚙️ Einstellungen",
        "🏃 Läufe & Beweisbilder"
    ])
    
    def save_runs(runs_by_user):
        import os
        import json
    
        # Ordner sicherstellen
        os.makedirs(os.path.dirname(RUNS_FILE), exist_ok=True)
    
        serializable = {}
        for user, runs in runs_by_user.items():
            serializable[user] = []
            for r in runs:
                r_copy = r.copy()
                r_copy["time"] = r_copy["time"].isoformat()
                serializable[user].append(r_copy)
    
        with open(RUNS_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
    def get_challenge_start_end():
        start = st.session_state.get("CHALLENGE_START_DATETIME")
        end = st.session_state.get("CHALLENGE_END_DATETIME")
        if not start:
            # Fallback: Montag dieser Woche
            now = datetime.now()
            start = now - timedelta(days=now.weekday())
        if not end:
            end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        return start, end
    
    def edit_run_form(user, run_index, run, admin=False):
        import base64
        from datetime import datetime
    
        with st.form(f"edit_form_{user}_{run_index}"):
            dist_km = st.number_input(
                "Distanz (km)",
                min_value=0.0,
                step=0.1,
                value=run["dist"] / 1000
            )
    
            duration = run.get("duration", 0)
            minutes = st.number_input("Minuten", min_value=0, step=1, value=duration // 60)
            seconds = st.number_input("Sekunden", min_value=0, max_value=59, step=1, value=duration % 60)
    
            # ✅ EDITIERBARER KOMMENTAR
            comment = st.text_area(
                "💬 Kommentar",
                value=run.get("comment", ""),
                max_chars=300
            )
    
            proof = run.get("proof_image")
            if proof and "data" in proof:
                image_bytes = base64.b64decode(proof["data"])
                st.image(image_bytes, caption=f"Aktuelles Beweisbild – {proof.get('name','')}")
    
            proof_image = st.file_uploader(
                "📸 Neues Beweisbild (optional)",
                type=["png", "jpg", "jpeg"]
            )
    
            submit = st.form_submit_button("Speichern")
    
        if submit:
            total_seconds = minutes * 60 + seconds
            dist_m = int(dist_km * 1000)
    
            runs_by_user = load_runs()
            run_entry = runs_by_user[user][run_index]
    
            run_entry["dist"] = dist_m
            run_entry["duration"] = total_seconds
            run_entry["comment"] = comment.strip() if comment else ""
            run_entry["time"] = datetime.now()
    
            if proof_image is not None:
                image_b64 = base64.b64encode(proof_image.read()).decode("utf-8")
                run_entry["proof_image"] = {
                    "name": proof_image.name,
                    "type": proof_image.type,
                    "data": image_b64
                }
    
            if not admin:
                run_entry["editable"] = True
    
            save_runs(runs_by_user)
    
            st.success("✅ Lauf erfolgreich bearbeitet!")
            st.session_state["edit_run_index"] = None
            st.session_state["edit_run_user"] = None
            st.session_state[f"expander_open_{user}"] = True
            st.rerun()


    
    def show_admin_runs_overview():
        import base64
        from datetime import datetime
    
        st.markdown("### 🏃 Eingetragene Läufe aller Nutzer")
    
        runs_by_user = load_runs()
        dt_start, dt_end = get_challenge_start_end()
    
        edit_user = st.session_state.get("admin_edit_user")
        edit_index = st.session_state.get("admin_edit_run_index")
    
        for username, runs in runs_by_user.items():
            if not runs:
                continue
    
            expander_key = f"expander_open_{username}"

            with st.expander(
                f"👤 {username} ({len(runs)} Läufe)",
                expanded=st.session_state.get(expander_key, False)
            ):

                for i, run in enumerate(runs, start=1):
                    run_time = run.get("time")
                    if isinstance(run_time, str):
                        run_time = datetime.fromisoformat(run_time)
    
                    if not (dt_start <= run_time <= dt_end):
                        continue
    
                    dist_km = run.get("dist", 0) / 1000
                    duration = run.get("duration", 0)
                    minutes = duration // 60
                    seconds = duration % 60
                    admin_confirmed = run.get("admin_confirmed", False)
    
                    st.markdown(
                        f"**#{i}** 📅 {run_time.strftime('%d.%m.%Y %H:%M')} "
                        f"📏 **{dist_km:.2f} km** ⏱ **{minutes}:{seconds:02d} min**"
                    )
    
                    # Beweisbild
                    proof = run.get("proof_image")
                    if proof and "data" in proof:
                        image_bytes = base64.b64decode(proof["data"])
                        st.image(image_bytes, caption=f"Beweisbild – {proof.get('name','')}")
    
                    # -------------------------
                    # ✏️ Bearbeiten / Wechseln
                    # -------------------------

                    if st.button(
                        f"✏️ Lauf #{i} bearbeiten",
                        key=f"edit_admin_{username}_{i}"
                    ):
                        st.session_state["admin_edit_user"] = username
                        st.session_state["admin_edit_run_index"] = i - 1
                        st.session_state[f"expander_open_{username}"] = True
                    
                        # 👇 Scroll-Ziel merken
                        st.session_state["scroll_to"] = f"scroll_target_{username}_{i}"
                    
                        st.rerun()

    
                    # -------------------------
                    # Edit-Formular DIREKT UNTER DEM LAUF
                    # -------------------------
                    anchor_id = f"scroll_target_{username}_{i}"

                    # unsichtbarer HTML-Anker
                    components.html(
                        f'<div id="{anchor_id}"></div>',
                        height=0
                    )
                    if edit_user == username and edit_index == i - 1:
                        st.markdown("#### ✏️ Lauf bearbeiten (Admin)")
                        edit_run_form(
                            user=username,
                            run_index=i - 1,
                            run=run,
                            admin=True
                        )
    
                    # -------------------------
                    # ✅ Bestätigen
                    # -------------------------
                    if not admin_confirmed:
                        if st.button(
                            f"✅ Lauf #{i} bestätigen",
                            key=f"confirm_{username}_{i}"
                        ):
                            runs_by_user[username][i - 1]["admin_confirmed"] = True
                            runs_by_user[username][i - 1]["editable"] = False
                            save_runs(runs_by_user)
                            st.success("Lauf bestätigt!")
                            st.rerun()
                    else:
                        st.markdown(
                            """
                            <div style="
                                background-color: #011848;
                                color: #ffffff;
                                padding: 12px 16px;
                                border-radius: 10px;
                                font-weight: 600;
                                display: flex;
                                align-items: center;
                                gap: 8px;
                                box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                            ">
                                <span style="font-size: 1.2em;">ℹ️</span>
                                <span>✅ Bestätigt</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
    
                    st.divider()


    
    def admin_module():
        if not is_admin():
            st.error("⛔ Keine Berechtigung.")
            return
    
    
        # -------------------------------------------------
        # TAB 1: EINSTELLUNGEN
        # -------------------------------------------------
        with tab_settings:

            
            st.markdown(
                        """
                        <div style="
                            background-color: #011848;
                            color: #ffffff;
                            padding: 12px 16px;
                            border-radius: 10px;
                            font-weight: 600;
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                        ">
                            <span style="font-size: 1.2em;">ℹ️</span>
                            <span>Hier können challenge-relevante Parameter angepasst werden. 
                            Änderungen gelten sofort für alle!</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                        )
    
            # ---------- Basis-Einstellungen ----------
            neue_woche = st.slider(
                "Aktuelle Challenge-Woche",
                min_value=0,
                max_value=GESAMT_WOCHEN,
                value=st.session_state["WOCHENNUMMER"]
            )
    
            ziel = st.number_input(
                "Wochenziel in Metern",
                min_value=500,
                max_value=100000,
                value=st.session_state["WOCHENZIEL"],
                step=100
            )
    
            batterie = st.slider(
                "Batterie-Schwellenwert (%)",
                min_value=1,
                max_value=100,
                value=st.session_state["BATTERIE_SCHWELLE"]
            )
    
            info_text = st.text_area(
                "Admin Infotext",
                value=st.session_state["admin_info_text"]
            )
    
    
            enddt = st.date_input(
                "Challenge-Enddatum",
                value=st.session_state["CHALLENGE_END_DATETIME"].date()
            )
    
            endtime = st.time_input(
                "End-Uhrzeit",
                value=st.session_state["CHALLENGE_END_DATETIME"].time()
            )
            
            startdt = st.date_input(
                "Challenge-Startdatum",
                value=st.session_state.get("CHALLENGE_START_DATETIME", datetime.now()).date()
            )
            starttime = st.time_input(
                "Start-Uhrzeit",
                value=st.session_state.get("CHALLENGE_START_DATETIME", datetime.now()).time()
            )
            
            teamziel_wochen = st.number_input(
            "Teamziel erreicht in bisherigen Wochen",
            min_value=0,
            max_value=GESAMT_WOCHEN,
            value=st.session_state.get("TEAMZIEL_WOCHEN_ERREICHT", 0),
            step=1
            )
            


            st.markdown("### 🏃 Aktive Teilnehmer auswählen (für diese Woche)")
            

            all_users_total = st.session_state.get("all_usernames", [])

            selected_users = st.multiselect(
                "Wer nimmt diese Woche teil?",
                options=all_users_total,
                default=st.session_state.get("active_users_this_week", all_users_total)
            )
    
            # ---------- Lotteriepreise ----------


            st.markdown("### 🎁 Lotterie-Wochenpreise konfigurieren")
    
            if "lotterie_preise" not in st.session_state:
                st.session_state["lotterie_preise"] = [
                    {"icon": "🎁", "text": "Tolles Buchpaket"},
                    {"icon": "🎁", "text": "Café-Gutschein"},
                    {"icon": "🎁", "text": "Cooles Gadget"},
                ]
    
            preise = st.session_state["lotterie_preise"]
    
            # Für jede vorhandene Kachel Admin-Eingaben
            for i, preis in enumerate(preise):
                col1, col2 = st.columns([1, 3])
                with col1:
                    icon = st.text_input(f"Icon für Preis {i+1}", value=preis["icon"], key=f"icon_{i}")
                with col2:
                    text = st.text_input(f"Text für Preis {i+1}", value=preis.get("text", ""), key=f"text_{i}")
                preise[i]["icon"] = icon
                preise[i]["text"] = text
    
            # Möglichkeit, weitere Preise hinzuzufügen
            if st.button("➕ Preis hinzufügen"):
                preise.append({"icon": "🎁", "text": "Neuer Preis"})
    
            # Möglichkeit, Preise zu löschen
            for i in reversed(range(len(preise))):
                if st.button(f"🗑 Preis {i+1} löschen"):
                    preise.pop(i)
                    break
    
            st.session_state["lotterie_preise"] = preise
    
            # Änderungen speichern
            if st.button("💾 Änderungen speichern"):
                st.session_state["WOCHENNUMMER"] = neue_woche
                st.session_state["WOCHENZIEL"] = ziel
                st.session_state["BATTERIE_SCHWELLE"] = batterie
                st.session_state["admin_info_text"] = info_text
                st.session_state["CHALLENGE_START_DATETIME"] = datetime.combine(startdt, starttime)
                st.session_state["CHALLENGE_END_DATETIME"] = datetime.combine(enddt, endtime)
                st.session_state["TEAMZIEL_WOCHEN_ERREICHT"] = teamziel_wochen
                st.session_state["lotterie_preise"] = preise
                st.session_state["active_users_this_week"] = selected_users
            
                save_settings({
                    "WOCHENNUMMER": st.session_state["WOCHENNUMMER"],
                    "WOCHENZIEL": st.session_state["WOCHENZIEL"],
                    "BATTERIE_SCHWELLE": st.session_state["BATTERIE_SCHWELLE"],
                    "CHALLENGE_START_DATETIME": st.session_state["CHALLENGE_START_DATETIME"].isoformat(),
                    "CHALLENGE_END_DATETIME": st.session_state["CHALLENGE_END_DATETIME"].isoformat(),
                    "TEAMZIEL_WOCHEN_ERREICHT": st.session_state["TEAMZIEL_WOCHEN_ERREICHT"],
                    "admin_info_text": st.session_state["admin_info_text"],
                    "lotterie_preise": st.session_state["lotterie_preise"],
                    "active_users_this_week": st.session_state["active_users_this_week"]
                })
            
                st.success("✅ Einstellungen gespeichert.")
                st.rerun()

    
        # -------------------------------------------------
        # TAB 2: LÄUFE & BEWEISBILDER
        # -------------------------------------------------
        with tab_runs:
            show_admin_runs_overview()

    
    admin_module()
 
def show():
    
    import streamlit as st
    import pandas as pd
    from datetime import datetime, timedelta, time
    import html
    import streamlit.components.v1 as components
    import textwrap
    from streamlit_autorefresh import st_autorefresh 
    import time as time_sleep
    import json
    import os
    import re
    
        
    page = st.session_state.get("page", "dashboard")
    
    if page == "dashboard":
        show_dashboard()

    elif page == "admin":
        show_admin_page()
