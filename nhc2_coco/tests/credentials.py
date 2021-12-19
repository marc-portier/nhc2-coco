from dotenv import load_dotenv
import os

load_dotenv()

HOST = os.environ.get('NHC2_HOST', 'nhc2.local')
PORT = int(os.environ.get('NHC2_PORT', 8883))  # or 8884 for hobby api

USER = os.environ.get('NHC2_UUID')
PASS = os.environ.get('NHC2_PASS')


if __name__ == "__main__":
    print(f"Credentials for nhc2 @ host:port='{HOST}:{PORT}' are user:pass='{USER}:{PASS}'")
