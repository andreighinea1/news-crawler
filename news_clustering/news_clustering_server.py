import logging

from sanic import Sanic
from sanic_ext import Extend

from api import handlers
# from news_clustering.custom_sanic_cors.cors import add_cors_headers
# from news_clustering.custom_sanic_cors.options import setup_options

app = Sanic('news')

# CORS
app.config.CORS_ORIGINS = "http://localhost:3000,http://localhost:8000"
Extend(app)

# Add routes
app.add_route(handlers.train_and_get_clusters, '/news-clustering/train-get-clusters', methods=['GET', 'POST'])
app.add_route(handlers.get_similar_news, '/news-clustering/get-similar-news', methods=['GET', 'POST'])

# CORS
# app.register_listener(setup_options, "before_server_start")  # Add OPTIONS handlers to any route that is missing it
# app.register_middleware(add_cors_headers, "response")  # Fill in CORS headers

if __name__ == '__main__':
    # debug = not getattr(app.config, 'NO_DEBUG', False)
    debug = True
    if debug:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler("debug_API.log", encoding="utf-8"),
                logging.StreamHandler()
            ]
        )

    app.run(host='0.0.0.0', port=8000, backlog=5, debug=debug, auto_reload=False)
