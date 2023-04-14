#!/usr/bin/env python3
"""Order Class"""
from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import ForeignKey


class Order(BaseModel, Base):
    """
        Define Order Class

        Attributes:
            customer_id(str): String(60) ForeignKey for customer.id and can't be null
            cart_id(str): String(60) ForeginKey for carts.id and can't be null
    """
    __tablename__ = 'orders'
    customer_id = Column(String(60), ForeignKey('customers.id'), nullable=False)
    cart_id = Column(String(60), ForeignKey('carts.id'))


