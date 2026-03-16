# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit-powered pet care planning assistant that helps busy pet owners stay on top of daily care tasks for one or more pets.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## Features

- **Owner & pet profiles** — Register an owner with daily available time and add multiple pets with name, species, and age.
- **Task management** — Create tasks with name, category, duration, priority (1–3), optional scheduled time (HH:MM), and frequency (once/daily/weekly).
- **Sort by time, priority, or weighted score** — View tasks sorted chronologically, by priority level, or by a composite score that factors in urgency and recurrence.
- **Filter tasks** — Narrow the task list by pet name, completion status (pending/done), or category.
- **Smart scheduling** — Generate a daily plan that packs the highest-priority tasks into the owner's available time budget.
- **Weighted scheduling** — An advanced mode that combines priority, urgency (days until due), and frequency into a single score for smarter ordering.
- **Next available slot finder** — Scans the day's schedule and finds the earliest gap that fits a task of a given duration.
- **Plan explanation** — See a written breakdown of why tasks were ordered the way they were and which tasks were skipped.
- **Conflict detection** — Warnings are shown when two tasks have overlapping scheduled times (across any pet).
- **Recurring tasks** — Daily and weekly tasks auto-create their next occurrence when marked complete.
- **Task completion** — Mark tasks done directly in the UI; recurring tasks show their next due date.
- **Data persistence** — All data is saved to `data.json` automatically and reloaded on app restart.
- **Professional UI** — Category emojis (🚶🍽️💊✂️🧩), color-coded priority labels (🔴🟡🟢), and status indicators (✅⏳) throughout.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run the CLI demo

```bash
python main.py
```

## Smarter Scheduling

PawPal+ includes several algorithmic features beyond basic priority ordering:

- **Sort by time** — Tasks with a scheduled time (`HH:MM`) are sorted chronologically. Unscheduled tasks appear last.
- **Sort by priority** — Tasks are ordered from highest priority (1) to lowest (3).
- **Weighted scoring** — Each task computes a `weighted_score()` combining `priority * 3.0`, `days_until_due * 2.0`, and a frequency bonus (`-1.0` for daily, `-0.5` for weekly). Lower score = scheduled first. This was implemented using Agent Mode to design the formula and integrate it across the Scheduler.
- **Next available slot** — `find_next_available_slot(duration)` scans from 07:00 to 21:00, skipping occupied intervals, and returns the first gap. Agent Mode was used to plan the gap-scanning algorithm and generate tests.
- **Filter tasks** — Filter the task list by pet name, completion status (`pending`/`done`), or category.
- **Recurring tasks** — Tasks can have a `frequency` of `"daily"` or `"weekly"`. When completed, a new instance is automatically created with the next due date (using `timedelta`).
- **Conflict detection** — The scheduler checks for overlapping time windows between scheduled tasks and returns human-readable warning messages instead of crashing.

## Architecture

See [uml_diagram.md](uml_diagram.md) for the full Mermaid.js class diagram. The system has four classes:

| Class | Responsibility |
|---|---|
| **Owner** | Stores owner info, manages pets, collects all tasks, handles JSON persistence |
| **Pet** | Stores pet profile, manages its own task list |
| **Task** | Represents a care activity with scheduling, recurrence, weighted scoring, and emoji formatting |
| **Scheduler** | Sorts, filters, detects conflicts, finds slots, generates plans (basic & weighted), and explains reasoning |

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

The test suite (32 tests) covers:

- **Core scheduling** — priority ordering, time budget limits, completed task exclusion
- **Sorting** — chronological ordering by `HH:MM`, unscheduled tasks placed last
- **Filtering** — by pet name, completion status, and category
- **Recurring tasks** — daily (+1 day), weekly (+7 days), one-time (no recurrence), attribute preservation
- **Conflict detection** — overlapping times, exact duplicate times, cross-pet conflicts, non-overlapping (no false positives)
- **Edge cases** — pet with no tasks, zero available time, `explain_plan()` before generating, `edit()` field updates, `get_summary()` format
- **Next available slot** — empty schedule, gap between tasks, no room available
- **Weighted scoring** — urgency preference, recurring bonus, weighted plan ordering
- **JSON persistence** — save/load round-trip, missing file handling
- **UI formatting** — category emojis, color-coded priority labels

**Confidence Level: 4/5**
The scheduler handles all expected workflows and edge cases reliably. The remaining star accounts for features not yet tested in production conditions, such as very large task lists or UI-layer integration tests.
