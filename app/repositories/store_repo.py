from app.db.mysql import fetch_all, execute


def list_stores():
    return fetch_all(
        """
        SELECT id, name
        FROM store
        ORDER BY id DESC
        """
    )


def create_store(name: str):
    execute(
        """
        INSERT INTO store (name)
        VALUES (%s)
        """,
        (name,),
    )
