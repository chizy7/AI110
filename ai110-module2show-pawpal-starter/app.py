import streamlit as st
from pawpal_system import (
    Owner, Pet, Task, Scheduler,
    CATEGORY_EMOJI, PRIORITY_LABEL,
)

DATA_FILE = "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your smart pet care planning assistant")

# ── Session State Initialization ─────────────────────────────────────────────
if "owner" not in st.session_state:
    # Try loading from disk first (Challenge 2: persistence)
    loaded = Owner.load_from_json(DATA_FILE)
    st.session_state.owner = loaded
    st.session_state.scheduler = Scheduler(owner=loaded) if loaded else None

# Helper to persist after every change
def _save():
    if st.session_state.owner:
        st.session_state.owner.save_to_json(DATA_FILE)

# ── 1. Owner Setup ───────────────────────────────────────────────────────────
st.subheader("👤 Owner Setup")

with st.form("owner_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    available_time = st.number_input(
        "Available time today (minutes)", min_value=1, max_value=480, value=60
    )
    submitted_owner = st.form_submit_button("Save Owner")

if submitted_owner:
    owner = Owner(name=owner_name, available_time=available_time)
    st.session_state.owner = owner
    st.session_state.scheduler = Scheduler(owner=owner)
    _save()

owner: Owner | None = st.session_state.owner

if owner is None:
    st.info("Set up an owner above to get started.")
    st.stop()

st.success(f"Owner: **{owner.name}** — {owner.available_time} min available today")

# ── 2. Add a Pet ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("🐾 Your Pets")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
    submitted_pet = st.form_submit_button("Add Pet")

if submitted_pet:
    new_pet = Pet(name=pet_name, species=species, age=age, owner=owner)
    owner.add_pet(new_pet)
    _save()
    st.rerun()

if owner.pets:
    pet_cols = st.columns(min(len(owner.pets), 4))
    for i, pet in enumerate(owner.pets):
        with pet_cols[i % 4]:
            st.metric(label=pet.name, value=pet.species.title(), delta=f"{len(pet.tasks)} tasks")
            st.caption(pet.get_summary())
else:
    st.info("No pets yet. Add one above.")
    st.stop()

# ── 3. Add Tasks ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("📋 Add a Task")

pet_names = [p.name for p in owner.pets]
with st.form("task_form"):
    col1, col2 = st.columns(2)
    with col1:
        selected_pet_name = st.selectbox("Assign to pet", pet_names)
        task_title = st.text_input("Task name", value="Morning walk")
        category = st.selectbox(
            "Category",
            ["walk", "feeding", "meds", "grooming", "enrichment"],
            format_func=lambda c: f"{CATEGORY_EMOJI.get(c, '')} {c.title()}",
        )
    with col2:
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
        priority = st.selectbox(
            "Priority",
            [1, 2, 3],
            format_func=lambda p: PRIORITY_LABEL.get(p, f"P{p}"),
        )
        scheduled_time = st.text_input(
            "Scheduled time (HH:MM, optional)", value="", placeholder="e.g. 08:00"
        )
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
    submitted_task = st.form_submit_button("Add Task")

if submitted_task:
    target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
    new_task = Task(
        name=task_title,
        category=category,
        duration=int(duration),
        priority=int(priority),
        scheduled_time=scheduled_time.strip(),
        frequency=frequency,
    )
    target_pet.add_task(new_task)
    _save()
    st.rerun()

# ── 4. View & Filter Tasks ──────────────────────────────────────────────────
st.divider()
st.subheader("📊 Task Overview")

scheduler: Scheduler = st.session_state.scheduler
all_tasks = owner.get_all_tasks()

if not all_tasks:
    st.info("No tasks yet. Add one above.")
    st.stop()

# Filter controls
filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
with filter_col1:
    filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names)
with filter_col2:
    filter_status = st.selectbox("Filter by status", ["All", "pending", "done"])
with filter_col3:
    filter_category = st.selectbox(
        "Filter by category",
        ["All", "walk", "feeding", "meds", "grooming", "enrichment"],
    )
