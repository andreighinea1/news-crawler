from sanic import response

from news_clustering.api.similar_texts import SimilarTexts

MAX_QUERY_LEN = 16
similar_texts = SimilarTexts(results_path='../news_crawler/results.json',
                             threshold=0.6,
                             num_perm=128,
                             parameters={
                                 'title': [(2, 3), 'WORDS'],
                                 'content': [(5, 11), 'WORDS'],
                                 'contained_urls': [(3, 4), 'WORDS']
                             })


async def query(request):
    """
    Main query entry point.
    Params in the request in the following format:
    {'title': str, 'content': str, 'contained_urls': {URL: URL_TITLE}}
    """
    params = request.json or request.args
    if params is None:
        return response.text('Invalid JSON parameters! Check your request!', status=400)
    params = dict(params)  # This is a fix for the queries from the browser (params is a sanic response, not a dict)

    url = params.get('url', '')
    title = params.get('title', '')
    content = params.get('content', '')
    urls = params.get('urls', dict())

    result = {
        'news_clustering': similar_texts.get_similar_news(
            news_url=url,
            news_title=title,
            news_content=content,
            news_contained_urls=urls
        )
    }
    # return response.text('Invalid args!', status=400)

    return response.json(result, status=200)
