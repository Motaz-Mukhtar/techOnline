#!/usr/bin/python3
"""Create BaseModel Class"""
import uuid
from datetime import datetime


class BaseModel:
    """
        BaseModel Class

        Attributes:
            id(int) => using uuid4() to generate random ID
            created_at(datetime) => The time it was created
            updated_at(datetime) => The time it was updated

    """
    def __init__(self, **kwargs):
        self.id = uuid.uuid4()
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if kwargs:
            for key, val in kwargs.items():
                if key == "created_at" or key == "updated_at":
                    val = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S.%f")
                setattr(self, key, val)

    def __str__(self):
        """
            Return class type and id
        """
        return '{}.{}'.format(type(self).__name__, self.id) 