"""Tests for core PawPal+ behaviors."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import tempfile
from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


# ── Core tests ───────────────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    """Calling mark_complete() should set completed to True."""
    task = Task(name="Walk", category="walk", duration=20, priority=1)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase its task list length."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    assert len(pet.tasks) == 0
    pet.add_task(Task(name="Walk", category="walk", duration=20, priority=1))
    assert len(pet.tasks) == 1
    pet.add_task(Task(name="Feed", category="feeding", duration=10, priority=2))
    assert len(pet.tasks) == 2


def test_generate_plan_respects_time_limit():
    """Scheduler should not schedule more tasks than available time allows."""
    owner = Owner(name="Alex", available_time=30)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk", category="walk", duration=20, priority=1))
    pet.add_task(Task(name="Groom", category="grooming", duration=20, priority=2))
    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_plan()
    total_duration = sum(t.duration for t in plan)
    assert total_duration <= owner.available_time


def test_generate_plan_prioritizes_high_priority():
    """Higher priority tasks (lower number) should appear first in the plan."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Groom", category="grooming", duration=10, priority=3))
    pet.add_task(Task(name="Meds", category="meds", duration=5, priority=1))
    pet.add_task(Task(name="Play", category="enrichment", duration=15, priority=2))
    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_plan()
    assert plan[0].name == "Meds"
    assert plan[1].name == "Play"
    assert plan[2].name == "Groom"


def test_completed_tasks_excluded_from_plan():
    """Already completed tasks should not appear in the generated plan."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    task = Task(name="Walk", category="walk", duration=20, priority=1)
    task.mark_complete()
    pet.add_task(task)
    pet.add_task(Task(name="Feed", category="feeding", duration=10, priority=2))
    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_plan()
    assert len(plan) == 1
    assert plan[0].name == "Feed"


# ── Sorting tests ────────────────────────────────────────────────────────────

def test_sort_by_time_orders_by_scheduled_time():
    """Tasks should be sorted by HH:MM; unscheduled tasks go last."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Late", category="walk", duration=10, priority=1, scheduled_time="14:00"))
    pet.add_task(Task(name="Early", category="walk", duration=10, priority=1, scheduled_time="07:00"))
    pet.add_task(Task(name="No time", category="walk", duration=10, priority=1))
    scheduler = Scheduler(owner=owner)
    result = scheduler.sort_by_time()
    assert result[0].name == "Early"
    assert result[1].name == "Late"
    assert result[2].name == "No time"


# ── Filtering tests ──────────────────────────────────────────────────────────

def test_filter_by_pet_name():
    """Filtering by pet name returns only that pet's tasks."""
    owner = Owner(name="Alex", available_time=60)
    dog = Pet(name="Bella", species="dog", age=3, owner=owner)
    cat = Pet(name="Milo", species="cat", age=5, owner=owner)
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task(name="Walk", category="walk", duration=20, priority=1))
    cat.add_task(Task(name="Feed", category="feeding", duration=10, priority=1))
    scheduler = Scheduler(owner=owner)
    result = scheduler.filter_tasks(pet_name="Bella")
    assert len(result) == 1
    assert result[0].name == "Walk"


def test_filter_by_status():
    """Filtering by 'pending' excludes completed tasks."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    done_task = Task(name="Walk", category="walk", duration=20, priority=1)
    done_task.mark_complete()
    pet.add_task(done_task)
    pet.add_task(Task(name="Feed", category="feeding", duration=10, priority=2))
    scheduler = Scheduler(owner=owner)
    assert len(scheduler.filter_tasks(status="pending")) == 1
    assert len(scheduler.filter_tasks(status="done")) == 1


# ── Recurring task tests ─────────────────────────────────────────────────────

def test_daily_recurring_task_creates_next_occurrence():
    """Completing a daily task should create a new task due tomorrow."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    task = Task(name="Walk", category="walk", duration=20, priority=1,
                frequency="daily", due_date=date.today())
    pet.add_task(task)
    next_task = task.mark_complete()
    assert task.completed is True
    assert next_task is not None
    assert next_task.due_date == date.today() + timedelta(days=1)
    assert next_task.completed is False
    assert len(pet.tasks) == 2


