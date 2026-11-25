import json
from a2a_client import AGENTS, discover

def main():
    for name, url in AGENTS.items():
        print(name, json.dumps(discover(url), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
