from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta

# ── Emoji / formatting helpers ───────────────────────────────────────────────

CATEGORY_EMOJI = {
    "walk": "🚶",
    "feeding": "🍽️",
    "meds": "💊",
    "grooming": "✂️",
    "enrichment": "🧩",
}

PRIORITY_LABEL = {
    1: "🔴 High",
    2: "🟡 Medium",
    3: "🟢 Low",
}

# ── Weight multipliers for weighted priority scoring ─────────────────────────
# Higher weight = more influence on the scheduling score.
PRIORITY_WEIGHT = 3.0   # how much priority level matters
URGENCY_WEIGHT = 2.0    # how much an approaching due date matters
FREQUENCY_WEIGHT = 1.0  # recurring tasks get a small bonus


def _minutes_to_hhmm(minutes: int) -> str:
    """Convert minutes-since-midnight to 'HH:MM' string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Owner:
    """Represents the pet owner with their daily availability."""
    name: str
    available_time: int  # minutes available per day
    pets: list[Pet] = field(default_factory=list)

    def set_available_time(self, minutes: int) -> None:
        """Update the owner's available minutes for the day."""
        self.available_time = minutes

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Collect and return every task across all owned pets."""
        all_tasks: list[Task] = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    # ── JSON persistence (Challenge 2) ───────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize the owner and all pets/tasks to a plain dictionary."""
        return {
            "name": self.name,
            "available_time": self.available_time,
            "pets": [
                {
                    "name": pet.name,
                    "species": pet.species,
                    "age": pet.age,
                    "tasks": [
                        {
                            "name": t.name,
                            "category": t.category,
                            "duration": t.duration,
                            "priority": t.priority,
                            "completed": t.completed,
                            "scheduled_time": t.scheduled_time,
                            "frequency": t.frequency,
                            "due_date": t.due_date.isoformat() if t.due_date else None,
                        }
                        for t in pet.tasks
                    ],
                }
                for pet in self.pets
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Owner:
        """Deserialize an Owner (with pets and tasks) from a dictionary."""
        owner = cls(name=data["name"], available_time=data["available_time"])
        for pet_data in data.get("pets", []):
            pet = Pet(
                name=pet_data["name"],
                species=pet_data["species"],
                age=pet_data["age"],
                owner=owner,
            )
            for task_data in pet_data.get("tasks", []):
                task = Task(
                    name=task_data["name"],
                    category=task_data["category"],
                    duration=task_data["duration"],
                    priority=task_data["priority"],
                    completed=task_data.get("completed", False),
                    scheduled_time=task_data.get("scheduled_time", ""),
                    frequency=task_data.get("frequency", "once"),
                    due_date=(
                        date.fromisoformat(task_data["due_date"])
                        if task_data.get("due_date")
                        else None
                    ),
                )
                pet.add_task(task)
            owner.add_pet(pet)
        return owner

    def save_to_json(self, filepath: str = "data.json") -> None:
        """Write the owner's full state to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str = "data.json") -> Owner | None:
        """Load an Owner from a JSON file. Returns None if file doesn't exist."""
        if not os.path.exists(filepath):
            return None
        with open(filepath) as f:
            return cls.from_dict(json.load(f))


@dataclass
class Pet:
    """Represents a pet with basic profile information and its care tasks."""
    name: str
    species: str
    age: int
    owner: Owner
    tasks: list[Task] = field(default_factory=list)

    def get_summary(self) -> str:
        """Return a short description like 'Bella, 3-year-old dog'."""
        return f"{self.name}, {self.age}-year-old {self.species}"

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        self.tasks.remove(task)


@dataclass
class Task:
    """Represents a single pet care task with optional scheduling and recurrence."""
    name: str
    category: str  # walk, feeding, meds, grooming, enrichment
    duration: int  # minutes
    priority: int  # 1 = highest, 3 = lowest
    pet: Pet | None = None
    completed: bool = False
    scheduled_time: str = ""  # "HH:MM" format, e.g. "08:00"
    frequency: str = "once"  # "once", "daily", or "weekly"
    due_date: date | None = None

    def edit(self, name: str, duration: int, priority: int) -> None:
        """Update the task's name, duration, and priority."""
        self.name = name
        self.duration = duration
        self.priority = priority

    def mark_complete(self) -> Task | None:
        """Mark this task as completed. Returns a new Task for the next occurrence if recurring."""
        self.completed = True
        if self.frequency == "once":
            return None
        delta = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        next_due = (self.due_date or date.today()) + delta
        next_task = Task(
            name=self.name,
            category=self.category,
            duration=self.duration,
            priority=self.priority,
            scheduled_time=self.scheduled_time,
            frequency=self.frequency,
            due_date=next_due,
        )
        if self.pet:
            self.pet.add_task(next_task)
        return next_task

    def weighted_score(self) -> float:
        """Compute a weighted priority score (lower = schedule first).

        Combines priority level, urgency (days until due), and frequency bonus
        into a single comparable number.
        """
        # Priority component: P1=1, P2=2, P3=3 → lower is better
        priority_score = self.priority * PRIORITY_WEIGHT

        # Urgency component: tasks due sooner get a lower score
        if self.due_date:
            days_until = (self.due_date - date.today()).days
            urgency_score = max(days_until, 0) * URGENCY_WEIGHT
        else:
            urgency_score = 7 * URGENCY_WEIGHT  # unset = treat as a week away

        # Frequency bonus: recurring tasks get a small reduction
        freq_bonus = 0.0
        if self.frequency == "daily":
            freq_bonus = -1.0 * FREQUENCY_WEIGHT
        elif self.frequency == "weekly":
            freq_bonus = -0.5 * FREQUENCY_WEIGHT

        return priority_score + urgency_score + freq_bonus

    def end_time_minutes(self) -> int | None:
        """Return the end time in minutes-since-midnight, or None if unscheduled."""
        start = self.start_time_minutes()
        if start is None:
            return None
        return start + self.duration

    def start_time_minutes(self) -> int | None:
        """Convert scheduled_time 'HH:MM' to minutes since midnight, or None if unset."""
        if not self.scheduled_time:
            return None
        h, m = self.scheduled_time.split(":")
        return int(h) * 60 + int(m)

    @property
    def category_emoji(self) -> str:
        """Return the emoji for this task's category."""
        return CATEGORY_EMOJI.get(self.category, "📌")

    @property
    def priority_label(self) -> str:
        """Return a color-coded priority label."""
        return PRIORITY_LABEL.get(self.priority, f"P{self.priority}")

    def __str__(self) -> str:
        """Return a readable summary of the task."""
        status = "✅" if self.completed else "⏳"
        pet_name = self.pet.name if self.pet else "Unassigned"
        time_str = f" @{self.scheduled_time}" if self.scheduled_time else ""
        freq_str = f" [{self.frequency}]" if self.frequency != "once" else ""
        return (
            f"{self.category_emoji} [{self.priority_label}] {self.name} "
            f"({self.duration}min){time_str}{freq_str} - {pet_name} {status}"
        )


@dataclass
class Scheduler:
    """Generates a daily care plan with sorting, filtering, and conflict detection."""
    owner: Owner
    _current_plan: list[Task] = field(default_factory=list, repr=False)

    # ── Sorting ──────────────────────────────────────────────────────────────

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks by their scheduled_time ('HH:MM'). Unscheduled tasks go last."""
        source = tasks if tasks is not None else self.owner.get_all_tasks()
        return sorted(source, key=lambda t: (t.start_time_minutes() is None, t.start_time_minutes() or 0))

    def sort_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks by priority (1 = highest first)."""
        source = tasks if tasks is not None else self.owner.get_all_tasks()
        return sorted(source, key=lambda t: t.priority)

    def sort_by_weighted_score(self, tasks: list[Task] | None = None) -> list[Task]:
        """Sort tasks by weighted score (combines priority, urgency, frequency)."""
        source = tasks if tasks is not None else self.owner.get_all_tasks()
        return sorted(source, key=lambda t: t.weighted_score())

    # ── Filtering ────────────────────────────────────────────────────────────

    def filter_tasks(
        self,
        pet_name: str | None = None,
        status: str | None = None,
        category: str | None = None,
    ) -> list[Task]:
        """Filter tasks by pet name, completion status ('pending'/'done'), or category."""
        tasks = self.owner.get_all_tasks()
        if pet_name:
            tasks = [t for t in tasks if t.pet and t.pet.name == pet_name]
        if status == "pending":
            tasks = [t for t in tasks if not t.completed]
        elif status == "done":
            tasks = [t for t in tasks if t.completed]
        if category:
            tasks = [t for t in tasks if t.category == category]
        return tasks

    # ── Conflict Detection ───────────────────────────────────────────────────

    def detect_conflicts(self) -> list[str]:
        """Detect overlapping scheduled times and return warning messages."""
        scheduled = [t for t in self.owner.get_all_tasks() if t.scheduled_time and not t.completed]
        sorted_tasks = self.sort_by_time(scheduled)
        warnings: list[str] = []

        for i in range(len(sorted_tasks) - 1):
            a = sorted_tasks[i]
            b = sorted_tasks[i + 1]
            a_end = a.end_time_minutes()
            b_start = b.start_time_minutes()
            if a_end is not None and b_start is not None and a_end > b_start:
                warnings.append(
                    f"Conflict: '{a.name}' (ends {a.scheduled_time}+{a.duration}min) "
                    f"overlaps with '{b.name}' (starts {b.scheduled_time})"
                )

        return warnings

    # ── Next Available Slot (Challenge 1) ────────────────────────────────────

    def find_next_available_slot(self, duration: int, day_start: str = "07:00", day_end: str = "21:00") -> str | None:
        """Find the earliest time slot that fits a task of the given duration.

        Scans the day from day_start to day_end, skipping over already-scheduled
        incomplete tasks, and returns the first gap that fits. Returns None if
        no slot is available.
        """
        start_min = int(day_start.split(":")[0]) * 60 + int(day_start.split(":")[1])
        end_min = int(day_end.split(":")[0]) * 60 + int(day_end.split(":")[1])

        scheduled = [
            t for t in self.owner.get_all_tasks()
            if t.scheduled_time and not t.completed
        ]
        sorted_tasks = self.sort_by_time(scheduled)

        # Build list of occupied intervals
        occupied: list[tuple[int, int]] = []
        for t in sorted_tasks:
            t_start = t.start_time_minutes()
            t_end = t.end_time_minutes()
            if t_start is not None and t_end is not None:
                occupied.append((t_start, t_end))

        cursor = start_min
        for occ_start, occ_end in occupied:
            if cursor + duration <= occ_start:
                return _minutes_to_hhmm(cursor)
            cursor = max(cursor, occ_end)

        # Check gap after last occupied slot
        if cursor + duration <= end_min:
            return _minutes_to_hhmm(cursor)

        return None

    # ── Plan Generation ──────────────────────────────────────────────────────

    def generate_plan(self) -> list[Task]:
        """Sort incomplete tasks by priority, fit into available time, return the plan."""
        all_tasks = self.owner.get_all_tasks()
        incomplete = [t for t in all_tasks if not t.completed]
        sorted_tasks = sorted(incomplete, key=lambda t: t.priority)

        plan: list[Task] = []
        remaining_time = self.owner.available_time
        for task in sorted_tasks:
            if task.duration <= remaining_time:
                plan.append(task)
                remaining_time -= task.duration

        self._current_plan = plan
        return plan

    def generate_weighted_plan(self) -> list[Task]:
        """Generate a plan using weighted scores (priority + urgency + frequency)."""
        all_tasks = self.owner.get_all_tasks()
        incomplete = [t for t in all_tasks if not t.completed]
        sorted_tasks = sorted(incomplete, key=lambda t: t.weighted_score())

        plan: list[Task] = []
        remaining_time = self.owner.available_time
        for task in sorted_tasks:
            if task.duration <= remaining_time:
                plan.append(task)
                remaining_time -= task.duration

        self._current_plan = plan
        return plan

    def explain_plan(self) -> str:
        """Explain why the current plan was built the way it was."""
        if not self._current_plan:
            return "No plan generated yet. Call generate_plan() first."

        total_scheduled = sum(t.duration for t in self._current_plan)
        all_tasks = self.owner.get_all_tasks()
        incomplete = [t for t in all_tasks if not t.completed]
        skipped = [t for t in incomplete if t not in self._current_plan]

        lines = [
            f"Plan for {self.owner.name} "
            f"({self.owner.available_time} min available):",
            f"  Scheduled {len(self._current_plan)} task(s) "
            f"totalling {total_scheduled} min.",
            "  Tasks are ordered by priority (1 = highest).",
        ]

        if skipped:
            skipped_names = ", ".join(t.name for t in skipped)
            lines.append(
                f"  Skipped (not enough time): {skipped_names}."
            )

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("  Warnings:")
            for w in conflicts:
                lines.append(f"    - {w}")

        return "\n".join(lines)
