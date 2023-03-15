import logging
from typing import Optional

from sanic import response

from news_clustering.api.similar_texts import SimilarTexts

MAX_QUERY_LEN = 16
similar_texts: Optional[SimilarTexts] = None


async def train_and_get_clusters(request):
    """
    Train the SimilarTexts model.
    Params in the request should be one of:
    'results_path': results_path
    'news_json_obj': news_json_obj

    news_json_obj is in the following format:
    {news_url: {'title': str, 'content': str, 'contained_urls': {URL: URL_TITLE}}}
    """
    params = request.json or request.args
    if not params:
        return response.text('Invalid JSON parameters! Check your request!', status=400)
    params = dict(params)  # This is a fix for the queries from the browser (params is a sanic response, not a dict)

    # Get params
    news_json_obj = params.get('news_json_obj', dict())
    if not news_json_obj:
        results_path = params.get('results_path', '')
        if not results_path:
            return response.text('Insufficient JSON parameters! Check your request!', status=400)
        news_json_obj = SimilarTexts.get__news_json_obj__from__results_path(results_path=results_path)
    should_fit_similarity = params.get('should_fit_similarity', True)

    # Do the fitting
    try:
        global similar_texts
        similar_texts = SimilarTexts(
            news_json_obj=news_json_obj,
            threshold=0.4,
            num_perm=128,
            parameters={
                'title': [(2, 3), 'WORDS'],
                'content': [(5, 11), 'WORDS'],
                'contained_urls': [(3, 4)]
            })

        if should_fit_similarity:  # Better do it before fit_clustering(), because of the removal of noise points
            similar_texts.fit_similarity()

        similar_texts.fit_clustering(remove_noise_points=False,
                                     keep_database_in_memory=True,
                                     keep_lsh_in_memory=True)

        result = {
            'clusters': similar_texts.clusters
        }
    except Exception as e:
        logging.exception(e)
        return response.text(f'Something went wrong: {e}', status=400)

    return response.json(result, status=200)


async def get_similar_news(request):
    """
    Get similar news. Model needs to first be trained.
    Params in the request in the following format:
    {'title': str, 'content': str, 'contained_urls': {URL: URL_TITLE}}
    """
    global similar_texts
    if not similar_texts or not similar_texts.fitted_similarity:
        return response.text('You must first train the LSH Similarity!', status=400)

    params = request.json or request.args
    if params is None:
        return response.text('Invalid JSON parameters! Check your request!', status=400)
    params = dict(params)  # This is a fix for the queries from the browser (params is a sanic response, not a dict)

    url = params.get('url', '')
    title = params.get('title', '')
    content = params.get('content', '')
    urls = params.get('urls', dict())

    result = {
        'similar_news': similar_texts.get_similar_news(
            news_url=url,
            news_title=title,
            news_content=content,
            news_contained_urls=urls
        )
    }
    # return response.text('Invalid args!', status=400)

    return response.json(result, status=200)
