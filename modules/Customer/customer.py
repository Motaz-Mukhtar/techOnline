#!/usr/bin/env python3
import modules
from modules.Products.product import Product
from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from flask_login import UserMixin



class Customer(UserMixin, BaseModel, Base):
    """
        Customer Class

        Attributes:
            full_name (str):
            email (str):
            password (str):
            profile_avatar (text):
            order_status (bool):
            address (str): 
    """
    __tablename__ = 'customers'
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    profile_avatar = Column(Text, default="")
    order_status = Column(Boolean, default=False)
    address = Column(String(128))
    products = relationship('Product',
                            backref='customer',
                            cascade='delete') #type: ignore
    
    @property
    def products(self):
        """Getter for list of all customer products"""
        product_list = []
        all_products = modules.storage.all(Product)
        for product in all_products.values():
            if product.customer_id == self.id:
                product_dict = product.to_dict()
                product_dict['product_image'] = f'http://127.0.0.1:5000/product_img/{product.id}'
                product_list.append(product_dict)
        return product_list