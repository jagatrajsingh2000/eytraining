# Model Output Comparison – Medical Note Risk Review

We compared three models to see how well they review medical notes.

## What we looked for:
- **Finding medical risks**: Finding issues that could hurt the patient.
- **Finding writing risks**: Finding missing facts or legal issues in the notes.
- **Leaving nothing out**: Making sure the review is complete.
- **Staying on topic**: Answering exactly what was asked.
- **Not making things up**: Staying only on the facts in the note.
- **Easy to read**: Keep it short and clear.

---

# 1. chest_pain_note_review (Opus)

**Score: 9.5 / 10**

### Good Points
- Finds all key health risks (only using one heart scan, missing heart protein test, vague discharge details).
- Finds all writing/legal risks (mentions of doctor being in a rush, missing blood pressure/pulse data, missing reason for sending the patient home).
- Clearly separates medical risks, writing risks, and next steps.
- Thinks deeply rather than just listing facts.

### Bad Points
- Makes a few guesses not in the note (like extra tests and pills).

---

# 2. patient_note_summary (Sonnet)

**Score: 8.8 / 10**

### Good Points
- Finds the missing heart protein test.
- Highlights missing facts (missing pulse/blood pressure, vague instructions).
- Well-organized and ranks issues by importance.

### Bad Points
- Guesses too much and adds numbers not in the text (like "up to 50% of heart attacks...").
- Goes outside of the note review.

---

# 3. patient_note_analysis (Haiku)

**Score: 7.5 / 10**

### Good Points
- Very short.
- Finds the missing heart protein test and vague instructions.
- Does not make things up (lowest risk of lying).

### Bad Points
- Misses many key issues (missing vital sign numbers, missing other possible diseases, missing reasons for discharge).
- Not complete enough.

---

# Final Ranking

| Rank | Model | Score |
| :--- | :--- | :--- |
| 🥇 1 | Opus (chest_pain_note_review) | 9.5/10 |
| 🥈 2 | Sonnet (patient_note_summary) | 8.8/10 |
| 🥉 3 | Haiku (patient_note_analysis) | 7.5/10 |

**Winner: Opus**
Opus wins because it finds the most risks, separates them clearly, and does not guess.