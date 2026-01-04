import streamlit as st
import os
import json
import re
import hashlib
import time

USERS_FILE = "data/users.json"
PW_MAXLEN = 64
PW_MINLEN = 6

def set_streamlit_theme():
    st.markdown(
        """
        <style>
        html, body, .stApp {
            height: 100% !important;
            min-height: 100vh !important;
            background: #0d2547 !important;
        }
        .stApp {
            background-color: #0d2547 !important;
            color: #ffffff !important;
            min-height: 100vh !important;
            box-sizing: border-box;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
        }
        label, .stTextInput > div > input, .stSelectbox > label {
            color: #ffffff !important;
        }
        .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stSelectbox [data-baseweb="select"] {
            background-color: #192d4c !important;
            color: #ffffff !important;
            border-radius: 4px !important;
            border: 1px solid #2a4167 !important;
        }
        .stSelectbox [aria-selected="true"] {
            background-color: #12408f !important;
            color: #fff !important;
        }
        .stButton button, .stButton button:disabled {
            background-color: #12408f !important;
            color: #ffffff !important;
            border-radius: 14px !important;
            border: none !important;
            /* PATCH: Kleiner machen */
            min-height: 34px !important;
            font-size: 0.98em !important;
            padding: 0 1.0em !important;
            margin-bottom: 10px !important;
            width: 100% !important;
            max-width: 400px;
        }
        .stButton button:focus {
            outline: 3px solid #24a1f2 !important;
        }
        .stButton button:hover:enabled {
            background-color: #163b7e !important;
            color: #ffffff !important;
        }
        .stAlert, .stMarkdown>div[role="alert"] {
            background-color: #0d2547 !important;
            color: #fff !important;
            border-radius: 8px !important;
        }
        .stAlert[data-testid="stAlertError"] {
            background-color: #f8002f !important;
            color: #fff !important;
            border-radius: 10px !important;
            border: 2px solid #ff5090 !important;
        }
        .stNotificationContent {
            background-color: #123058 !important;
            color: #fff !important;
            border-radius: 8px !important;
        }
        hr {
            border: 1px solid #3a4468 !important;
        }
        .login-reg-divider {
            border-top: 1px solid #3a4468;
            margin: 32px 0 24px 0;
        }
        .sub-header {
            font-size: 1.4rem;
            font-weight: 600;
            color: #fff !important;
            margin-bottom: 0.7rem;
            margin-top: 1.6rem;
        }
        .stHelp {
            color: #fff !important;
        }
        .custom-label {
            font-weight: 600;
            color: #ffffff !important;
            margin-bottom: 0.3em;
            display: block;
        }
        .custom-section {
            margin-bottom: 1.7em;
        }
        .custom-form-field {
            margin-bottom: 0.6em;
        }
        .stTextInput input::placeholder, .stSelectbox input::placeholder {
            color: #e9edef !important;
            opacity: 1 !important;
        }
        .stSelectbox [data-baseweb="select"] input, .stSelectbox [data-baseweb="select"] div {
            color: #fff !important;
        }
        .stMarkdown .stAlert {
            background-color: #0d2547 !important;
            color: #fff !important;
        }
        input, textarea, select {
            color: #fff !important;
            background-color: #192d4c !important;
        }
        .css-1n76uvr,
        .stAlert, .stMarkdown>div[role="alert"] {
            color: #fff !important;
        }
        [data-testid="stHeader"], [data-testid="stHeader"] > div:first-child {
            display: none !important;
            background: none !important;
            box-shadow: none !important;
            pointer-events: none !important;
            height: 0 !important;
            min-height: 0 !important;
        }
        @media (max-width: 700px) {
            .stApp {
                padding: 0.6em !important;
            }
            .stTextInput input, .stButton button, .stSelectbox div, .stSelectbox input {
                font-size: 1.04em !important;
                min-height: 30px !important;
            }
            .stButton button {
                width: 100% !important;
                min-width: 0 !important;
                margin-bottom: 1em !important;
                padding: 0 1.0em !important;
                max-width: 400px;
            }
            .stTextInput, .stSelectbox {
                width: 100% !important;
                max-width: 400px;
            }
            .stForm {
                padding: 0 !important;
            }
            .sub-header, .custom-label {
                font-size: 1.07em !important;
            }
            .mobile-btn-row {
                display: flex;
                flex-direction: column;
                gap: 14px;
                margin-bottom: 1.3em !important;
                margin-top: 0.2em !important;
                width: 100%;
                max-width:400px;
            }
            /* PATCH: Die Box für Register entfernen */
            .mobile-form-container {
                padding: 0 !important;
                background: none !important;
                box-shadow: none !important;
                border-radius: 0 !important;
                margin: 0 !important;
            }
        }
        @media (max-width: 480px) {
            body, .stApp, .stTextInput input, .stButton button {
                font-size: 0.98em !important;
            }
            .sub-header, .custom-label {
                font-size: 0.96em !important;
            }
            .stTextInput input, .stSelectbox input {
                font-size: 0.93em !important;
            }
            .mobile-btn-row {
                gap: 10px;
            }
            .mobile-form-container {
                padding: 0 !important;
                max-width: 100vw !important;
            }
        }
        [data-testid="stDecoration"] {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            background: none !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def validate_users_file():
    if not os.path.exists(USERS_FILE):
        return True
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        if not isinstance(users, dict):
            return False
        for username, pw in users.items():
            if not isinstance(username, str) or not isinstance(pw, str):
                return False
        return True
    except Exception:
        return False

def load_users():
    if not validate_users_file():
        return None, "Beim Zugriff auf die Zugangsdaten ist ein Problem aufgetreten. Bitte informiere das Orga-Team (info@tsv-gerabronn.de) oder probiere es später erneut."
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
            if isinstance(users, dict):
                return users, None
            else:
                return {}, None
        except json.JSONDecodeError:
            return None, "Die Zugangsdaten sind unlesbar. Melde dich bitte beim Orga-Team (info@tsv-gerabronn.de)."
        except Exception:
            return {}, "Die Zugangsdaten konnten nicht geladen werden. Bitte versuche es erneut."
    else:
        return {}, None

def save_users(users):
    try:
        lockfile = USERS_FILE + ".lock"
        t0 = time.time()
        while os.path.exists(lockfile):
            if time.time() - t0 > 3:
                return False, "Derzeit ist eine Registrierung nicht möglich. Bitte versuche es gleich erneut."
            time.sleep(0.1)
        with open(lockfile, "w") as f:
            f.write("locked\n")
        tmpfile = USERS_FILE + ".tmp"
        with open(tmpfile, "w") as f:
            json.dump(users, f)
        os.replace(tmpfile, USERS_FILE)
        os.remove(lockfile)
        return True, None
    except Exception as e:
        try:
            if os.path.exists(lockfile):
                os.remove(lockfile)
        except Exception:
            pass
        return False, f"Dein Zugang konnte nicht gespeichert werden. Bitte versuche es erneut. ({str(e)})"

def username_valid(username, users=None):
    if not username or len(username) < 3:
        return False, "Dein Benutzername muss mindestens 3 Zeichen lang sein."
    if len(username) > 16:
        return False, "Dein Benutzername darf maximal 16 Zeichen haben."
    if re.search(r"\s", username):
        return False, "Bitte verwende keine Leerzeichen im Benutzernamen."
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", username):
        return False, "Im Benutzernamen sind nur Buchstaben, Zahlen, _ - . erlaubt."
    if users:
        lowered = username.lower()
        for u in users:
            if u.lower() == lowered:
                return False, "Dieser Benutzername ist bereits vergeben."
    return True, ""

def password_valid(password):
    if not password or len(password) < PW_MINLEN:
        return False, f"Dein Passwort muss mindestens {PW_MINLEN} Zeichen lang sein.\n{password_hint()}"
    if len(password) > PW_MAXLEN:
        return False, f"Dein Passwort darf maximal {PW_MAXLEN} Zeichen haben.\n{password_hint()}"
    if " " in password:
        return False, "Bitte verwende keine Leerzeichen im Passwort.\n" + password_hint()
    missing = []
    if not re.search(r"[A-Z]", password):
        missing.append("einen Großbuchstaben")
    if not re.search(r"[a-z]", password):
        missing.append("einen Kleinbuchstaben")
    if not re.search(r"[0-9]", password):
        missing.append("eine Zahl")
    if not re.search(r"[\W_]", password):
        missing.append("ein Sonderzeichen")
    if missing:
        return False, "Dein Passwort braucht mindestens " + ", ".join(missing) + ".\n" + password_hint()
    return True, ""

def password_hint():
    return "Erlaubt: Mind. 6 Zeichen, Groß-/Kleinschreibung, Zahl, Sonderzeichen (!?@#...). Keine Leerzeichen."

def canonical_username(users, username):
    if not isinstance(users, dict):
        return None
    lowered = username.lower()
    for k in users:
        if k.lower() == lowered:
            return k
    return None

def login_check(users, username, password):
    real_username = canonical_username(users, username)
    if real_username and users[real_username] == hash_password(password):
        return real_username
    return None

def reset_state_keys(*keys):
    for key in keys:
        if key in st.session_state:
            try:
                del st.session_state[key]
            except Exception:
                pass

def switch_to_register(usernames_list):
    st.session_state["page"] = "register"
    reset_state_keys("login_error", "reg_error", "login_submit_triggered", "reg_submit_triggered")

def switch_to_login(usernames_list):
    st.session_state["page"] = "login"
    reset_state_keys("login_error", "reg_error", "login_submit_triggered", "reg_submit_triggered")

def safe_rerun(force_reload=True):
    st.rerun()

def _generate_key(base, context):
    return f"{base}__{context}"

def show_login(users, usernames, file_error=None, reg_blocked=False):
    st.header("Laufchallenge TSV Gerabronn")
    if not isinstance(usernames, list) or not all(isinstance(u, str) for u in usernames):
        usernames = []
    if file_error:
        st.error(file_error or "Fehler beim Laden der Zugangsdaten.")
        st.info(
            "Bitte lade die Seite neu. Sollte es weiterhin nicht funktionieren oder der Fehlertext auf einen Problemfall hinweisen, wende dich an das Orga-Team unter info@tsv-gerabronn.de."
        )
        st.markdown('<div class="mobile-btn-row">', unsafe_allow_html=True)
        if st.button("Seite neu laden"):
            keys = list(st.session_state.keys())
            for key in keys:
                if key != "page":
                    try:
                        del st.session_state[key]
                    except Exception:
                        pass
            safe_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if reg_blocked:
        st.error("Ein Login ist im Moment nicht möglich.")
        return

    if not usernames or len(usernames) == 0:
        st.info(
            "Willkommen! Es wurde noch kein Benutzer angelegt.\n\n"
            "Klicke unten auf \"Neu registrieren\" und lege einen Benutzernamen und ein Passwort fest. "
            "Anschließend können sich auch andere anmelden."
        )
        st.markdown('<div class="mobile-btn-row">', unsafe_allow_html=True)
        if st.button("Neu registrieren", key="goto_reg_btn_from_login_alone"):
            switch_to_register(usernames)
            safe_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    sb_key_user = _generate_key("login_username_select", "login")
    sb_key_pw = _generate_key("login_pw", "login")
    login_error = st.session_state.get("login_error", "")

    current_user_value = st.session_state.get(sb_key_user)
    default_index = 0
    valid_user_index = default_index

    if usernames:
        try:
            if current_user_value in usernames:
                valid_user_index = usernames.index(current_user_value)
            else:
                valid_user_index = 0
                st.session_state[sb_key_user] = usernames[0]
        except Exception:
            valid_user_index = 0
            st.session_state[sb_key_user] = usernames[0]
    else:
        current_user_value = ""
        valid_user_index = 0

    with st.form("login_form", clear_on_submit=False):
        st.markdown('<div class="custom-label">Benutzername</div>', unsafe_allow_html=True)
        login_username = st.selectbox(
            "Benutzername",
            usernames if usernames else ["Bitte registrieren"],
            index=valid_user_index,
            key=sb_key_user,
            label_visibility="collapsed",
            format_func=lambda u: u,
            disabled=(not usernames)
        )
        st.markdown('<div class="custom-label">Passwort</div>', unsafe_allow_html=True)
        login_pw = st.text_input(
            "Passwort",
            "",
            max_chars=PW_MAXLEN,
            type="password",
            key=sb_key_pw,
            label_visibility="collapsed",
            placeholder="Passwort eingeben",
            disabled=(not usernames)
        )

        if _generate_key("login_input_last", "login") not in st.session_state:
            st.session_state[_generate_key("login_input_last", "login")] = ("", "")
        last_username, last_pw = st.session_state[_generate_key("login_input_last", "login")]
        if (login_username != last_username or login_pw != last_pw) and login_error:
            st.session_state["login_error"] = ""
            login_error = ""
        st.session_state[_generate_key("login_input_last", "login")] = (login_username, login_pw)

        submit_btn = st.form_submit_button("Anmelden", disabled=(not usernames))
        if submit_btn:
            err = ""
            if not login_username or not login_pw or login_username == "Bitte registrieren":
                err = "Bitte gib deinen Benutzernamen und dein Passwort ein."
            elif canonical_username(users, login_username) is None:
                err = "Diesen Benutzernamen gibt es nicht."
            elif not login_check(users, login_username, login_pw):
                err = "Das eingegebene Passwort ist nicht korrekt."
            if err:
                st.session_state["login_error"] = err
                login_error = err
            else:
                real_user = canonical_username(users, login_username)
                st.session_state["user"] = real_user
                st.session_state["page"] = "dashboard"
                reset_state_keys("login_error", "reg_error", "login_submit_triggered", "reg_submit_triggered", _generate_key("login_input_last", "login"))
                safe_rerun()
                return

    if login_error:
        st.error(login_error)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("Noch keinen Account?")
    st.markdown('<div class="mobile-btn-row">', unsafe_allow_html=True)
    if st.button("Neu registrieren", key="goto_reg_btn_from_login_bottom"):
        switch_to_register(usernames)
        safe_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_registration_first_user(users, usernames):
    st.info(
        "Du bist der erste Benutzer auf dieser Seite. Nach deiner Anmeldung können sich weitere Nutzer durch Klick auf \"Neu registrieren\" anmelden.\n\n"
        "Teile den Link gerne mit deinem Team!"
    )
    reg_error = st.session_state.get("reg_error", "")
    prefix = "register_first"

    # PATCH: mobile-form-container Box entfernt (Block entfernt und Felder einzeln)
    with st.form("register_first_user_form", clear_on_submit=False):
        st.markdown('<div class="custom-label">Neuer Benutzername</div>', unsafe_allow_html=True)
        reg_username = st.text_input(
            "Benutzername",
            "",
            max_chars=16,
            key=_generate_key("register_username", prefix),
            label_visibility="collapsed",
            placeholder="Benutzername"
        )
        st.markdown('<div class="custom-label">Passwort</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.91em;color:#efef91;margin-bottom:1em">'+password_hint()+'</div>',unsafe_allow_html=True)
        reg_pw1 = st.text_input(
            "Passwort",
            "",
            max_chars=PW_MAXLEN,
            key=_generate_key("register_pw1", prefix),
            type="password",
            label_visibility="collapsed",
            placeholder="Passwort"
        )
        st.markdown('<div class="custom-label">Passwort bestätigen</div>', unsafe_allow_html=True)
        reg_pw2 = st.text_input(
            "Passwort bestätigen",
            "",
            max_chars=PW_MAXLEN,
            key=_generate_key("register_pw2", prefix),
            type="password",
            label_visibility="collapsed",
            placeholder="Passwort bestätigen"
        )

        last_input_key = _generate_key("reg_input_last", prefix)
        if last_input_key not in st.session_state:
            st.session_state[last_input_key] = ("", "", "")
        last_username, last_pw1, last_pw2 = st.session_state[last_input_key]
        if (reg_username != last_username or reg_pw1 != last_pw1 or reg_pw2 != last_pw2) and reg_error:
            st.session_state["reg_error"] = ""
            reg_error = ""
        st.session_state[last_input_key] = (reg_username, reg_pw1, reg_pw2)

        submit_btn = st.form_submit_button("Registrieren")
        if submit_btn:
            user_ok, user_msg = username_valid(reg_username, users)
            pw_ok, pw_msg = password_valid(reg_pw1)
            err = ""
            if not reg_username or not reg_pw1 or not reg_pw2:
                err = "Bitte fülle alle Felder aus."
            elif not user_ok:
                err = user_msg
            elif canonical_username(users, reg_username) is not None:
                err = "Dieser Benutzername ist bereits vergeben."
            elif not pw_ok:
                err = pw_msg
            elif reg_pw1 != reg_pw2:
                err = "Die Passwörter stimmen nicht überein."
            if err:
                st.session_state["reg_error"] = err
                reg_error = err
            else:
                users[reg_username] = hash_password(reg_pw1)
                success, save_err = save_users(users)
                if not success:
                    fgerr = save_err if save_err else "Fehler beim Speichern deiner Registrierung."
                    st.session_state["reg_error"] = fgerr
                    reg_error = fgerr
                else:
                    st.session_state["user"] = reg_username
                    st.session_state["page"] = "dashboard"
                    reset_state_keys("reg_error", "login_error", "reg_submit_triggered", _generate_key("register_pw1", prefix), _generate_key("register_pw2", prefix), last_input_key)
                    safe_rerun()
                    return

    if reg_error:
        st.error(reg_error)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="mobile-btn-row">', unsafe_allow_html=True)
    if st.button("Zurück zum Login", key="reg_firstuser_back"):
        switch_to_login(usernames)
        safe_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def show_register(users, usernames, reg_blocked=False):
    st.header("Laufchallenge TSV Gerabronn")
    st.markdown('<div class="sub-header">Registrierung</div>', unsafe_allow_html=True)
    if reg_blocked:
        st.error("Eine Registrierung ist im Moment nicht möglich.")
        st.markdown('<div class="mobile-btn-row">', unsafe_allow_html=True)
        if st.button("Zurück zum Login", key="reg_blocked_back_btn"):
            switch_to_login(usernames)
            safe_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if isinstance(users, dict) and len(users) == 0:
        show_registration_first_user(users, usernames)
        return

    if not isinstance(usernames, list) or not all(isinstance(u, str) for u in usernames):
        usernames = []

    reg_error = st.session_state.get("reg_error", "")
    prefix = "register"

    # PATCH: mobile-form-container Box entfernt (Block entfernt und Felder einzeln)
    with st.form("register_user_form", clear_on_submit=False):
        st.markdown('<div class="custom-label">Wunsch-Benutzername</div>', unsafe_allow_html=True)
        reg_username = st.text_input(
            "Benutzername",
            "",
            max_chars=16,
            key=_generate_key("register_username", prefix),
            label_visibility="collapsed",
            placeholder="Benutzername"
        )
        st.markdown('<div class="custom-label">Passwort</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.91em;color:#efef91;margin-bottom:1em">'+password_hint()+'</div>',unsafe_allow_html=True)
        reg_pw1 = st.text_input(
            "Passwort",
            "",
            max_chars=PW_MAXLEN,
            key=_generate_key("register_pw1", prefix),
            type="password",
            label_visibility="collapsed",
            placeholder="Passwort"
        )
        st.markdown('<div class="custom-label">Passwort bestätigen</div>', unsafe_allow_html=True)
        reg_pw2 = st.text_input(
            "Passwort bestätigen",
            "",
            max_chars=PW_MAXLEN,
            key=_generate_key("register_pw2", prefix),
            type="password",
            label_visibility="collapsed",
            placeholder="Passwort bestätigen"
        )

        last_input_key = _generate_key("reg_input_last", prefix)
        if last_input_key not in st.session_state:
            st.session_state[last_input_key] = ("", "", "")
        last_username, last_pw1, last_pw2 = st.session_state[last_input_key]
        if (reg_username != last_username or reg_pw1 != last_pw1 or reg_pw2 != last_pw2) and reg_error:
            st.session_state["reg_error"] = ""
            reg_error = ""
        st.session_state[last_input_key] = (reg_username, reg_pw1, reg_pw2)

        submit_btn = st.form_submit_button("Account anlegen")
        if submit_btn:
            user_ok, user_msg = username_valid(reg_username, users)
            pw_ok, pw_msg = password_valid(reg_pw1)
            err = ""
            if not reg_username or not reg_pw1 or not reg_pw2:
                err = "Bitte fülle alle Felder aus."
            elif not user_ok:
                err = user_msg
            elif canonical_username(users, reg_username) is not None:
                err = "Dieser Benutzername ist bereits vergeben."
            elif not pw_ok:
                err = pw_msg
            elif reg_pw1 != reg_pw2:
                err = "Die Passwörter stimmen nicht überein."
            if err:
                st.session_state["reg_error"] = err
                reg_error = err
            else:
                users[reg_username] = hash_password(reg_pw1)
                success, save_err = save_users(users)
                if not success:
                    fgerr = save_err if save_err else "Fehler beim Speichern deiner Registrierung."
                    st.session_state["reg_error"] = fgerr
                    reg_error = fgerr
                else:
                    st.session_state["user"] = reg_username
                    st.session_state["page"] = "dashboard"
                    reset_state_keys("reg_error", "login_error", "reg_submit_triggered", _generate_key("register_pw1", prefix), _generate_key("register_pw2", prefix), last_input_key)
                    safe_rerun()
                    return
    if reg_error:
        st.error(reg_error)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div class="mobile-btn-row">', unsafe_allow_html=True)
    if st.button("Zurück zum Login", key="register_back_btn"):
        switch_to_login(usernames)
        safe_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

#def show_home():
#    user = st.session_state.get("user")
#    st.header("Willkommen zur Laufchallenge TSV Gerabronn")
#    if user:
#        st.success(f"Willkommen, {user}! Du bist jetzt eingeloggt.")
#    st.markdown('<div style="margin-top:2em"></div>', unsafe_allow_html=True)
#    st.markdown('<div class="mobile-btn-row">', unsafe_allow_html=True)
#    if st.button("Abmelden", key="logout_btn_home"):
#        do_logout()
#        safe_rerun()
#    st.markdown('</div>', unsafe_allow_html=True)

def do_logout():
    st.session_state["user"] = None
    st.session_state["page"] = "login"
    reset_state_keys(
        "login_error", "reg_error", "reg_submit_triggered", "login_submit_triggered",
        _generate_key("register_pw1", "register"), _generate_key("register_pw2", "register"),
        _generate_key("register_pw1", "register_first"), _generate_key("register_pw2", "register_first"),
        _generate_key("reg_input_last", "register"), _generate_key("reg_input_last", "register_first"),
        _generate_key("login_input_last", "login"),
        _generate_key("login_username_select", "login"), _generate_key("login_pw", "login")
    )

def main(for_app=True):
    """
    for_app=True → wird von app.py aufgerufen, nur Login/Register anzeigen, kein Home/Dashboard
    for_app=False → standalone, wie bisher, inklusive Home (z.B. zum Testen)
    """
    set_streamlit_theme()
    users, file_error = load_users()
    reg_blocked = users is None or (file_error is not None)

    # Benutzerliste vorbereiten
    usernames = []
    if users and isinstance(users, dict):
        usernames_lc = set()
        for k in sorted(users.keys(), key=lambda u: u.lower()):
            if isinstance(k, str) and k.strip() != "" and k.lower() not in usernames_lc:
                usernames.append(k)
                usernames_lc.add(k.lower())
    st.session_state["all_usernames"] = usernames

    # Session Defaults nur setzen, falls noch nicht vorhanden
    if "page" not in st.session_state:
        st.session_state["page"] = "login"
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "login_error" not in st.session_state:
        st.session_state["login_error"] = ""
    if "reg_error" not in st.session_state:
        st.session_state["reg_error"] = ""

    # Routing für Login/Register
    page = st.session_state.get("page", "login")

    if page=="register":
        show_register(users if isinstance(users, dict) else {}, usernames, reg_blocked=reg_blocked)
    else:
        show_login(users if isinstance(users, dict) else {}, usernames, file_error, reg_blocked=reg_blocked)





if __name__ == "__main__":
    main()
