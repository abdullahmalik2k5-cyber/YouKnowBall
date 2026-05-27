import psycopg

passwords = ["xryVQXSfChDFj2tY", "xryVQXSfChDFj2tY"] # We can try variations if needed

# Let's try direct connection
direct_url = "postgresql://postgres:xryVQXSfChDFj2tY@db.rdrjwibqllrpiuztbhgd.supabase.co:5432/postgres"
print(f"Testing direct connection: {direct_url.split('@')[-1]}")
try:
    with psycopg.connect(direct_url, connect_timeout=5) as conn:
        print("SUCCESS: Connected directly!")
except Exception as e:
    print(f"FAILED direct connection: {e}")

# Let's try pooler connections
pooler_urls = [
    "postgresql://postgres.rdrjwibqllrpiuztbhgd:xryVQXSfChDFj2tY@aws-1-ap-south-1.pooler.supabase.com:5432/postgres",
    "postgresql://postgres.rdrjwibqllrpiuztbhgd:xryVQXSfChDFj2tY@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
]

for url in pooler_urls:
    print(f"\nTesting pooler: {url.split('@')[-1]}")
    try:
        with psycopg.connect(url, connect_timeout=5) as conn:
            print("SUCCESS: Connected via pooler!")
    except Exception as e:
        print(f"FAILED pooler: {e}")
