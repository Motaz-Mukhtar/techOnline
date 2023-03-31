
from modules.Customer.customer import Customer
from modules.Cart.cart import Cart
from modules.Order.order import Order
from modules.Products.product import Product
from modules.Review.review import Review
from modules.baseModel import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session


class DBStorage:
    """
        DBStorage Class:
            Sotre, delete and update data in the database
    """
    __session = None
    __engine = None

    def __init__(self):
        """
        """
        self.__engine = create_engine("sqlite:///{}.db".format("test"))

    def all(self, cls=None):
        """
            query in the current database session, if cls is None
            query all type of ojbects, else query all objects
            depending on the class names.
        """
        if cls is None:
            obj = self.__session.query(Customer).all()
            obj.extend(self.__session.query(Review).all())
            obj.extend(self.__session.query(Order).all())
            obj.extend(self.__session.query(Product).all())
            obj.extend(self.__session.query(Cart).all())
        else:
            if type(cls) == str:
                cls = eval(cls)
            obj = self.__session.query(cls)
        return {"{}.{}".format(type(val).__name__, val.id): val for val in obj}

    def save(self):
        """
            Update all changes in the database
        """
        self.__session.commit()

    def delete(self, obj=None):
        """
            Delete the given instnace from database
        """
        if obj is not None:
            self.__session.delete(obj)

    def new(self, obj):
        """
            Add new instnace to the database
        """
        self.__session.add(obj)

    def close(self):
        """
            End up the currnet Session
        """
        self.__session.close()

    def reload(self):
        """
            create new Session
        """
        Base.metadata.create_all(self.__engine)
        new_session = sessionmaker(bind=self.__engine,
                                    expire_on_commit=False)
        Session = scoped_session(new_session)
        self.__session = Session()

    def close(self):
        """
            Closing the currnet Session
        """
        self.__session.close()