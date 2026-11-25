import argparse
import asyncio
import re
from a2a_client import AGENTS, send

CASES = {
    'burger': [('What is the price of one Classic Cheeseburger?', '8.50'), ('Calculate the total for two Classic Cheeseburgers and one Double Cheeseburger. Give a price breakdown.', '28.00')],
    'pizza': [('What is the price of one Margherita Pizza?', '10.00'), ('Calculate the total for two Margherita Pizzas and one Pepperoni Pizza. Give a price breakdown.', '34.00')],
}

async def run(agents, delay=10, full=False, show_json=False):
    if delay < 0:
        raise ValueError('Delay must be nonnegative')
    cases = [(name, query, expected) for name in agents for query, expected in CASES[name][:2 if full else 1]]
    for index, (name, query, expected) in enumerate(cases):
        if index:
            print(f'Pausing {delay:g} seconds...', flush=True)
            await asyncio.sleep(delay)
        print(f'\n{name}: {query}', flush=True)
        result = await send(AGENTS[name], query + ' Use euros with two decimal places. Do not create an order.', show_json=show_json)
        print(result['state'], result['task_id'])
        print(result['text'])
        # Smoke check, not a semantic validation of the whole answer.
        normalized = result['text'].replace(',', '.')
        if not re.search(r'(?<![\d.])' + re.escape(expected) + r'(?!\d)', normalized) or not re.search(r'€|\bEUR\b|\beuros?\b', normalized, re.I):
            raise RuntimeError(f'Expected EUR {expected}; inspect response above')
        if re.search(r'\bIDR\b|rupiah', normalized, re.I):
            raise RuntimeError('Unexpected legacy currency')
        print('PASS: completed task and expected EUR amount')


def main(agents=('burger', 'pizza')):
    parser = argparse.ArgumentParser(description='Sequential, read-only seller smoke tests')
    parser.add_argument('--delay', type=float, default=10)
    parser.add_argument('--full', action='store_true', help='Also test price calculations')
    parser.add_argument('--json', action='store_true', help='Print protocol requests and responses')
    args = parser.parse_args()
    asyncio.run(run(agents, args.delay, args.full, args.json))

if __name__ == '__main__':
    main()