def test_weekly_recurring_task_creates_next_occurrence():
    """Completing a weekly task should create a new task due in 7 days."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Grooming", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    task = Task(name="Bath", category="grooming", duration=30, priority=2,
                frequency="weekly", due_date=date(2026, 3, 16))
    pet.add_task(task)
    next_task = task.mark_complete()
    assert next_task is not None
    assert next_task.due_date == date(2026, 3, 23)


def test_one_time_task_no_recurrence():
    """Completing a one-time task should not create a new occurrence."""
    task = Task(name="Vet visit", category="meds", duration=60, priority=1, frequency="once")
    next_task = task.mark_complete()
    assert next_task is None


# ── Conflict detection tests ─────────────────────────────────────────────────

def test_detect_overlapping_tasks():
    """Two tasks whose times overlap should produce a conflict warning."""
    owner = Owner(name="Alex", available_time=120)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk", category="walk", duration=30, priority=1, scheduled_time="08:00"))
    pet.add_task(Task(name="Vet call", category="meds", duration=20, priority=2, scheduled_time="08:15"))
    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "Walk" in warnings[0]
    assert "Vet call" in warnings[0]


def test_no_conflict_when_tasks_dont_overlap():
    """Non-overlapping tasks should produce no warnings."""
    owner = Owner(name="Alex", available_time=120)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk", category="walk", duration=30, priority=1, scheduled_time="08:00"))
    pet.add_task(Task(name="Feed", category="feeding", duration=10, priority=1, scheduled_time="09:00"))
    scheduler = Scheduler(owner=owner)
    assert scheduler.detect_conflicts() == []


def test_exact_same_scheduled_time_triggers_conflict():
    """Two tasks at the exact same time should be flagged as a conflict."""
    owner = Owner(name="Alex", available_time=120)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk", category="walk", duration=30, priority=1, scheduled_time="08:00"))
    pet.add_task(Task(name="Meds", category="meds", duration=10, priority=1, scheduled_time="08:00"))
    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1


# ── Edge case tests ──────────────────────────────────────────────────────────

def test_pet_with_no_tasks_generates_empty_plan():
    """A pet with no tasks should result in an empty plan."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    assert scheduler.generate_plan() == []


def test_zero_available_time_schedules_nothing():
    """If the owner has 0 minutes available, no tasks should be scheduled."""
    owner = Owner(name="Alex", available_time=0)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk", category="walk", duration=20, priority=1))
    scheduler = Scheduler(owner=owner)
    assert scheduler.generate_plan() == []


def test_filter_by_category():
    """Filtering by category returns only matching tasks."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk", category="walk", duration=20, priority=1))
    pet.add_task(Task(name="Feed", category="feeding", duration=10, priority=1))
    pet.add_task(Task(name="Run", category="walk", duration=15, priority=2))
    scheduler = Scheduler(owner=owner)
    result = scheduler.filter_tasks(category="walk")
    assert len(result) == 2
    assert all(t.category == "walk" for t in result)


def test_edit_task_updates_fields():
    """Calling edit() should update name, duration, and priority."""
    task = Task(name="Walk", category="walk", duration=20, priority=2)
    task.edit(name="Long walk", duration=45, priority=1)
    assert task.name == "Long walk"
    assert task.duration == 45
    assert task.priority == 1


def test_pet_get_summary_format():
    """get_summary() should return 'Name, Age-year-old Species'."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    assert pet.get_summary() == "Bella, 3-year-old dog"


def test_explain_plan_before_generating():
    """Calling explain_plan() before generate_plan() should return a message."""
    owner = Owner(name="Alex", available_time=60)
    scheduler = Scheduler(owner=owner)
    assert "No plan generated yet" in scheduler.explain_plan()


def test_conflict_across_different_pets():
    """Conflicts should be detected even when tasks belong to different pets."""
    owner = Owner(name="Alex", available_time=120)
    dog = Pet(name="Bella", species="dog", age=3, owner=owner)
    cat = Pet(name="Milo", species="cat", age=5, owner=owner)
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task(name="Walk dog", category="walk", duration=30, priority=1, scheduled_time="08:00"))
    cat.add_task(Task(name="Feed cat", category="feeding", duration=15, priority=1, scheduled_time="08:10"))
    scheduler = Scheduler(owner=owner)
    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "Walk dog" in warnings[0]
    assert "Feed cat" in warnings[0]


