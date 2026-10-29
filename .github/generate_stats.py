import html
import json
import os
import urllib.request

USER = os.environ["USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]


def api(url, data=None):
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


user = api(f"https://api.github.com/users/{USER}")

repos, page = [], 1
while True:
    batch = api(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}")
    repos += batch
    if len(batch) < 100:
        break
    page += 1

stars = sum(r["stargazers_count"] for r in repos)

langs = {}
for r in repos:
    if r["fork"]:
        continue
    for name, size in api(r["languages_url"]).items():
        langs[name] = langs.get(name, 0) + size

query = json.dumps({"query": 'query { user(login: "%s") { contributionsCollection { totalCommitContributions restrictedContributionsCount } } }' % USER}).encode()
c = api("https://api.github.com/graphql", query)["data"]["user"]["contributionsCollection"]
commits = c["totalCommitContributions"] + c["restrictedContributionsCount"]

total = sum(langs.values()) or 1
items = sorted(langs.items(), key=lambda x: -x[1])[:3]
rest = total - sum(v for _, v in items)
if rest > 0:
    items.append(("Other", rest))

colors = ["#3572A5", "#00a6a6", "#bc8cff"]
bar, legend, x = "", "", 40
for i, (name, size) in enumerate(items):
    color = "#8b949e" if name == "Other" else colors[i]
    w = 760 - x if i == len(items) - 1 else round(720 * size / total)
    bar += f'<rect x="{x}" y="252" width="{w}" height="10" fill="{color}"/>'
    x += w
    lx = 46 + i * 140
    legend += (
        f'<circle cx="{lx}" cy="290" r="5" fill="{color}"/>'
        f'<text x="{lx + 12}" y="295" font-size="13" fill="#c9d1d9">{html.escape(name)} '
        f'<tspan fill="#8b949e">{round(100 * size / total)}%</tspan></text>'
    )

stats = [
    (user["public_repos"], "Repositories"),
    (stars, "Stars Earned"),
    (commits, "Commits (1 yr)"),
    (user["followers"], "Followers"),
]
tiles = ""
for i, (value, label) in enumerate(stats):
    tx = 40 + i * 184
    cx = tx + 84
    tiles += (
        f'<rect x="{tx}" y="112" width="168" height="94" rx="12" fill="#161b22" stroke="#30363d"/>'
        f'<text x="{cx}" y="156" font-size="32" font-weight="700" fill="url(#accent)" text-anchor="middle">{value:,}</text>'
        f'<text x="{cx}" y="184" font-size="13" fill="#8b949e" text-anchor="middle">{label}</text>'
    )

name = html.escape(user["name"] or USER)

svg = f"""<svg width="800" height="320" viewBox="0 0 800 320" fill="none" xmlns="http://www.w3.org/2000/svg" font-family="-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif">
<defs>
<linearGradient id="accent" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#58a6ff"/><stop offset="1" stop-color="#bc8cff"/></linearGradient>
<clipPath id="bar"><rect x="40" y="252" width="720" height="10" rx="5"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="799" height="319" rx="16" fill="#0d1117" stroke="#30363d"/>
<text x="40" y="56" font-size="24" font-weight="700" fill="#f0f6fc">GitHub Stats</text>
<text x="40" y="80" font-size="14" fill="#8b949e">{name} · @{html.escape(USER)}</text>
<rect x="40" y="92" width="48" height="3" rx="1.5" fill="url(#accent)"/>
{tiles}
<text x="40" y="238" font-size="14" font-weight="600" fill="#c9d1d9">Top Languages</text>
<g clip-path="url(#bar)"><rect x="40" y="252" width="720" height="10" fill="#21262d"/>{bar}</g>
{legend}
</svg>
"""

with open("github-stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)