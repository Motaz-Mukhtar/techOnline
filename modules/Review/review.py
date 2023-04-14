#!/usr/bin/env python3
"""Create Review Class"""
from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import String
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import ForeignKey


class Review(BaseModel, Base):
    """
        Review Class

        Attributes:
            text(str):
            product_id(str):
            customer(str):
            rate(float):
    """
    __tablename__ = 'reviews'
    text = Column(String(2048))
    product_id = Column(String(60), ForeignKey('products.id'), nullable=False)
    customer_id = Column(String(60), ForeignKey('customers.id'), nullable=False)
    rate = Column(Float, default=0.0)
    

