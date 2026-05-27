import psycopg

local_urls = [
    "postgresql://postgres:postgres@localhost:5432/postgres",
    "postgresql://postgres:IpR40mmavxSaYmEW@localhost:5432/postgres",
    "postgresql://postgres:postgres@127.0.0.1:5432/postgres",
    "postgresql://postgres:admin@localhost:5432/postgres",
    "postgresql://postgres:root@localhost:5432/postgres",
    "postgresql://postgres@localhost:5432/postgres"
]

for url in local_urls:
    print(f"Testing local connection: {url}")
    try:
        with psycopg.connect(url, connect_timeout=1) as conn:
            print("SUCCESS! Connected to local PostgreSQL.")
            exit(0)
    except Exception as e:
        print(f"FAILED: {e}")

print("No local PostgreSQL detected running on port 5432.")
exit(1)
