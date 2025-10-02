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
    profile_avatar = Column(String(255), default="")  # Store file path or URL
    profile_avatar_filename = Column(String(255))  # Store original filename for management
    order_status = Column(Boolean, default=False)
    address = Column(String(128))
    products = relationship('Product',
                            backref='customer',
                            cascade='delete') #type: ignore
    reviews = relationship('Review', back_populates='customer', cascade='all, delete-orphan')
    
    @property
    def products(self):
        """Getter for list of all customer products"""
        product_list = []
        all_products = modules.storage.all(Product)
        for product in all_products.values():
            if product.customer_id == self.id:
                product_dict = product.to_dict()
                # Use the stored image URL or provide a default
                if product.product_image:
                    product_dict['product_image'] = product.product_image
                else:
                    product_dict['product_image'] = '/static/images/default-product.png'
                product_list.append(product_dict)
        return product_list