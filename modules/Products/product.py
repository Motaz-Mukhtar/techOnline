#!/usr/bin/env python3
"""Create Product Class"""
from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import String
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Text


class Product(BaseModel, Base):
    """
        Product Class

        Attributes:
            name(str):
            description(str):
            price(float):
            image(str):
            category_id(str):
            customer_id(str):
    """
    __tablename__ = "products"
    product_name = Column(String(60))
    description = Column(String(1024))
    customer_id = Column(String(60), ForeignKey('customers.id'), nullable=False)
    price = Column(Float)
    rate = Column(Float, default=0.0)
    # must put 'default' attribute as an default image for the product
    product_image = Column(Text)
    # category_id  = Column(String(60), ForeignKey('categories.id'), nullable=False)