def test_recurring_task_preserves_attributes():
    """The next occurrence of a recurring task should keep the same category and time."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    task = Task(name="Walk", category="walk", duration=20, priority=1,
                frequency="daily", due_date=date.today(), scheduled_time="07:00")
    pet.add_task(task)
    next_task = task.mark_complete()
    assert next_task.category == "walk"
    assert next_task.scheduled_time == "07:00"
    assert next_task.frequency == "daily"
    assert next_task.priority == 1


# ── Challenge 1: Next available slot tests ───────────────────────────────────

def test_find_next_available_slot_empty_schedule():
    """With no scheduled tasks, the first slot should be at day_start."""
    owner = Owner(name="Alex", available_time=120)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    scheduler = Scheduler(owner=owner)
    assert scheduler.find_next_available_slot(30) == "07:00"


def test_find_next_available_slot_between_tasks():
    """Should find a gap between two scheduled tasks."""
    owner = Owner(name="Alex", available_time=120)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk", category="walk", duration=30, priority=1, scheduled_time="07:00"))
    pet.add_task(Task(name="Feed", category="feeding", duration=10, priority=1, scheduled_time="09:00"))
    scheduler = Scheduler(owner=owner)
    # Gap from 07:30 to 09:00 = 90 min
    slot = scheduler.find_next_available_slot(60)
    assert slot == "07:30"


def test_find_next_available_slot_no_room():
    """Should return None when no slot fits."""
    owner = Owner(name="Alex", available_time=120)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    # Fill the entire day
    pet.add_task(Task(name="Long task", category="walk", duration=840, priority=1, scheduled_time="07:00"))
    scheduler = Scheduler(owner=owner)
    assert scheduler.find_next_available_slot(30) is None


# ── Challenge 1: Weighted score tests ────────────────────────────────────────

def test_weighted_score_prefers_urgent_tasks():
    """A task due today should score lower (better) than one due in 5 days."""
    urgent = Task(name="Meds", category="meds", duration=5, priority=2, due_date=date.today())
    later = Task(name="Groom", category="grooming", duration=15, priority=2, due_date=date.today() + timedelta(days=5))
    assert urgent.weighted_score() < later.weighted_score()


def test_weighted_score_prefers_recurring():
    """A daily recurring task should score slightly lower than a one-time task with same priority."""
    daily = Task(name="Walk", category="walk", duration=20, priority=2, frequency="daily", due_date=date.today())
    once = Task(name="Walk", category="walk", duration=20, priority=2, frequency="once", due_date=date.today())
    assert daily.weighted_score() < once.weighted_score()


def test_generate_weighted_plan_uses_scores():
    """Weighted plan should order by composite score, not just raw priority."""
    owner = Owner(name="Alex", available_time=120)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    # P2 due today should beat P2 due in a week
    pet.add_task(Task(name="Later groom", category="grooming", duration=15, priority=2, due_date=date.today() + timedelta(days=7)))
    pet.add_task(Task(name="Urgent meds", category="meds", duration=5, priority=2, due_date=date.today()))
    scheduler = Scheduler(owner=owner)
    plan = scheduler.generate_weighted_plan()
    assert plan[0].name == "Urgent meds"
    assert plan[1].name == "Later groom"


# ── Challenge 2: JSON persistence tests ──────────────────────────────────────

def test_save_and_load_json():
    """Owner data should survive a save/load round-trip."""
    owner = Owner(name="Alex", available_time=60)
    pet = Pet(name="Bella", species="dog", age=3, owner=owner)
    owner.add_pet(pet)
    pet.add_task(Task(name="Walk", category="walk", duration=20, priority=1,
                      scheduled_time="08:00", frequency="daily", due_date=date.today()))

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        filepath = f.name

    try:
        owner.save_to_json(filepath)
        loaded = Owner.load_from_json(filepath)

        assert loaded is not None
        assert loaded.name == "Alex"
        assert loaded.available_time == 60
        assert len(loaded.pets) == 1
        assert loaded.pets[0].name == "Bella"
        assert len(loaded.pets[0].tasks) == 1

        task = loaded.pets[0].tasks[0]
        assert task.name == "Walk"
        assert task.scheduled_time == "08:00"
        assert task.frequency == "daily"
        assert task.due_date == date.today()
    finally:
        os.remove(filepath)


def test_load_from_nonexistent_file():
    """Loading from a missing file should return None."""
    assert Owner.load_from_json("nonexistent_file_12345.json") is None


# ── Challenge 4: Emoji/formatting tests ──────────────────────────────────────

def test_category_emoji():
    """Each category should have a corresponding emoji."""
    task = Task(name="Walk", category="walk", duration=20, priority=1)
    assert task.category_emoji == "🚶"
    task2 = Task(name="Feed", category="feeding", duration=10, priority=1)
    assert task2.category_emoji == "🍽️"


def test_priority_label():
    """Each priority level should produce a color-coded label."""
    t1 = Task(name="A", category="walk", duration=10, priority=1)
    t2 = Task(name="B", category="walk", duration=10, priority=2)
    t3 = Task(name="C", category="walk", duration=10, priority=3)
    assert "🔴" in t1.priority_label
    assert "🟡" in t2.priority_label
    assert "🟢" in t3.priority_label
