# Estimaton
App for automatic evaluation of an Estimathon (Estimate-Marathon ;) ). It allows teams to enter their answers using a team code and question number, along with a minimum and maximum value that they believe contains the true answer. A live scoreboard shows the performance of each team.

## How does it work

- Every teams submits answers using:
  - A **team code**
  - A **question number**
  - A **minimum** and **maximum** interval
- The app checks whether the true answer lies within the submitted interval.
- A **scoreboard** displays:
  - Each team's results for every question (ratios or ✖ for wrong guesses)
  - Total score based on the number and quality of correct answers
- Only the **latest submission per question** counts for the score.
- The number of maximum attempts is limited. 
- All previous attempts are shown in the table for transparency.
- Admin can add teams dynamically.

## Scoring Rules

- A correct answer is one where the true value lies within the submitted interval.
- For each correct interval, a **ratio** is calculated:  
  $$
  \text{ratio} = \left\lfloor \frac{\text{max}}{\text{min}} \right\rfloor
  $$
- The total score is calculated as:
  $$
  \text{score} = \left(10 + \sum_{\text{correct}} \text{ratio}\right) \cdot 2^{\text{#question} - \text{#correctly questions}}
  $$

## Usage
0. configure your own `questions.json` file 
1. Start the app: `streamlit run estimathon_app.py`
2. Submit answers using the form:
   - `Team Code`
   - `Question Number`
   - `Min`
   - `Max`
3. View the live scoreboard below the form.

## Example

| Team   | Q1     | Q2     | Q3     | Total Score |
|--------|--------|--------|--------|-------------|
| Alpha  | ✖ 3    | 2      | ✖ ✖ 4  | 1260        |
| Beta   | 2      | ✖      | 5      | 2340        |

## Requirements

- Python 3.8+
- Streamlit
- Pandas

Install dependencies with:

```bash
pip install streamlit pandas
```

## Todos
- [ ] Secrete team code and team name
- [ ] Display all questions option
- [ ] Display all answers option