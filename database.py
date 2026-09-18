import mysql.connector
from config import DB_CONFIG


# =========================================================
# KONEKSI DATABASE
# =========================================================

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# =========================================================
# INISIALISASI DATABASE
# =========================================================

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabel users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL UNIQUE,
            username VARCHAR(255),
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabel transactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            type ENUM('income', 'expense') NOT NULL,
            amount BIGINT NOT NULL,
            category VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            INDEX idx_telegram_id (telegram_id),
            INDEX idx_created_at (created_at)
        )
    """)

    # Tabel budgets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            category VARCHAR(100) NOT NULL,
            amount BIGINT NOT NULL,
            month VARCHAR(7) NOT NULL,

            UNIQUE KEY unique_budget (
                telegram_id,
                category,
                month
            )
        )
    """)

    # Tabel target tabungan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            name VARCHAR(255) NOT NULL,
            target_amount BIGINT NOT NULL,
            current_amount BIGINT DEFAULT 0,
            deadline DATE NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    cursor.close()
    conn.close()


# =========================================================
# USER
# =========================================================

def add_user(telegram_id, username, full_name):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO users
        (telegram_id, username, full_name)
        VALUES (%s, %s, %s)

        ON DUPLICATE KEY UPDATE
        username = VALUES(username),
        full_name = VALUES(full_name)
    """

    cursor.execute(
        query,
        (
            telegram_id,
            username,
            full_name
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# =========================================================
# TRANSAKSI
# =========================================================

def add_transaction(
    telegram_id,
    transaction_type,
    amount,
    category,
    description
):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO transactions
        (
            telegram_id,
            type,
            amount,
            category,
            description
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            telegram_id,
            transaction_type,
            amount,
            category,
            description
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# =========================================================
# RINGKASAN BULANAN
# =========================================================

def get_summary(telegram_id):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'income'
                        THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS income,

            COALESCE(
                SUM(
                    CASE
                        WHEN type = 'expense'
                        THEN amount
                        ELSE 0
                    END
                ),
                0
            ) AS expense

        FROM transactions

        WHERE telegram_id = %s

        AND MONTH(created_at) = MONTH(CURRENT_DATE())

        AND YEAR(created_at) = YEAR(CURRENT_DATE())
    """

    cursor.execute(
        query,
        (telegram_id,)
    )

    result = cursor.fetchone()

    income = result[0] or 0
    expense = result[1] or 0

    cursor.close()
    conn.close()

    return income, expense


# =========================================================
# RIWAYAT TRANSAKSI
# =========================================================

def get_transactions(telegram_id, limit=10):

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            type,
            amount,
            category,
            description,
            created_at

        FROM transactions

        WHERE telegram_id = %s

        ORDER BY created_at DESC

        LIMIT %s
    """

    cursor.execute(
        query,
        (
            telegram_id,
            limit
        )
    )

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


# =========================================================
# RESET DATA USER
# =========================================================

def reset_user_data(telegram_id):

    conn = get_connection()
    cursor = conn.cursor()

    # Hapus semua transaksi
    cursor.execute(
        """
        DELETE FROM transactions
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    # Hapus semua budget
    cursor.execute(
        """
        DELETE FROM budgets
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    # Hapus semua target tabungan
    cursor.execute(
        """
        DELETE FROM savings_goals
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    # Hapus user
    cursor.execute(
        """
        DELETE FROM users
        WHERE telegram_id = %s
        """,
        (telegram_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()