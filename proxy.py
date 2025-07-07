from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = Flask(__name__)

# --- Database config from environment ---
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "5439")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

def get_connection():
    """Establishes and returns a database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        sslmode="require"
    )

@app.route("/")
def index():
    return "Proxy API is running. Access /signatures for data."

@app.route("/signatures", methods=["GET"])
def fetch_signatures():
    """Fetches and pivots signature data into one row per respondent."""
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # This query now pivots the data using GROUP BY and CASE statements.
        cur.execute("""
            SELECT
                a.first_name,
                a.last_name,
                MAX(CASE WHEN fn.name = 'EPA_Supporter_Type' THEN fv.value END) AS "Supporter Type",
                MAX(CASE WHEN fn.name = 'EPA_Professional_Position' THEN fv.value END) AS "Professional Position",
                MAX(CASE WHEN fn.name = 'EPA_Professional_Category' THEN fv.value END) AS "Professional Category",
                MAX(CASE WHEN fn.name = 'Title' THEN fv.value END) AS "Title",
                MAX(CASE WHEN fn.name = 'Institution / Organization' THEN fv.value END) AS "Institution / Organization",
                MAX(CASE WHEN fn.name = 'EPA_Notable' THEN fv.value END) AS "Notable"
            FROM 
                group_326944_indexed.answers a
            LEFT JOIN 
                group_326944_indexed.field_values fv ON a.user_id = fv.user_id
            LEFT JOIN
                group_326944_indexed.field_names fn ON fv.field_name_id = fn.id
            WHERE
                a.form_id = 706308
            GROUP BY
                a.id, a.first_name, a.last_name, a.created_at
            ORDER BY 
                a.created_at DESC;
        """)
        
        rows = cur.fetchall()
        
        # Create a list of dictionaries from the query result
        colnames = [desc[0] for desc in cur.description]
        result = [dict(zip(colnames, row)) for row in rows]

        return jsonify(result)
    
    except Exception as e:
        # Print the specific error to your terminal/console for debugging
        print(f"AN ERROR OCCURRED: {e}")
        return jsonify({
            "error_type": type(e).__name__,
            "error_message": str(e)
        }), 500

    finally:
        # Ensure the cursor and connection are closed
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting server on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)

