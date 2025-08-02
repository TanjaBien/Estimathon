import streamlit as st
import pandas as pd
import os
import math
import json

st.set_page_config(page_title="Estimathon", layout="wide")

# --- Configuration ---
ANSWER_FILE = "estimathon_answers.csv"
TEAM_FILE = "estimathon_teams.csv"

with open("questions.json", "r") as f:
    question_data = json.load(f)

QUESTIONS = [q["id"] for q in question_data["questions"]]
TRUE_ANSWERS = {q["id"]: q["answer"] for q in question_data["questions"]}
QUESTION_TEXT = {q["id"]: q["question"] for q in question_data["questions"]}
QUESTION_INFO = {q["id"]: q["info"] for q in question_data["questions"]}
MAX_ATTEMPTS_PER_TEAM = question_data["max_attempts"]

# --- Helper functions ---
def load_teams():
    if os.path.exists(TEAM_FILE):
        return pd.read_csv(TEAM_FILE)
    return pd.DataFrame(columns=["team"])

def load_answers():
    if os.path.exists(ANSWER_FILE):
        df = pd.read_csv(ANSWER_FILE)
        df["question"] = df["question"].astype(int)
        return df
    return pd.DataFrame(columns=["team", "question", "min", "max"])

def save_teams(df):
    df.to_csv(TEAM_FILE, index=False)

def save_answers(df):
    df.to_csv(ANSWER_FILE, index=False)

def calculate_score(team_df):
    good = 0
    ratios = {}

    for q in QUESTIONS:
        rows = team_df[team_df["question"] == q]
        if not rows.empty:
            last_row = rows.iloc[-1]
            min_val = last_row["min"]
            max_val = last_row["max"]
            true_val = TRUE_ANSWERS[q]

            if min_val <= true_val <= max_val:
                ratio = math.floor(max_val / min_val)
                good += 1
                ratios[q] = ratio

    score = (10 + sum(ratios.values())) * (2 ** (len(QUESTIONS) - good))
    return round(score, 2)

def get_status_display(team, history):
    status = {q: "" for q in QUESTIONS}
    true_vals = TRUE_ANSWERS

    if team not in history:
        return status

    for q in QUESTIONS:
        attempts = history[team].get(q, [])
        attempts = list(dict.fromkeys(attempts))
        attempt_list = []
        for min_val, max_val in attempts:
            if min_val <= true_vals[q] <= max_val:
                ratio = math.floor(max_val / min_val)
                attempt_list.append(str(ratio))
            else:
                attempt_list.append("✖")
        status[q] = " ".join(attempt_list)
    return status


def rebuild_session_state_from_csv():
    answers_df = load_answers()
    history = {}
    counts = {}

    for team in answers_df["team"].unique():
        team_df = answers_df[answers_df["team"] == team]
        history[team] = {}
        for q in team_df["question"].unique():
            q_df = team_df[team_df["question"] == q]
            attempts = list(zip(q_df["min"], q_df["max"]))
            history[team][q] = attempts
            counts[team] = counts.get(team, 0) + len(attempts)

    st.session_state.submission_history = history
    st.session_state.submission_counts = counts

if "submission_history" not in st.session_state or "submission_counts" not in st.session_state:
    rebuild_session_state_from_csv()

if "submission_counts" not in st.session_state:
    # team -> count of total submissions (or per question if you want)
    st.session_state.submission_counts = {}

# --- UI: Add Teams ---
st.sidebar.header("👥 Team Management")
teams_df = load_teams()
new_team = st.sidebar.text_input("New Team").strip().upper()
if st.sidebar.button("➕ Add Team"):
    if new_team and new_team not in teams_df["team"].values:
        teams_df = pd.concat([teams_df, pd.DataFrame([{"team": new_team}])], ignore_index=True)
        save_teams(teams_df)
        st.sidebar.success(f"Team {new_team} hinzugefügt.")
    else:
        st.sidebar.warning("Invalid or already existing team.")

# --- UI: Delete Session ---
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Delete Session"):
    # Delete the team file
    if os.path.exists(TEAM_FILE):
        os.remove(TEAM_FILE)

    # Optionally also delete answers
    if os.path.exists(ANSWER_FILE):
        os.remove(ANSWER_FILE)

    # Clear session state history & counts
    st.session_state.submission_history = {}
    st.session_state.submission_counts = {}

    st.success("All teams and answers deleted.")
    st.rerun()

# --- UI: Submission Form ---
st.header("📥 Submit Answer")

answers_df = load_answers()

team_key = "team_key"
min_key = "min_key"
max_key = "max_key"

with st.form("submit_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        team_input = st.text_input("Teamkürzel", key=team_key).strip().upper()
    with col2:
        question_input = st.selectbox("Fragenummer", QUESTIONS)
    with col3:
        min_input = st.number_input("Minimum", min_value=0, step=1, format="%d", key=min_key)
    with col4:
        max_input = st.number_input("Maximum", min_value=0, step=1, format="%d", key=max_key)
    submitted = st.form_submit_button("✅ Save Submission")

if submitted:
    teams_df = load_teams()
    if team_input not in teams_df["team"].values:
        st.error(f"Team {team_input} does not exist. Please add it first.")
    elif min_input <= 0 or max_input <= 0 or max_input < min_input:
        st.error("Invalid interval.")
    else:
        # Check submission limit
        counts = st.session_state.submission_counts
        current_count = counts.get(team_input, 0)
        if current_count >= MAX_ATTEMPTS_PER_TEAM:
            st.error(f"Maximum number of {MAX_ATTEMPTS_PER_TEAM} submissions reached for team.")
        else:
            # Save last submission to CSV (overwrite old)
            answers_df = load_answers()
            new_row = pd.DataFrame([{
                "team": team_input,
                "question": question_input,
                "min": min_input,
                "max": max_input
            }])
            answers_df = pd.concat([answers_df, new_row], ignore_index=True)
            save_answers(answers_df)
            rebuild_session_state_from_csv()


            # Append to session history
            history = st.session_state.submission_history
            if team_input not in history:
                history[team_input] = {}
            if question_input not in history[team_input]:
                history[team_input][question_input] = []
            history[team_input][question_input].append((min_input, max_input))

            # Update submission count
            counts[team_input] = current_count + 1
            st.session_state.submission_counts = counts

            st.success(f"Answer for team {team_input}, question {question_input} saved!")
            for key in ["team_input", "min_input", "max_input"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# --- UI: Scoreboard ---
st.header("📊 Live-Scoreboard")

teams_df = load_teams()
if teams_df.empty:
    st.info("No existing teams yet.")
else:
    rows = []
    for team in sorted(teams_df["team"].unique()):
        team_answers = answers_df[answers_df["team"] == team]
        score = calculate_score(team_answers)
        status = get_status_display(team, st.session_state.submission_history)
        row = {"Team": team}
        for q in QUESTIONS:
            row[f"Q{q}"] = status[q]
        row["Punkte"] = score
        rows.append(row)

    scoreboard_df = pd.DataFrame(rows)
    scoreboard_df = scoreboard_df.sort_values("Punkte", ascending=False)
    st.dataframe(scoreboard_df.reset_index(drop=True), use_container_width=True)

