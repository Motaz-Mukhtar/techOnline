#!/usr/bin/env python3
"""
Seed predefined product categories (admin-only action).

This script adds five core categories if they do not already exist:
- Mobile Devices
- Electronics
- Accessories
- Computers
- Gaming

Each category receives a unique ID (via BaseModel) and a unique slug.
Run this as an admin operation (direct DB write via storage layer).
"""

import os
import sys

# Ensure project root is on sys.path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from modules.Category.category import Category
from modules import storage


def ensure_categories():
    target_categories = [
        {"name": "Mobile Devices", "slug": "mobile-devices", "description": "Smartphones, tablets, and wearables"},
        {"name": "Electronics", "slug": "electronics", "description": "General consumer electronics and gadgets"},
        {"name": "Accessories", "slug": "accessories", "description": "Cables, chargers, cases, and add-ons"},
        {"name": "Computers", "slug": "computers", "description": "Desktops, laptops, and components"},
        {"name": "Gaming", "slug": "gaming", "description": "Consoles, PC gaming gear, and titles"},
    ]

    existing = list(storage.all(Category).values())
    existing_by_slug = {getattr(c, 'slug', '').lower(): c for c in existing}

    created = []
    skipped = []

    for cat in target_categories:
        slug = cat["slug"].lower()
        if slug in existing_by_slug:
            skipped.append(cat["name"])
            continue

        new_cat = Category(
            name=cat["name"],
            slug=cat["slug"],
            description=cat["description"],
            is_active='True'
        )
        new_cat.save()
        created.append((cat["name"], new_cat.id))

    return created, skipped


if __name__ == "__main__":
    created, skipped = ensure_categories()
    if created:
        print("Created categories:")
        for name, cid in created:
            print(f" - {name} (id={cid})")
    else:
        print("No new categories created.")
    if skipped:
        print("Skipped existing categories:")
        for name in skipped:
            print(f" - {name}")