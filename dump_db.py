#!/usr/bin/env python3
import json

try:
    from modules import storage
    from modules.Customer.customer import Customer
    from modules.Products.product import Product
    from modules.Category.category import Category
    from modules.Cart.cart import Cart
    from modules.Cart.cart_item import CartItem
    from modules.Order.order import Order
    from modules.Order.order_item import OrderItem
    from modules.Review.review import Review
except Exception as e:
    print(f"Error importing modules: {e}")
    raise


def dump_collection(name, cls):
    try:
        items = list(storage.all(cls).values())
        print(f"\n=== {name} ({len(items)}) ===")
        for obj in items:
            try:
                data = obj.to_dict()
            except Exception:
                # Fallback if to_dict is not available
                data = obj.__dict__
            print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Failed to dump {name}: {e}")


def main():
    print("\nTechOnline Database Dump")
    print("====================================")
    collections = [
        ("Customers", Customer),
        ("Products", Product),
        ("Categories", Category),
        ("Carts", Cart),
        ("CartItems", CartItem),
        ("Orders", Order),
        ("OrderItems", OrderItem),
        ("Reviews", Review),
    ]

    for name, cls in collections:
        dump_collection(name, cls)


if __name__ == "__main__":
    main()