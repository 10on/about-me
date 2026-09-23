"""Save public giscus discussion reaction counts for the static feed.

Run with GITHUB_TOKEN set. GitHub Actions refreshes the snapshot periodically.
"""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'data' / 'reactions.json'
CATEGORY_ID = 'DIC_kwDOSG9VXc4DGOlc'
QUERY = '''
query($cursor: String, $categoryId: ID!) {
  repository(owner: "10on", name: "about-me") {
    discussions(first: 100, after: $cursor, categoryId: $categoryId) {
      pageInfo { hasNextPage endCursor }
      nodes { title url reactions { totalCount } }
    }
  }
}
'''


def fetch_page(token, cursor):
    payload = json.dumps({
        'query': QUERY,
        'variables': {'cursor': cursor, 'categoryId': CATEGORY_ID},
    }).encode('utf-8')
    request = Request(
        'https://api.github.com/graphql',
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'User-Agent': 'about-me-reaction-snapshot',
        },
    )
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    if result.get('errors'):
        raise RuntimeError(f'GitHub GraphQL error: {result["errors"]}')
    return result['data']['repository']['discussions']


def main():
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise SystemExit('GITHUB_TOKEN is required')

    reactions = {}
    cursor = None
    while True:
        page = fetch_page(token, cursor)
        for discussion in page['nodes']:
            term = discussion['title']
            if term.startswith(('note:', 'article:')):
                reactions[term] = {
                    'count': discussion['reactions']['totalCount'],
                    'url': discussion['url'],
                }
        if not page['pageInfo']['hasNextPage']:
            break
        cursor = page['pageInfo']['endCursor']
        if not cursor:
            raise RuntimeError('GitHub GraphQL pagination cursor is missing')

    content = json.dumps(reactions, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != content:
        OUTPUT.write_text(content, encoding='utf-8')
    print(f'{len(reactions)} discussions with reaction counters')


if __name__ == '__main__':
    main()
