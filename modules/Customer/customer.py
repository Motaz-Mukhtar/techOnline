from modules.baseModel import BaseModel
from modules.baseModel import Base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Boolean


class Customer(BaseModel, Base):
    """
        Customer Class

        Attributes:
            full_name (str):
            email (str):
            password (str):
            profile_avatar (str):
            order_status (bool):
            address (str): 
    """
    __tablename__ = 'customers'
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False, unique=True)
    password = Column(String(128), nullable=False)
    # must put 'default' attribute as an default image for customer
    profile_avatar = Column(String(128), default="")
    order_status = Column(Boolean, default=False)
    address = Column(String(128))