#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""取当天的 GitHub 候选项目。不需要令牌，只用公开搜索 API。
输出 JSON：{"generated_at": "...", "items": [ ... ]}
"""
import json
import urllib.request
import urllib.parse
from datetime import date, timedelta

UA = {"User-Agent": "gh-daily-brief", "Accept": "application/vnd.github+json"}
API = "https://api.github.com/search/repositories"


def search(q, per_page=30):
    url = API + "?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": per_page}
    )
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r).get("items", [])
        except Exception:
            if attempt == 0:
                continue
            return []
    return []


def main():
    today = date.today()
    qs = [
        "created:>%s stars:>80" % (today - timedelta(days=7)).isoformat(),
        "created:>%s stars:>300" % (today - timedelta(days=30)).isoformat(),
        "pushed:>%s stars:>2000" % (today - timedelta(days=1)).isoformat(),
    ]

    seen, items = set(), []
    for q in qs:
        for it in search(q):
            full = it.get("full_name")
            if not full or full in seen:
                continue
            seen.add(full)
            created = (it.get("created_at") or "")[:10]
            try:
                age_days = max((today - date.fromisoformat(created)).days, 1)
            except Exception:
                age_days = 999
            stars = it.get("stargazers_count", 0)
            items.append(
                {
                    "repo": full,
                    "desc": it.get("description") or "",
                    "stars": stars,
                    "forks": it.get("forks_count", 0),
                    "open_issues": it.get("open_issues_count", 0),
                    "age_days": age_days,
                    "stars_per_day": round(stars / age_days, 1),
                    "created": created,
                    "pushed": (it.get("pushed_at") or "")[:10],
                    "language": it.get("language") or "",
                    "topics": (it.get("topics") or [])[:8],
                    "url": it.get("html_url"),
                }
            )

    # 建库超过 5 天的项目，star 要够高才值得占一个名额
    items = [x for x in items if x["age_days"] <= 5 or x["stars"] >= 3000]
    items.sort(key=lambda x: x["stars_per_day"], reverse=True)

    print(
        json.dumps(
            {"generated_at": today.isoformat(), "count": len(items), "items": items[:40]},
            ensure_ascii=False,
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
