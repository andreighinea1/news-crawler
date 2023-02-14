from api import handlers
from sanic import Sanic
import logging

app = Sanic('news')
app.add_route(handlers.query, '/similar_news/query', methods=['GET', 'POST'])

if __name__ == '__main__':
    # debug = not getattr(app.config, 'NO_DEBUG', False)
    debug = True
    if debug:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.FileHandler("debug.log", encoding="utf-8"),
                logging.StreamHandler()
            ]
        )

    app.run(host='0.0.0.0', port=8000, backlog=5, debug=debug, auto_reload=False)
