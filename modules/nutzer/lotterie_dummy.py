import streamlit as st
import datetime as dt
from streamlit_autorefresh import st_autorefresh

def show():

    # Seite alle 1 Sekunde aktualisieren
    st_autorefresh(interval=1000, key="lotterie_autorefresh")

    def show_lotterie_page():
        # ---------- Globale Styles ----------
        st.markdown("""
        <style>
        html, body, .main, [data-testid="stAppViewContainer"] { background:#011848 !important; color:#fff;}
        .dashboard-tiles-bar { display:flex; flex-wrap:wrap; gap:16px; justify-content:center; margin-bottom:25px;}
        .dashboard-tile { flex:0 0 150px; min-width:120px; border-radius:13px; padding:18px; display:flex; flex-direction:column; align-items:center; justify-content:center;
                          font-family:sans-serif; font-weight:700; color:#fff; box-shadow:0 8px 33px #01184844,0 1px 0 #fff2 inset; transition: transform .2s ease, box-shadow .2s ease;}
        .dashboard-tile:hover { transform:translateY(-4px); box-shadow:0 14px 34px rgba(0,0,0,0.45);}
        .tile-title { font-size:1.5em; margin-bottom:6px;}
        .tile-content { font-size:1em; text-align:center;}
        .tile-blue-1 { background:#173985 !important; }
        .tile-blue-2 { background:#24428a !important; }
        .tile-blue-3 { background:#082053 !important; }
        .countdown-box { text-align:center; font-size:1.4em; font-weight:700; margin-bottom:25px; }
        </style>
        """, unsafe_allow_html=True)

        # ---------- Countdown ----------
        target_datetime = dt.datetime(2026, 1, 12, 20, 0, 0)
        now = dt.datetime.now()
        remaining = target_datetime - now
        if remaining.total_seconds() > 0:
            days, remainder = divmod(remaining.total_seconds(), 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            countdown_text = f"⏳ Die Lotterie für Woche 1 startet in {int(days)} Tagen, {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}. Zu gegebener Zeit kannst du hier dann die Lotterie verfolgen."
        else:
            countdown_text = "🎉 Die Lotterie ist jetzt live!"

        st.markdown(f'<div class="countdown-box">{countdown_text}</div>', unsafe_allow_html=True)

        # ---------- Lotterie-Kacheln ----------
        # Hier deine Kachel-Funktion einfügen, falls gewünscht
        # show_lotterie_kacheln()

        # ---------- Zurück Button ----------
        if st.button("Zurück zum Dashboard", key="back_to_dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()

    show_lotterie_page()
            
