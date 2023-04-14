#!/usr/bin/env python3
"""Create BaseModel Class"""
import uuid
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime
import modules
import json


Base = declarative_base()


class BaseModel:
    """
        BaseModel Class

        Attributes:
            id(int): using uuid4() to generate random ID
            created_at(datetime): The time it was created
            updated_at(datetime): The time it was updated
    """
    id = Column(String(60), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow())
    updated_at = Column(DateTime, default=datetime.utcnow())

    def __init__(self, *args, **kwargs):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if kwargs:
            for key, val in kwargs.items():
                if key == "created_at" or key == "updated_at":
                    val = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S.%f")
                setattr(self, key, val)

    def to_dict(self):
        """Returns dictionary containing
        all keys/values of the instance:"""
        my_dict = self.__dict__.copy()
        my_dict['__class__'] = str(type(self).__name__)
        my_dict['created_at'] = self.created_at.isoformat()
        my_dict['updated_at'] = self.updated_at.isoformat()
        my_dict.pop("_sa_instance_state", None)
        my_dict.pop('password', None)
        return my_dict

    def save(self):
        """ Save class instnace """
        self.updated_at = datetime.utcnow()
        modules.storage.new(self)
        modules.storage.save()


    def delete(self):
        """ Delete class instnace """
        modules.storage.delete(self)

    def __str__(self):
        """
            Return class type and id
        """
        instnace_dict = self.__dict__.copy()
        instnace_dict.pop('_sa_instance_state', None)
        return "[{}] ({}) {}".format(type(self).__name__, self.id, instnace_dict)
