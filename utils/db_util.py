import psycopg2
import pandas as pd

class PostgreSQLDatabase:
    def __init__(self, username, password, host, port, database_name):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database_name = database_name
        self.conn = None

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
            self.conn = None

    def get_cursor(self):
        if self.conn is not None:
            try:
                return self.conn.cursor()
            except psycopg2.OperationalError as e:
                print(f"Cursor creation failed: {e}")
                return None
        return None

    def create_table(self, table_name, columns):
        cursor = self.get_cursor()
        if cursor:
            try:
                query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                cursor.execute(query)
                self.conn.commit()
            except psycopg2.OperationalError as e:
                print(f"Table creation failed: {e}")
            finally:
                cursor.close()

    def delete_table(self, table_name):
        cursor = self.get_cursor()
        if cursor:
            try:
                query = f"DROP TABLE IF EXISTS {table_name}"
                cursor.execute(query)
                self.conn.commit()
                print(f"Table {table_name} deleted successfully.")
            except psycopg2.OperationalError as e:
                print(f"Table deletion failed: {e}")
            finally:
                cursor.close()


    def insert_data(self, table_name, data):
        cursor = self.get_cursor()
        if cursor:
            try:
                columns = list(data.keys())
                values = list(data.values())
                placeholders = ', '.join(['%s'] * len(values))  # Create placeholders for parameterized query
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                self.conn.commit()
            except psycopg2.OperationalError as e:
                print(f"Insertion failed: {e}")

            except Exception as e:
                print('EXCEPTION', e)
                pass
            finally:
                cursor.close()

    def update_or_insert(self, table_name, data):
        """
        Updates or inserts data based on hash and confirmation progress.
        Assumes data is a dictionary containing all necessary columns including hash and confirmationProgress.
    
        :param table_name: Name of the table to update or insert into.
        :param data: Data dictionary where keys are column names and values are data values.
        """
        hash = data['hash']
        new_confirmation = data['confirmationProgress']
        cursor = self.get_cursor()
        if cursor:
            try:
                # First, try to fetch the existing row with the same hash.
                cursor.execute("SELECT * FROM {} WHERE hash = %s".format(table_name), (hash,))
                existing_row = cursor.fetchone()
    
                if existing_row:
                    existing_confirmation = existing_row[4]  # Assuming confirmationProgress is the 5th column in the table
                    if new_confirmation > existing_confirmation:
                        # If new confirmation is greater, update the row.
                        columns = ', '.join([f"{key} = %s" for key in data.keys()])
                        values = list(data.values())
                        cursor.execute(f"UPDATE {table_name} SET {columns} WHERE hash = %s", values + [hash])
                else:
                    # If no existing row, insert new.
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join(['%s'] * len(data))
                    cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(data.values()))
    
                self.conn.commit()
            except psycopg2.OperationalError as e:
                print(f"Database operation failed: {e}")
            finally:
                cursor.close()



    def fetch_data(self, table_name, columns='*', where=None):
        """
        Fetches data from the specified table.
    
        :param table_name: Name of the table to fetch data from.
        :param columns: Columns to fetch, defaults to '*'.
        :param where: Optional WHERE clause to filter results.
        :return: A list of tuples containing the data fetched, or an empty list if no data.
        """
        cursor = self.get_cursor()
        if cursor:
            try:
                query = f"SELECT {', '.join(columns) if isinstance(columns, list) else columns} FROM {table_name}"
                if where:
                    query += f" WHERE {where}"
                return pd.read_sql_query(query, self.conn)
         
            except psycopg2.OperationalError as e:
                print(f"Data fetch failed: {e}")
            finally:
                cursor.close()
        return pd.DataFrame()


    def close(self):
        if self.conn:
            self.conn.close()

# Example usage
if __name__ == '__main__':
    database = PostgreSQLDatabase('marctheshark', 'password', 'localhost', 5432, 'sigmanaut-mining')
    database.connect()
    database.cursor()
    database.insert_data('your_table_name', ['column1', 'column2'], ('value1', 'value2'))
