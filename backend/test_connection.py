import psycopg
import concurrent.futures

prefixes = ["aws-0", "aws-1", "aws-2"]
regions = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ap-southeast-1", "ap-southeast-2", "ap-south-1",
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
    "eu-central-1", "eu-west-1", "eu-west-2", "eu-west-3", "eu-north-1",
    "ca-central-1", "sa-east-1"
]
ports = [5432, 6543]

combinations = []
for prefix in prefixes:
    for region in regions:
        for port in ports:
            combinations.append((prefix, region, port))

def check_combination(combo):
    prefix, region, port = combo
    host = f"{prefix}-{region}.pooler.supabase.com"
    conn_str = f"postgresql://postgres.uyrnzqlbxrmzwzuoxupl:xryVQXSfChDFj2tY@{host}:{port}/postgres"
    try:
        with psycopg.connect(conn_str, connect_timeout=3) as conn:
            return combo, "SUCCESS"
    except psycopg.OperationalError as e:
        err_msg = str(e)
        if "tenant/user" in err_msg and "not found" in err_msg:
            return combo, "NOT_FOUND"
        elif "password authentication failed" in err_msg:
            return combo, "AUTH_FAILED"
        else:
            return combo, f"ERROR: {err_msg[:80]}"
    except Exception as e:
        return combo, f"EXCEPTION: {str(e)[:80]}"

print("Scanning all Supabase regional poolers for project 'uyrnzqlbxrmzwzuoxupl'...")
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    results = executor.map(check_combination, combinations)

found = False
for combo, status in results:
    prefix, region, port = combo
    if status in ["SUCCESS", "AUTH_FAILED"]:
        print(f"\nFOUND IT! Host: {prefix}-{region}.pooler.supabase.com on Port: {port} (Status: {status})")
        found = True
        break

if not found:
    print("\nCould not find regional pooler connection.")