with filter_col4:
    sort_by = st.selectbox("Sort by", ["Priority", "Scheduled time", "Weighted score"])

# Apply filters
filtered = scheduler.filter_tasks(
    pet_name=filter_pet if filter_pet != "All" else None,
    status=filter_status if filter_status != "All" else None,
    category=filter_category if filter_category != "All" else None,
)

# Apply sorting
if sort_by == "Scheduled time":
    filtered = scheduler.sort_by_time(filtered)
elif sort_by == "Weighted score":
    filtered = scheduler.sort_by_weighted_score(filtered)
else:
    filtered = scheduler.sort_by_priority(filtered)

if filtered:
    task_data = [
        {
            "": t.category_emoji,
            "Pet": t.pet.name if t.pet else "—",
            "Task": t.name,
            "Time": t.scheduled_time or "—",
            "Duration": f"{t.duration} min",
            "Priority": t.priority_label,
            "Frequency": t.frequency.title(),
            "Status": "✅ Done" if t.completed else "⏳ Pending",
        }
        for t in filtered
    ]
    st.table(task_data)
    st.caption(f"Showing {len(filtered)} of {len(all_tasks)} tasks")
else:
    st.warning("No tasks match the current filters.")

# ── 5. Mark Tasks Complete ───────────────────────────────────────────────────
st.divider()
st.subheader("✅ Complete a Task")

pending_tasks = [t for t in all_tasks if not t.completed]
if pending_tasks:
    task_options = {str(t): t for t in pending_tasks}
    selected_task_str = st.selectbox("Select a task to complete", list(task_options.keys()))
    if st.button("Mark Complete"):
        selected_task = task_options[selected_task_str]
        next_task = selected_task.mark_complete()
        _save()
        if next_task:
            st.success(
                f"Completed: **{selected_task.name}**. "
                f"Next occurrence auto-created for **{next_task.due_date}**."
            )
        else:
            st.success(f"Completed: **{selected_task.name}**")
        st.rerun()
else:
    st.info("All tasks are complete! 🎉")

# ── 6. Find Next Available Slot ──────────────────────────────────────────────
st.divider()
st.subheader("🔍 Find Next Available Slot")

slot_col1, slot_col2 = st.columns(2)
with slot_col1:
    slot_duration = st.number_input("Task duration (minutes)", min_value=1, max_value=240, value=30, key="slot_dur")
with slot_col2:
    if st.button("Find Slot"):
        slot = scheduler.find_next_available_slot(int(slot_duration))
        if slot:
            st.success(f"Next available slot: **{slot}** (for {slot_duration} min)")
        else:
            st.error("No available slot found in today's schedule (07:00–21:00).")

# ── 7. Generate Schedule ─────────────────────────────────────────────────────
st.divider()
st.subheader("📅 Daily Schedule")

plan_mode = st.radio(
    "Scheduling strategy",
    ["Priority only", "Weighted (priority + urgency + frequency)"],
    horizontal=True,
)

if st.button("Generate Schedule", type="primary"):
    if plan_mode == "Weighted (priority + urgency + frequency)":
        plan = scheduler.generate_weighted_plan()
    else:
        plan = scheduler.generate_plan()

    # Show conflict warnings first
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            st.warning(f"⚠️ {warning}")

    if plan:
        st.write("**Today's Plan:**")
        plan_data = [
            {
                "#": i,
                "": t.category_emoji,
                "Pet": t.pet.name if t.pet else "—",
                "Task": t.name,
                "Time": t.scheduled_time or "—",
                "Duration": f"{t.duration} min",
                "Priority": t.priority_label,
            }
            for i, t in enumerate(plan, start=1)
        ]
        st.table(plan_data)

        # Metrics dashboard
        total_min = sum(t.duration for t in plan)
        remaining = owner.available_time - total_min
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tasks scheduled", len(plan))
        with col2:
            st.metric("Time used", f"{total_min} min")
        with col3:
            st.metric("Time remaining", f"{remaining} min")

        with st.expander("View plan explanation"):
            st.text(scheduler.explain_plan())
    else:
        st.info("No incomplete tasks to schedule.")
