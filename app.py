#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
from modules.login import main as login_main
from modules.nutzer import dashboard_selbst_gemacht_v02 as nutzer_dashboard
from modules.nutzer import lotterie_dummy as lotterie_module
from datetime import datetime
    


# ---------- SESSION DEFAULTS ----------
if "user" not in st.session_state:
    st.session_state["user"] = None

if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"


# ---------- LOGIN ----------
if st.session_state["user"] is None:
    login_main()
    st.stop()


# ---------- PAGE ROUTING ----------
if st.session_state["page"] == "dashboard":
    nutzer_dashboard.show_dashboard()

elif st.session_state["page"] == "admin":
    nutzer_dashboard.show_admin_page()

elif st.session_state["page"] == "lotterie":
    lotterie_module.show()

