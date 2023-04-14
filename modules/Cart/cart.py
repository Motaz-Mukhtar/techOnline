#!/usr/bin/env python3
"""Create Cart Class"""
from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Cart(BaseModel, Base):
    """
        Cart Class

        Attributes:
            total_price (float): Float type, 0.0 by default
            customer_id (str): String(60) type and ForignKey for customers.id
    """
    __tablename__ = 'carts'
    total_price = Column(Float, default=0.0)
    customer_id = Column(String(60), ForeignKey("customers.id"), nullable=False)
    # products = relationship('Product', backref='cart', cascade='delete')

    # @property
    # def products(self):
    #     """
    #         Return List of products that linked with the customer cart
    #     """
