import itertools
import urllib
from collections import namedtuple

import requests
from bs4 import BeautifulSoup

from textcleanup import (calculate_unique_score_for_chunk, generate_ngrams,
                         html_to_basic_text, remove_special_characters,
                         split_into_chunks)


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


def get_text_from_elem(elem):
    try:
        text = elem.get_text(" ", strip=True)
    except AttributeError:
        text = elem
    return text





def run_request(queries, exclude_urls):
    result = []
    headers = {"Ocp-Apim-Subscription-Key": "f0a1cf2c35e746c49679f5971ef9db70"}
    params = {"textDecoration": True, "textFormat": "HTML"}
    url = "https://api.bing.microsoft.com/v7.0/search"

    for query in queries:
        params['q'] = query
        api_result = requests.get(
            url,
            params=params,
            headers=headers
        )
        if api_result.status_code == 200:
            json = api_result.json()["webPages"]["value"]
            add_result(json, result, exclude_urls)

            """# Get another page of results from the API, so each query can yield up to 100 results
            if len(json["results"]) > 49 and json["__next"] is not None:
                api_result = requests.get(
                    json["__next"] + "&$format=json", auth=(key, key)
                )
                if api_result.status_code == 200:
                    json = api_result.json()["d"]
                    for i in json["results"]:
                        add_result(i, result, exclude_urls)"""

    return result



def add_result(row, result_list, excluded_urls):
    # Second 'and' is explained here:
    # http://stackoverflow.com/questions/3897499/check-if-value-already-exists-within-list-of-dictionaries
    for api_row in row:
        if api_row["url"] not in excluded_urls and not any(
            dict.get("url", None) == api_row["url"] for dict in result_list
        ):
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


"""DOCTEST!!! THIS IS WHERE THE MAIN THING IS BEGINNING"""

scan_info = namedtuple("Scaninfo", 'match_url source query')


def scan_url(request):
    URL = request # request.POST.get('url')  # TODO IN PRODUCTION
    scan_res = []
    queries = get_text_queries(request)
    
    if queries['success'] and len(queries['data']) > 0:
        results = run_request(queries["data"], [])
        for result in results:
            scan_res.append(scan_info(result['url'], queries['source'], queries["data"][0]))
    return scan_res


def process_url_scan(result: scan_info):
    url_result = urllib.request.urlopen(
        urllib.request.Request(
            result.match_url,
            headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'}),
        timeout=5).read()
    url_text = url_result.decode('utf-8')
    result_text = html_to_basic_text(url_text)
    queries_in_res = [result.query] if remove_special_characters(result.query) in result_text else []

    if not queries_in_res:
        perc_of_duplication = -1
       
    else:
        # Else the results seem okay, so work out a % duplication based on trigrams (NumMatchedTGs / NumProtectedTGs * 100)
        source_text = html_to_basic_text(result.source)
        source_trigrams = generate_ngrams(source_text.lower())
        result_trigrams = generate_ngrams(result_text.lower())

        num_trigram_intersection = len([source for source in source_trigrams if source.lower() in result_trigrams])
        perc_of_duplication = (num_trigram_intersection / len(source_trigrams)) * 100
    
    return perc_of_duplication


def get_text_queries(source, num_queries=3):
    scored_chunks = []

    for chunk in split_into_chunks(source, filter_poor_quality=True):
        score = calculate_unique_score_for_chunk(chunk)
        scored_chunks.append((remove_special_characters(chunk), score))

    return build_query_result(scored_chunks, num_queries, source=source)

source = """What is a blog anyway?
In short, a blog is a type of website that focuses mainly on written content, also known as blog posts. In popular culture we most often hear about news blogs or celebrity blog sites, but as you’ll see in this guide, you can start a successful blog on just about any topic imaginable.
Bloggers often write from a personal perspective that allows them to connect directly with their readers. In addition, most blogs also have a “comments” section where visitors can correspond with the blogger. Interacting with your visitors in the comments section helps to further the connection between the blogger and the reader.
This direct connection to the reader is one of the main benefits of starting a blog. This connection allows you to interact and share ideas with other like-minded people. It also allows you to build trust with your readers. Having the trust and loyalty of your readers also opens up the door to making money from your blog, which is something I discuss later in this guide.
The good news is that the internet is exploding with growth right now. More people than ever are online. This explosion in growth means more potential readers for your blog. In short, if you are thinking about starting a blog then there is no better time than right now.
Let’s start your blog!

"""
q = scan_url(source)

print(process_url_scan(q[0]))
#print(q)