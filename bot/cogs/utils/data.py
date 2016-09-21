import os
import sqlite3


class BadQuery(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class Data:
    """The database object and queries/functions to go with it"""

    def __init__(self, name, **options):
        self.data_dir = 'data'
        if not os.path.isdir(self.data_dir):
            os.makedirs(self.data_dir)
        self.name = name
        self.file = '{}\{}'.format(self.data_dir, self.name)
        self.conn = None

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_connection(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.file)
            self.conn.row_factory = self.dict_factory
        return self.conn

    def close_connection(self):
        if self.conn is not None:
            self._save()
            self.conn.close()

    def _save(self):
        self.get_connection().commit()

    def execute_query(self, query, parameters=None):
        if not isinstance(query, str):
            raise BadQuery('The query needs to be a string. A {} was given'.format(type(query).__name__))
        c = self.get_connection().cursor()
        if isinstance(parameters, list):
            result = c.executemany(query, parameters)
        elif isinstance(parameters, tuple):
            result = c.execute(query, parameters)
        else:
            result = c.execute(query)
        self._save()
        return result.fetchall()
