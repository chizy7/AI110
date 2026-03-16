# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML design included four classes, each with a clear responsibility:

- **Owner** — Stores the pet owner's name and how many minutes they have available per day for pet care. Responsible for managing daily availability.
- **Pet** — Stores pet profile information (name, species, age) and holds a reference to its Owner. Responsible for producing a readable summary of the pet.
- **Task** — Represents a single care activity (e.g., walk, feeding, meds). Holds the task name, category, duration in minutes, and a priority level (1 = highest). Responsible for self-editing and producing a string summary.
- **Scheduler** — The core engine. Collects all tasks and the owner's available time, then generates a prioritized daily plan that fits within the time budget. Also responsible for explaining why the plan was ordered the way it was.

**Core User Actions:**

1. **Register a pet and owner profile** — The user can enter basic information about themselves (name, time available per day) and their pet (name, species, age) so the system knows who it is planning for.

2. **Add and edit care tasks** — The user can create pet care tasks (such as walks, feeding, medication, grooming, or enrichment), specifying at minimum a duration and priority level for each task. They can also edit or remove existing tasks as needs change.

3. **Generate and view a daily care plan** — The user can request a daily schedule that arranges their tasks based on available time and priority. The system displays the resulting plan clearly and explains why it ordered tasks the way it did (e.g., higher-priority tasks are scheduled first, tasks that exceed available time are flagged or deferred).

**Building Blocks (Main Objects):**

### 1. Owner
- **Attributes:**
  - `name` (str) — the pet owner's name
  - `available_time` (int) — total minutes the owner has available per day for pet care
- **Methods:**
  - `set_available_time(minutes)` — update how much time the owner has on a given day

### 2. Pet
- **Attributes:**
  - `name` (str) — the pet's name
  - `species` (str) — type of animal (dog, cat, etc.)
  - `age` (int) — the pet's age in years
  - `owner` (Owner) — reference to the pet's owner
- **Methods:**
  - `get_summary()` — return a short description of the pet (e.g., "Bella, 3-year-old dog")

### 3. Task
- **Attributes:**
  - `name` (str) — description of the task (e.g., "Morning walk")
  - `category` (str) — type of task (walk, feeding, meds, grooming, enrichment)
  - `duration` (int) — how long the task takes in minutes
  - `priority` (int) — importance level (1 = highest, 3 = lowest)
- **Methods:**
  - `edit(name, duration, priority)` — update the task's details
  - `__str__()` — return a readable summary of the task

### 4. Scheduler
- **Attributes:**
  - `tasks` (list[Task]) — all tasks to consider for the plan
  - `available_time` (int) — the owner's available minutes for the day
- **Methods:**
  - `add_task(task)` — add a new task to the list
  - `remove_task(task)` — remove a task from the list
  - `generate_plan()` — sort tasks by priority, fit them into available time, and return a daily plan
  - `explain_plan()` — provide reasoning for why tasks were ordered/included the way they were

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, the design changed after reviewing the skeleton with AI. Three issues were identified:

1. **Added a `pet` reference to Task** — The original Task class had no link to a Pet. If an owner has multiple pets, there would be no way to tell which pet a task belongs to. I added an optional `pet` field to Task so tasks can be associated with a specific pet.

2. **Stored the generated plan inside Scheduler** — `generate_plan()` returned a list, but `explain_plan()` had no access to it. I added a `_current_plan` attribute so the scheduler remembers the last generated plan, allowing `explain_plan()` to reference it directly.

3. **Linked Scheduler to Owner** — The Scheduler originally duplicated the owner's `available_time` as its own attribute, which could go out of sync. I replaced it with a direct `owner` reference so the scheduler always reads the owner's current availability.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler considers three main constraints:
1. **Available time** — the owner's total minutes for the day. Tasks are packed in until time runs out.
2. **Priority** — tasks are sorted by priority (1 = highest) so the most important ones are scheduled first.
3. **Scheduled time** — tasks can have a specific "HH:MM" start time. The conflict detector checks for overlapping time windows.

