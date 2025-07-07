import os
import psycopg2
import json
import requests # You'll need to add this library

# --- Your Gist and GitHub Info ---
# Paste the ID from your Gist's URL
GIST_ID = "YOUR_GIST_ID" 
# This will be a secret environment variable
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") 

# --- Database config from environment ---
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "5439")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

def fetch_data():
    """Connects to the DB and runs the query."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
            user=DB_USER, password=DB_PASS, sslmode="require"
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT
                a.first_name,
                a.last_name,
                MAX(CASE WHEN fn.name = 'Title' THEN fv.value END) AS "Title",
                MAX(CASE WHEN fn.name = 'Institution / Organization' THEN fv.value END) AS "Institution / Organization"
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
        colnames = [desc[0] for desc in cur.description]
        result = [dict(zip(colnames, row)) for row in rows]
        return result
    finally:
        if conn:
            conn.close()

def update_gist(data):
    """Updates the specified GitHub Gist with new data."""
    gist_url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    payload = {
        "files": {
            "signatures.json": {
                "content": json.dumps(data, indent=2)
            }
        }
    }
    
    response = requests.patch(gist_url, headers=headers, json=payload)
    response.raise_for_status() # Raises an error if the request fails
    print("Gist updated successfully.")

if __name__ == "__main__":
    print("Fetching data...")
    signatures_data = fetch_data()
    print(f"Found {len(signatures_data)} signatures.")
    
    if GITHUB_TOKEN and GIST_ID != "YOUR_GIST_ID":
        print("Updating Gist...")
        update_gist(signatures_data)
    else:
        print("Skipping Gist update (token or ID not set).")

