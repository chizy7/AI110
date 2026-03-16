"""Demo script for PawPal+ — showcases all features including bonus challenges."""

from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    # --- Create Owner ---
    owner = Owner(name="Alex", available_time=60)

    # --- Create Pets ---
    dog = Pet(name="Bella", species="dog", age=3, owner=owner)
    cat = Pet(name="Milo", species="cat", age=5, owner=owner)
    owner.add_pet(dog)
    owner.add_pet(cat)

    # --- Add Tasks (out of order, mixed priorities & due dates) ---
    dog.add_task(Task(name="Brush coat", category="grooming", duration=15, priority=3, scheduled_time="10:00"))
    dog.add_task(Task(name="Morning walk", category="walk", duration=30, priority=1, scheduled_time="07:00", frequency="daily", due_date=date.today()))
    dog.add_task(Task(name="Flea medication", category="meds", duration=5, priority=1, scheduled_time="08:00", due_date=date.today()))
    cat.add_task(Task(name="Feed breakfast", category="feeding", duration=10, priority=1, scheduled_time="07:30", frequency="daily", due_date=date.today()))
    cat.add_task(Task(name="Play with feather toy", category="enrichment", duration=20, priority=2, scheduled_time="09:00", due_date=date.today() + timedelta(days=3)))

    # Conflicting task
    dog.add_task(Task(name="Vet check-in call", category="meds", duration=20, priority=2, scheduled_time="07:15"))

    scheduler = Scheduler(owner=owner)

    # --- 1. Sort by time ---
    print("=" * 60)
    print("  📋 SORT BY SCHEDULED TIME")
    print("=" * 60)
    for task in scheduler.sort_by_time():
        print(f"  {task}")

    # --- 2. Sort by weighted score ---
    print()
    print("=" * 60)
    print("  ⚖️  SORT BY WEIGHTED SCORE (priority + urgency + frequency)")
    print("=" * 60)
    for task in scheduler.sort_by_weighted_score():
        print(f"  {task}  (score: {task.weighted_score():.1f})")

    # --- 3. Conflict detection ---
    print()
    print("=" * 60)
    print("  ⚠️  CONFLICT DETECTION")
    print("=" * 60)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for w in conflicts:
            print(f"  WARNING: {w}")

    # --- 4. Find next available slot ---
    print()
    print("=" * 60)
    print("  🔍 NEXT AVAILABLE SLOT")
    print("=" * 60)
    slot = scheduler.find_next_available_slot(duration=25)
    print(f"  Next 25-min slot: {slot or 'None found'}")
    slot2 = scheduler.find_next_available_slot(duration=60)
    print(f"  Next 60-min slot: {slot2 or 'None found'}")

    # --- 5. Generate weighted plan ---
    print()
    plan = scheduler.generate_weighted_plan()
    print("=" * 60)
    print(f"  📅 WEIGHTED SCHEDULE FOR {owner.name.upper()}")
    print(f"  Available time: {owner.available_time} min")
    print("=" * 60)
    for i, task in enumerate(plan, start=1):
        print(f"  {i}. {task}")
    print("-" * 60)
    print(scheduler.explain_plan())

    # --- 6. Recurring task demo ---
    print()
    print("=" * 60)
    print("  🔄 RECURRING TASK DEMO")
    print("=" * 60)
    walk_task = dog.tasks[1]  # Morning walk (daily)
    print(f"  Completing: {walk_task}")
    next_task = walk_task.mark_complete()
    print(f"  Original now: {walk_task}")
    if next_task:
        print(f"  Next occurrence: {next_task} (due {next_task.due_date})")

    # --- 7. JSON persistence demo ---
    print()
    print("=" * 60)
    print("  💾 JSON PERSISTENCE DEMO")
    print("=" * 60)
    owner.save_to_json("demo_data.json")
    print("  Saved to demo_data.json")
    loaded = Owner.load_from_json("demo_data.json")
    if loaded:
        print(f"  Loaded: {loaded.name}, {len(loaded.pets)} pets, {len(loaded.get_all_tasks())} tasks")
    # Clean up
    import os
    os.remove("demo_data.json")
    print("  Cleaned up demo file.")
    print("=" * 60)


if __name__ == "__main__":
    main()
