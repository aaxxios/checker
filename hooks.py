import itertools
import urllib
from collections import namedtuple

import requests
from bs4 import BeautifulSoup
from googlesearch import search

from .cleanup import (
    calculate_unique_score_for_chunk,
    generate_ngrams,
    html_to_basic_text,
    remove_special_characters,
    split_into_chunks,
)


def get_queries(url, num_queries=3):
    scored_chunks = []
    initial = get_htmlparsed_snippets(url)

    # Return now if there's been a failure (e.g. a HTTP 404 code)
    if initial["success"] is False:
        return initial

    for i in initial["data"]:
        # Cleanup string by stripping out whitespace, special chars etc
        text, score = remove_special_characters(i[0]), i[1]

        # Improve scores by adding points for the overall number of words for this snippet
        text_len = len(text.split())
        if 5 <= text_len < 8:
            score += 3
        elif 8 <= text_len < 20:
            score += 4
        elif 20 <= text_len < 100:
            score += 5
        elif text_len >= 100:
            score += 6

        for chunk in split_into_chunks(text):
            # Add 2 to the score since the HTML surrounding elements checks increase the scores c.f. other content types
            chunk_score = score + calculate_unique_score_for_chunk(chunk) + 2
            scored_chunks.append((chunk, chunk_score))

    return build_query_result(scored_chunks, num_queries, initial["source"])


# TODO This can return duplicates (e.g. <td><p>Test</p></td>); may need to remove duplicate sub-strings at a later date
def get_htmlparsed_snippets(url):
    """Scans a URL, gets the HTML text from obvious tags (e.g. p, li) and returns an initial score by also looking
    at the surrounding elements. Returns a tuple of boolean and result, e.g. for a success it'll return
    True and a list of tuples containing the text then the score."""
    tags = ["h3", "h4", "h5", "h6", "p", "li", "td"]
    num_surrounding = 3
    try:
        urlresult = requests.get(
            url,
            timeout=5,
            headers={
                "User-agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
                "Connection": "close",
            },
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        return {"success": False, "data": str(e)}

    if urlresult.status_code == 200:
        result = []
        html = urlresult.text
        soup = BeautifulSoup(html, "html.parser")
        candidates = soup.find_all(tags)
        for c in candidates:
            # For each candidate, check the previous and next N elements (n max 3).
            # If they contain 8 or more words, 3, 2 and 1 (desc) points
            candscore = 0

            for idx, prev in enumerate(
                itertools.islice(c.previous_elements, num_surrounding)
            ):
                prev_text = get_text_from_elem(prev)
                if prev_text.count(" ") >= 8:
                    candscore += (
                        num_surrounding - idx
                    )  # first iteration: 3-0 = 3 points, second iteration: 3-1 = 2 points etc

            for idx, next in enumerate(
                itertools.islice(c.next_elements, num_surrounding)
            ):
                next_text = get_text_from_elem(next)
                if next_text.count(" ") >= 8:
                    candscore += num_surrounding - idx

            result.append((get_text_from_elem(c), candscore))

        return {
            "success": True,
            "data": result,
            "source": html,
        }
    else:
        return {
            "success": False,
            "data": urlresult.status_code,
            "source": "",
        }


def get_text_from_elem(e):
    try:
        txt = e.get_text(" ", strip=True)
    except AttributeError:
        txt = elem
    return txt


def run_request(queries, exclude_urls):
    result = []
    headers = {"Ocp-Apim-Subscription-Key": "f0a1cf2c35e746c49679f5971ef9db70"}
    params = {"textDecoration": True, "textFormat": "HTML"}
    url = "https://api.bing.microsoft.com/v7.0/search"

    for query in queries:
        params["q"] = query
        api_result = requests.get(url, params=params, headers=headers)
        if api_result.status_code == 200:
            json = api_result.json()["webPages"]["value"]
            add_result(json, result, exclude_urls)

    return result


def add_result(row, result_list, excluded_urls):
    for api_row in row:
        if api_row["url"] not in excluded_urls:
            result_list.append(
                {
                    "displayUrl": api_row["displayUrl"],
                    "url": api_row["url"],
                }
            )


# Sort list; get top num_queries and return just the text
# chunks_with_scores is a list of tuples; each tuple is the chunk and its score
def build_query_result(chunks_with_scores, num_queries, source=""):
    sorted_chunks = sorted(
        chunks_with_scores, key=lambda score: score[1], reverse=True
    )[:num_queries]

    return {
        "success": True,
        "data": [top_text[0] for top_text in sorted_chunks],
        "source": source,
    }




def get_text_queries(source, num_queries=3):
    scored_chunks = []

    for chunk in split_into_chunks(source, filter_poor_quality=True):
        score = calculate_unique_score_for_chunk(chunk)
        scored_chunks.append((remove_special_characters(chunk), score))

    return build_query_result(scored_chunks, num_queries, source=source)
