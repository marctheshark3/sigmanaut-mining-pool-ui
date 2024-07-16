import psycopg2
from psycopg2 import sql
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
        if cursor:
            cursor.execute(query)
            size = cursor.fetchone()[0]
            cursor.close()
            return size
        return None

    def create_database(self, new_db_name, superuser, superuser_password):
        # Connect to the default 'postgres' database to create a new database
        default_conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=superuser,
            password=superuser_password,
            dbname='postgres'  # Connect to the default 'postgres' database
        )
        default_conn.autocommit = True  # Enable autocommit mode
        cursor = default_conn.cursor()

        try:
            # Create the new database
            cursor.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(new_db_name)))
            print(f"Database {new_db_name} created successfully.")
        except psycopg2.OperationalError as e:
            print(f"Database creation failed: {e}")
        finally:
            cursor.close()
            default_conn.close()

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

    def delete_db(self, superuser, superuser_password):
        default_conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            user=superuser,
            password=superuser_password,
            dbname='postgres'  # Connect to the default 'postgres' database
        )
        default_conn.autocommit = True
        cursor = default_conn.cursor()
    
        try:
            # Terminate active connections to the database
            cursor.execute(sql.SQL("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid();
            """), [self.database_name])
    
            # Drop the database
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {};").format(sql.Identifier(self.database_name)))
            print(f"Database {self.database_name} deleted successfully.")
        except psycopg2.errors.InsufficientPrivilege as e:
            print(f"Insufficient privileges to delete database {self.database_name}: {e}")
        except psycopg2.OperationalError as e:
            print(f"Database deletion failed: {e}")
        finally:
            cursor.close()
            default_conn.close()

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
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_rows = cursor.fetchone()[0]
                num_batches = (total_rows + batch_size - 1) // batch_size

                for batch in range(num_batches):
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
                placeholders = ', '.join(['%s'] * len(values))
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                self.conn.commit()
            except psycopg2.OperationalError as e:
                print(f"Insertion failed: {e}")
            finally:
                cursor.close()

    def update_or_insert(self, table_name, data, key_columns):
        cursor = self.get_cursor()
        if cursor:
            try:
                where_clause = ' AND '.join([f"{col} = %s" for col in key_columns])
                key_values = [data[col] for col in key_columns]
    
                cursor.execute(f"SELECT * FROM {table_name} WHERE {where_clause}", key_values)
                existing_row = cursor.fetchone()
    
                if existing_row:
                    columns = ', '.join([f"{key} = %s" for key in data.keys() if key not in key_columns])
                    values = [data[key] for key in data.keys() if key not in key_columns]
                    cursor.execute(f"UPDATE {table_name} SET {columns} WHERE {where_clause}", values + key_values)
                else:
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join(['%s'] * len(data))
                    cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(data.values()))
    
                self.conn.commit()
            except psycopg2.OperationalError as e:
                print(f"Database operation failed: {e}")
            finally:
                cursor.close()

    def fetch_data(self, table_name, columns='*', where=None):
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
    database = PostgreSQLDatabase('marctheshark', 'password', 'localhost', 5432, 'mining-db')
    database.connect()

    # Example operations
    print(database.get_db_size())
    # database.create_table('your_table_name', ['column1 TEXT', 'column2 TEXT'])
    # database.insert_data('your_table_name', {'column1': 'value1', 'column2': 'value2'})
    # data = database.fetch_data('your_table_name')
    # print(data)

    # Delete database with superuser credentials
    superuser = 'postgres'  # Default superuser
    superuser_password = 'password'  # The new password you set
    database.delete_db(superuser, superuser_password)

    database.close()
