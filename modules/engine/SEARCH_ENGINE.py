#!/usr/bin/python3
"""Search Class"""
import modules


class Search:
    """
        Define Search Class
    """
    def search_query_by_name(obj):
        """
            Search query by name, and return list of queries.
        """
        modules.storage.reload()

        result = modules.storage.__session.query(obj).filter(obj.name.ilike(f'%{obj}%')).all()
        modules.storage.__session.close()

        return result

    def search_query_by_id(obj=None, id=None):
        """
            Search query by id, and return the result.
        """
        modules.storage.reload()

        result = modules.storage.__session.query(obj).filter(id==id).all()
        modules.storage.__session.close()

        return result