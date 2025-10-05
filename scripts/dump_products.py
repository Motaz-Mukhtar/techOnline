#!/usr/bin/env python3
"""
Quick script to print products in the local database.
"""
import sys, os

# Ensure project root is on PYTHONPATH
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from modules import storage
from modules.Products.product import Product
import json

def main():
    products = list(storage.all(Product).values())
    print('Total products:', len(products))
    out = []
    for p in products:
        d = p.to_dict()
        out.append({
            'id': d.get('id'),
            'product_name': d.get('product_name'),
            'customer_id': d.get('customer_id'),
            'price': d.get('price'),
            'category_id': d.get('category_id'),
        })
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()