#!/usr/bin/env python3
import argparse
import json
import math
import re


def load_shards(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_section_map(shards):
    return {section.get("id"): section for section in shards.get("sections", [])}


def search_by_keyword(shards, section_map, keyword):
    matches = []
    index = shards.get("index", {}).get("keywords", {})
    for slug in index.get(keyword, []):
        section = section_map.get(slug)
        if section:
            matches.append(section)
    return matches


def search_by_regex(shards, pattern, flags=0):
    regex = re.compile(pattern, flags)
    results = []
    for section in shards.get("sections", []):
        if regex.search(section.get("content", "")):
            results.append(section)
    return results


def search_by_bm25(shards, section_map, query):
    term_index = shards.get("index", {}).get("term_index", {})
    bm25_meta = shards.get("meta", {}).get("bm25", {})
    k1 = bm25_meta.get("k1", 1.5)
    b = bm25_meta.get("b", 0.75)
    doc_count = bm25_meta.get("doc_count", len(section_map))
    avgdl = bm25_meta.get("avgdl", 0) or 1

    query_terms = [term.lower() for term in re.findall(r"[A-Za-z0-9]+", query)]
    scores = {}

    for term in query_terms:
        postings = term_index.get(term, [])
        df = len(postings)
        if df == 0:
            continue
        idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
        for slug, tf in postings:
            section = section_map.get(slug)
            if not section:
                continue
            dl = section.get("token_count", 0) or 1
            denom = tf + k1 * (1 - b + b * (dl / avgdl))
            score = idf * (tf * (k1 + 1) / denom)
            scores[slug] = scores.get(slug, 0) + score

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [section_map[slug] for slug, _score in ranked]


def main():
    parser = argparse.ArgumentParser(description="Search shards.json for fast lookup.")
    parser.add_argument("--shards", required=True, help="Path to shards.json.")
    parser.add_argument("--keyword", help="Exact keyword from shards index.")
    parser.add_argument("--regex", help="Regex pattern to search within section content.")
    parser.add_argument("--query", help="Free-text query for BM25 ranking.")
    parser.add_argument("--top", type=int, default=5, help="Max results to print.")
    args = parser.parse_args()

    shards = load_shards(args.shards)
    section_map = build_section_map(shards)

    if args.keyword:
        results = search_by_keyword(shards, section_map, args.keyword)
    elif args.regex:
        results = search_by_regex(shards, args.regex, flags=re.IGNORECASE)
    elif args.query:
        results = search_by_bm25(shards, section_map, args.query)
    else:
        raise SystemExit("Provide --keyword, --regex, or --query.")

    for section in results[: args.top]:
        print(f"[{section['id']}] {section['title']}")


if __name__ == "__main__":
    main()
