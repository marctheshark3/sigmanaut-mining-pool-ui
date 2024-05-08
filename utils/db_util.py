import psycopg2
import pandas as pd
import time 
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

    def get_db_size(self):
        query = f"SELECT pg_size_pretty(pg_database_size('{self.database_name}'));"
        cursor = self.get_cursor()
        cursor.execute(query)
    
        # Fetch the result
        size = cursor.fetchone()[0]
        return size

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

    def delete_data_in_batches(self, table_name, batch_size=10000):
        cursor = self.get_cursor()
        if cursor:
            try:
                # First, determine the total number of rows in the table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_rows = cursor.fetchone()[0]
                num_batches = (total_rows + batch_size - 1) // batch_size  # Calculate how many batches are needed

                for batch in range(num_batches):
                    # Use ROW_NUMBER() to select a range of rows within the current batch
                    delete_query = f"""
                    DELETE FROM {table_name}
                    WHERE ctid IN (
                        SELECT ctid FROM (
                            SELECT ctid, ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) as rn
                            FROM {table_name}
                        ) sub
                        WHERE rn BETWEEN {batch * batch_size + 1} AND {(batch + 1) * batch_size}
                    );
                    """
                    cursor.execute(delete_query)
                    self.conn.commit()
                    print(f"Batch {batch + 1}/{num_batches}: Deleted up to {batch_size} rows from {table_name}")

                    # Avoid overloading the database with a small delay
                    time.sleep(1)

            except psycopg2.OperationalError as e:
                print(f"Batch deletion failed: {e}")
                self.conn.rollback()
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

    # def update_or_insert(self, table_name, data):
    #     """
    #     Updates or inserts data based on hash and confirmation progress.
    #     Assumes data is a dictionary containing all necessary columns including hash and confirmationProgress.
    
    #     :param table_name: Name of the table to update or insert into.
    #     :param data: Data dictionary where keys are column names and values are data values.
    #     """
    #     hash = data['hash']
    #     new_confirmation = data['confirmationProgress']
    #     cursor = self.get_cursor()
    #     flag = False
    #     if cursor:
    #         try:
    #             # First, try to fetch the existing row with the same hash.
    #             cursor.execute("SELECT * FROM {} WHERE hash = %s".format(table_name), (hash,))
    #             existing_row = cursor.fetchone()
    
    #             if existing_row:
    #                 existing_confirmation = existing_row[4]  # Assuming confirmationProgress is the 5th column in the table
    #                 if new_confirmation > existing_confirmation:
    #                     # If new confirmation is greater, update the row.
    #                     columns = ', '.join([f"{key} = %s" for key in data.keys()])
    #                     values = list(data.values())
    #                     cursor.execute(f"UPDATE {table_name} SET {columns} WHERE hash = %s", values + [hash])
    #                     flag = True
    #             else:
    #                 # If no existing row, insert new.
    #                 columns = ', '.join(data.keys())
    #                 placeholders = ', '.join(['%s'] * len(data))
    #                 cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(data.values()))
    #                 flag = True
    
    #             self.conn.commit()
    #         except psycopg2.OperationalError as e:
    #             print(f"Database operation failed: {e}")
    #         finally:
    #             cursor.close()
    #     return flag

    def update_or_insert(self, table_name, data, key_columns):
        """
        Updates or inserts data based on specified key columns.
        Assumes data is a dictionary containing all necessary columns.
    
        :param table_name: Name of the table to update or insert into.
        :param data: Data dictionary where keys are column names and values are data values.
        :param key_columns: A list of column names to use as keys for identifying existing records.
        """
        cursor = self.get_cursor()
        flag = False
        if cursor:
            try:
                # Construct WHERE clause based on key columns
                where_clause = ' AND '.join([f"{col} = %s" for col in key_columns])
                key_values = [data[col] for col in key_columns]
    
                # First, try to fetch the existing row with the same keys.
                cursor.execute(f"SELECT * FROM {table_name} WHERE {where_clause}", key_values)
                existing_row = cursor.fetchone()
    
                if existing_row:
                    # Update the row if it exists.
                    columns = ', '.join([f"{key} = %s" for key in data.keys() if key not in key_columns])
                    values = [data[key] for key in data.keys() if key not in key_columns]
                    cursor.execute(f"UPDATE {table_name} SET {columns} WHERE {where_clause}", values + key_values)
                    flag = True
                else:
                    # Insert a new row if it doesn't exist.
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join(['%s'] * len(data))
                    cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(data.values()))
                    flag = True
    
                self.conn.commit()
            except psycopg2.OperationalError as e:
                print(f"Database operation failed: {e}")
            finally:
                cursor.close()
        return flag




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
