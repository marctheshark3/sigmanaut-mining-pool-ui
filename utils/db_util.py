class PostgreSQLDatabase:
    def __init__(self, username, password, host, port, database_name):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database_name = database_name

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                dbname=self.database_name
            )
        except psycopg2.OperationalError as e:
            print(f"Connection failed: {e}")
        finally:
            if self.conn is not None:
                self.conn.close()
                self.conn = None

    def cursor(self):
        try:
            self.cursor = self.conn.cursor()
        except psycopg2.OperationalError as e:
            print(f"Cursor creation failed: {e}")
        finally:
            if self.cursor is not None:
                self.cursor.close()
                self.cursor = None
                self.connect()

    def create_table(self, table_name, columns):
        try:
            if self.conn is not None and self.cursor is not None:
                query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join([f'{column} VARCHAR(255)' for column 
in columns])})"
                self.cursor.execute(query)
                self.conn.commit()
        except psycopg2.OperationalError as e:
            print(f"Table creation failed: {e}")
        finally:
            if self.cursor is not None:
                self.cursor.close()

    def insert_data(self, table_name, columns, values):
        try:
            if self.conn is not None and self.cursor is not None:
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * 
len(values))})"
                self.cursor.execute(query, tuple(values))
                self.conn.commit()
        except psycopg2.OperationalError as e:
            print(f"Insertion failed: {e}")
        finally:
            if self.cursor is not None:
                self.cursor.close()

# Example usage
if __name__ == '__main__':
    database = PostgreSQLDatabase('marctheshark', 'password', 'localhost', 5432, 'sigmanaut-mining')
    database.connect()
    database.cursor()
    database.insert_data('your_table_name', ['column1', 'column2'], ('value1', 'value2'))