Priority and time budget were treated as the most important constraints because a pet owner with limited time needs to guarantee that critical tasks (like medication) happen before optional ones (like enrichment).

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The conflict detection algorithm checks for **overlapping time ranges** between consecutive tasks (sorted by start time), but it does not automatically resolve conflicts — it only returns warning messages. This means two overlapping tasks can both appear in the plan.

This tradeoff is reasonable because automatic resolution (e.g., bumping one task later) would require assumptions about the owner's preferences that the system doesn't have. A warning lets the owner decide how to rearrange their schedule, keeping the human in control.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

AI was used throughout every phase of the project:

- **Design brainstorming** — I described the scenario and asked AI to identify the core classes, their attributes, and relationships. This produced the initial four-class UML design (Owner, Pet, Task, Scheduler).
- **Skeleton generation** — AI generated Python dataclass stubs from the UML, saving time on boilerplate while letting me review the structure before writing logic.
- **Code review** — After writing the skeleton, I asked AI to review `pawpal_system.py` for missing relationships and logic bottlenecks. This surfaced three issues (Task-Pet link, stored plan state, Scheduler-Owner coupling) that I fixed before implementation.
- **Algorithm implementation** — For sorting by `HH:MM` strings, I asked AI how to use a lambda with `sorted()` to convert time strings to comparable integers. For recurring tasks, I asked about `timedelta` for date arithmetic.
- **Test generation** — AI helped draft the initial test cases and suggested edge cases I hadn't considered (zero available time, cross-pet conflicts, calling `explain_plan()` before generating).

The most helpful prompts were specific and scoped: "Based on my classes in pawpal_system.py, how should the Scheduler retrieve tasks from the Owner's pets?" worked much better than vague requests like "make my code better."

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is. 
- How did you evaluate or verify what the AI suggested?

One moment where I did not accept an AI suggestion as-is: AI initially suggested that the Scheduler should have its own `tasks` list and `add_task()`/`remove_task()` methods, duplicating data that already lived on each Pet. I rejected this because it would create two sources of truth — tasks on pets and tasks on the scheduler — that could go out of sync. Instead, I redesigned the Scheduler to read tasks directly from the Owner's pets via `owner.get_all_tasks()`, making the Owner the single source of truth.

I verified this by writing tests that add tasks to pets and then generate a plan through the Scheduler, confirming that the Scheduler always sees the latest task state without needing its own copy.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The test suite (22 tests) verifies six categories of behavior:

1. **Core scheduling** — tasks are ordered by priority, fit within the time budget, and completed tasks are excluded from the plan.
2. **Sorting** — `sort_by_time()` returns tasks in chronological `HH:MM` order with unscheduled tasks last.
3. **Filtering** — `filter_tasks()` correctly narrows results by pet name, completion status (`pending`/`done`), and category.
4. **Recurring tasks** — completing a daily task creates a next occurrence due tomorrow; weekly creates one due in 7 days; one-time tasks produce no recurrence; all attributes (category, time, priority) are preserved.
5. **Conflict detection** — overlapping time windows are flagged, exact duplicate times are caught, conflicts across different pets are detected, and non-overlapping tasks produce no false positives.
6. **Edge cases** — a pet with no tasks yields an empty plan, zero available time schedules nothing, `explain_plan()` before generating returns a safe message, `edit()` updates fields correctly, `get_summary()` returns the expected format.

These tests are important because they verify both the "happy paths" (normal usage) and boundary conditions that could silently produce wrong schedules.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

**Confidence: 4 out of 5.** All 22 tests pass and cover the core logic, smart features, and edge cases thoroughly. The missing star reflects areas not yet tested: performance with very large task lists, UI-layer integration, and concurrent session state in Streamlit.

