from django.views.generic import View
from django.http import HttpResponse
from django.shortcuts import render
from urllib.error import HTTPError, URLError
import urllib
from .models import ScanLog, Query, ScanResult
import os
from socket import timeout
from .hooks import get_queries, run_request, get_text_queries, generate_ngrams, html_to_basic_text
from .cleanup import remove_special_characters

class HomeView(View):
    def get(self, request):
        return render(request, "checker/index.html", context={"name":"abas"})


def process_request(request):
    """
    Processes the HTTP request and scans the URL or file, returning the ID of the homepage trial.

    :param request: The HTTP request
    :return: Tuple of [0] the scan log and [1] a list of results (if applicable)
    """
    scan_results = []
    param_url = request.POST.get('url')
    text = request.POST.get('data')

    if param_url:
        queries = get_queries(param_url)
    else:
        queries = get_text_queries(text)
    

    # TODO Too similar to scan_resources code
    if queries['success']:
        log = ScanLog(protected_resource=queries['source'])
        log.save()
        query_list = []
        for query in queries['data']:
            q = Query(query=query)
            q.save()
            query_list.append(q)

        log.queries.add(*query_list)
        log.save()

    if queries['success'] and len(queries['data']):
        results = run_request(queries['data'], [param_url, ])

        for result in results:
            scan_result = ScanResult(result_log=log, match_url=result['url'],
                                     match_display_url=result['displayUrl'],post_scanned=False)
            scan_result.save()
            scan_results.append(scan_result)
    else:
        if queries['success'] and len(queries['data']) == 0:
            reason = 'No suitable content found'
            fail_type = ScanLog.C
        else:
            log = ScanLog()
            reason = queries['data']
            fail_type = ScanLog.H

        log.fail_reason = reason
        log.fail_type = fail_type
        log.save()
    
    #TODO (if scan_result) then process each asynchronously
    info = []
    for res in scan_results:
    	info.append(post_process_result(res))
    info = "\n".join([str(i) for i in info])
    return HttpResponse(f"{info}")



def post_process_result(result):
    try:
        url_result = urllib.request.urlopen(urllib.request.Request(result.match_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'}),
                                            timeout=5).read()
    except (HTTPError, URLError) as e:
        result.perc_of_duplication = -1
        result.post_fail_reason = str(e)
        result.post_fail_type = ScanLog.H
        result.post_scanned = True
        result.save()
        return result
    except timeout as t:
        result.perc_of_duplication = -1
        result.post_fail_reason = 'URL timed out'
        result.post_fail_type = ScanLog.H
        result.post_scanned = True
        result.save()
        return result
    else:
        try:
            url_text = url_result.decode('utf-8')
        except UnicodeDecodeError:
            url_text = url_result.decode('ISO-8859-1')

        result_text = html_to_basic_text(url_text)
        queries_in_result = [query.query for query in result.result_log.queries.all() if
                             remove_special_characters(query.query) in result_text]

        # If no queries exist in the result, this must be a false positive - i.e. Bing has returned rubbish results
        if len(queries_in_result) == 0:
            result.perc_of_duplication = -1
            result.post_fail_reason = 'False positive'
            result.post_fail_type = ScanLog.C
        else:
            # Else the results seem okay, so work out a % duplication based on trigrams (NumMatchedTGs / NumProtectedTGs * 100)
            source_text = html_to_basic_text(result.result_log.protected_resource)
            source_trigrams = generate_ngrams(source_text.lower())
            result_trigrams = generate_ngrams(result_text.lower())

            num_trigram_intersection = len(
                [source for source in source_trigrams if source.lower() in result_trigrams])
            result.perc_of_duplication = (num_trigram_intersection / len(source_trigrams)) * 100

        result.post_scanned = True
        result.save()
        return result
