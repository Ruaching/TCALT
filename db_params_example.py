class Encryption:
    def __init__(self):

        self.key = None  

    def db_info(self, key: str | None = None) -> str:

        DB = {
            "DB_HOST": "your-db-host",
            "DB_PORT": "your-db-port",
            "DB_USER": "your-db-user",
            "DB_PASSWORD": "your-db-password",
            "DB_NAME": "your-db-name",
        }

        if not key:
            raise ValueError("A key is needed for database validation.")

        if key not in DB:
            raise ValueError("Value entered is not in database parameters.")

        return DB[key]