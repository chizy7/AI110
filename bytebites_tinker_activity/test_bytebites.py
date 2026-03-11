import pytest
from models import Customer, FoodItem, Menu, Transaction

# --- Logic Tests (The "Happy Path") ---

def test_calculate_total_with_multiple_items():
    """Verify that a transaction correctly sums multiple items."""
    item1 = FoodItem("Burger", 10.00, "Main", 4.0)
    item2 = FoodItem("Soda", 5.00, "Drinks", 4.0)
    order = Transaction([item1, item2])
    assert order.calculate_total_cost() == 15.00

def test_filter_category_is_case_insensitive():
    """Verify that filtering 'drinks' returns items even if stored as 'Drinks'."""
    soda = FoodItem("Soda", 2.00, "Drinks", 4.0)
    menu = Menu([soda])
    results = menu.filter_by_category("drinks")
    assert len(results) == 1
    assert results[0].name == "Soda"

# --- Edge Cases (The "What If?") ---

def test_order_total_is_zero_when_empty():
    """Verify that a transaction with no items returns a cost of $0."""
    empty_order = Transaction([])
    assert empty_order.calculate_total_cost() == 0.0

def test_sort_items_invalid_criteria():
    """Verify that sorting by an unsupported key raises an error."""
    menu = Menu([])
    with pytest.raises(ValueError):
        menu.sort_items("weight") # 'weight' is not popularity or price