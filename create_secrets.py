import json
from getpass import getpass
from pathlib import Path


def main():
    key = getpass('Enter your EIA API key: ').strip()
    secrets = {'EIA_API_KEY': key}
    secrets_path = Path(__file__).resolve().parent / 'secrets.json'
    with open(secrets_path, 'w', encoding='utf-8') as f:
        json.dump(secrets, f)
    print(f'Secrets written to {secrets_path}')


if __name__ == '__main__':
    main()