If I had more time I would test:
- A task whose duration exactly equals available time (boundary fit)
- An owner with 10+ pets and 50+ tasks (performance)
- Recurring tasks completing multiple cycles in sequence

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the clean separation between the logic layer (`pawpal_system.py`) and the UI layer (`app.py`). Building and testing everything in the terminal first with `main.py` meant I could verify sorting, filtering, conflict detection, and recurring tasks before touching Streamlit. When it came time to wire the UI, it was just calling methods that already worked — no debugging logic and layout at the same time.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If I had another iteration, I would:
- Add a **time-slot visualization** (e.g., a timeline bar) instead of just a table, so the owner can see their day at a glance.
- Implement **conflict auto-resolution** with user preferences (e.g., "if two tasks conflict, keep the higher-priority one and shift the other").
- Store data in a **lightweight database** (SQLite) so tasks persist across browser sessions instead of only living in `st.session_state`.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing I learned is that AI works best as a collaborator, not a replacement for design thinking. AI excelled at generating boilerplate, suggesting edge cases, and drafting code quickly — but the critical decisions (like making the Owner the single source of truth for tasks, or choosing to warn about conflicts rather than auto-resolve them) required human judgment about the system's purpose. Being the "lead architect" means knowing when to accept AI output, when to push back, and when to ask a more specific question to get a better answer.

---

## 6. Bonus Challenges

**Challenge 1: Advanced Algorithmic Capability** — Added two new algorithms:
- `find_next_available_slot(duration)` scans the day for the earliest gap that fits a task. It builds a list of occupied intervals, walks a cursor forward, and returns the first gap. Agent Mode was used to design the gap-scanning logic and edge cases (empty schedule, no room).
- `weighted_score()` computes a composite score from priority (weight 3.0), urgency/days until due (weight 2.0), and a frequency bonus (daily gets -1.0, weekly gets -0.5). `generate_weighted_plan()` uses this score instead of raw priority.

**Challenge 2: Data Persistence** — Added `save_to_json()` and `load_from_json()` class methods to Owner. The serialization converts the full object graph (Owner → Pets → Tasks) into nested dictionaries, handling `date` fields via `.isoformat()`. The Streamlit app auto-loads from `data.json` on startup and auto-saves after every change.

**Challenge 3: Advanced Priority Scheduling** — Priority was already numeric (1–3). Added color-coded labels (🔴 High, 🟡 Medium, 🟢 Low) via the `priority_label` property. The UI uses these labels in all tables, dropdowns, and the schedule output, making priority visually scannable at a glance.

**Challenge 4: Professional UI Formatting** — Added `category_emoji` property mapping each category to an icon (🚶 walk, 🍽️ feeding, 💊 meds, ✂️ grooming, 🧩 enrichment). Status uses ✅/⏳. The CLI output (`main.py`) and Streamlit tables both use these consistently for a polished, readable experience.

**Challenge 5: Multi-Model Prompt Comparison**

I compared how two AI models approached the weighted rescheduling task:

**Prompt used:** "Design a weighted scoring function for pet care tasks that considers priority level, urgency (days until due date), and whether the task recurs daily or weekly. Return a single float score where lower = schedule first."

**Claude's approach:**
- Clean, linear formula: `priority * 3.0 + days_until_due * 2.0 + frequency_bonus`
- Used named constants (`PRIORITY_WEIGHT`, `URGENCY_WEIGHT`, `FREQUENCY_WEIGHT`) at the module level for tunability
- Treated missing `due_date` as 7 days away (safe default)
- More "Pythonic" — concise, relied on properties and dataclass conventions

**GPT-5's approach:**
- Suggested a normalized 0–1 scoring system with `min-max` scaling across all tasks
- Required collecting all tasks first to compute min/max bounds before scoring any single task
- Proposed a separate `ScoringEngine` class with configurable weight profiles
- More enterprise-oriented — heavier abstraction, more code, harder to debug for a small app

**Verdict:** Claude's approach was more appropriate for this project's scope. The linear formula is transparent (you can read a score like `2.0` and immediately understand what drove it), doesn't require batch computation, and keeps the logic inside the `Task` class where it belongs. GPT-5's normalized approach would make more sense in a system with hundreds of tasks and configurable scoring profiles, but for a pet care app it adds unnecessary complexity. The key lesson: the "better" solution depends on the project's actual scale and audience.
