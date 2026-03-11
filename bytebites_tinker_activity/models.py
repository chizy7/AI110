"""
ByteBites Core Models
---------------------
This module contains the core data structures for the ByteBites campus food app.

1. Customer: Manages user profiles and purchase history for verification.
2. FoodItem: Defines individual menu products with pricing and popularity ratings.
3. Menu: A collection of FoodItems providing filtering and organization logic.
4. Transaction: Groups selected items into an order and calculates total costs.

---------------------

High-level implementation plan (per bytebites_spec.md):
 
1) Choose a simple class style
    - Use plain Python classes or @dataclass for:
      - FoodItem (record-like)
      - Menu (collection)
      - Transaction (order grouping)
      - Customer (profile + purchase history)
 
2) Implement FoodItem
    - Attributes: name, price, category, popularity_rating
    - Keep validation lightweight (e.g., price >= 0)
 
3) Implement Menu
    - Attribute: items (collection of FoodItem)
    - Method: filter_by_category(category) -> list[FoodItem]
      - Return items whose item.category matches the given category
 
4) Implement Transaction
    - Attribute: selected_items (list of FoodItem)
    - Method: calculate_total_cost() -> float
      - Sum item.price across selected_items
 
5) Implement Customer
    - Attributes: name, purchase_history (list of Transaction)
    - purchase_history exists to help verify real users
 
6) Quick integration sanity check (optional)
    - Create FoodItems -> add to Menu -> filter_by_category
    - Create Transaction -> calculate_total_cost
    - Add Transaction to Customer.purchase_history
"""

from typing import List, Optional

class Customer:
    def __init__(self, name: str, purchase_history: Optional[List["Transaction"]] = None):
        self.name = name
        self.purchase_history = purchase_history if purchase_history is not None else []

class FoodItem:
    def __init__(self, name: str, price: float, category: str, popularity_rating: float):
        self.name = name
        self.price = price
        self.category = category
        self.popularity_rating = popularity_rating

class Menu:
    def __init__(self, items: Optional[List["FoodItem"]] = None):
        self.items = items if items is not None else []

    def filter_by_category(self, category: str) -> List["FoodItem"]:
        return [item for item in self.items if item.category == category]

class Transaction:
    def __init__(self, selected_items: Optional[List["FoodItem"]] = None):
        self.selected_items = selected_items if selected_items is not None else []

    def calculate_total_cost(self) -> float:
        return sum(item.price for item in self.selected_items)
