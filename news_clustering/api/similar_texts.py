import json
import logging
import re
import time

from datasketch import MinHash, MinHashLSH, LeanMinHash
from typing import Tuple, List, Dict, Any

words_regex = re.compile(r'\W+')


class ShinglesCalc:
    def __init__(self, parameters, *, shingles_unique=True, case_sensitive=False):
        """
        Calculates the MinHash for the news page.

        Args:
            parameters (Dict[str, list]):
                The dict used for selecting what types of shingles enter the MinHash, of format:
                    {news_page_dict__key: [(start_range, end_range), 'WORDS']}
            shingles_unique (bool):
                Should the shingles be unique?
            case_sensitive (bool):
                Should the shingles be case-sensitive?
        Returns:
            SimilarTexts:
                The initialized similarity class
        """

        self.parameters = parameters
        self.shingles_unique = shingles_unique
        self.case_sensitive = case_sensitive

    def create_all_shingles(self, str_dict_to_shingle):
        """
        Calculates all the shingles using the parameters the class was initialized with.

        Args:
            str_dict_to_shingle (Dict[str, str]):
                The news page dict, of format:
                    {'title': STR, 'content': STR, 'contained_urls': URLS_COMBINED_STR}
        Returns:
            List[str]: The list of shingles.
        """
        shingles = []
        for key, text in str_dict_to_shingle.items():
            for param in self.parameters[key]:
                if param == 'WORDS':
                    shingles += self.__create_shingles_words(text)
                elif isinstance(param, tuple):
                    shingles += self.__create_shingles_ngrams(text, shingle_range=param)

        return self.__sort_shingles(shingles)

    def __create_shingles_single(self, text, shingle_length):
        """
        Split the key into individual tokens/shingles/n-grams, with n=shingle_length.

        Args:
            text (str): The text to calculate the shingles for.
            shingle_length (int): The shingle length.
        Returns:
            List[str]: The list of shingles created.
        """
        shingles = [
            text[start: start + shingle_length]
            for start in range(len(text) - shingle_length + 1)
        ]

        if self.shingles_unique:
            return list(dict.fromkeys(shingles))  # To return only the unique shingles, while keeping the order the same
        return shingles

    def __create_shingles_ngrams(self, text, shingle_range):
        """
        Split the key into individual tokens/shingles/n-grams, with n in range shingle_range.

        Args:
            text (str): The text to calculate the shingles for.
            shingle_range (Tuple[int] | List[int]):
                The shingle range to use (both ends inclusive).
        Returns:
            List[str]: The list of shingles created.
        """
        if not self.case_sensitive:
            text = text.lower()

        shingles = []
        for shingle_length in range(shingle_range[0], shingle_range[1] + 1):
            shingles.extend(self.__create_shingles_single(text, shingle_length))
        return shingles

    def __create_shingles_words(self, text):
        """
        Split the key into individual words.

        Args:
            text (str): The text to calculate the shingles for.
        Returns:
            List[str]: The list of words created.
        """
        if not self.case_sensitive:
            text = text.lower()

        shingles = words_regex.split(text)
        shingles = [s for s in shingles if s != '']
        if self.shingles_unique:
            return list(dict.fromkeys(shingles))  # Return only the unique shingles, and keep the order the same
        return shingles

    @staticmethod
    def __sort_shingles(shingles):
        """
        Sort a list of shingles.

        Args:
            shingles(List[str]):
                The list of shingles to sort.

        Returns:
            List[str]:
                The sorted list of shingles, first based on their length, then on content.
        """
        return sorted(shingles, key=lambda x: (len(x), x))


class NewsPage:
    def __init__(self, news_page_dict, news_url, shingles_calc, *, num_perm=128):
        """
        Calculates the MinHash for the news page.

        Args:
            news_page_dict (Dict[str, Any]):
                The news page dict, of format:
                    {'title': str, 'content': str, 'contained_urls': {URL: URL_TITLE}}
            news_url (str):
                The news website URL.
            shingles_calc (ShinglesCalc):
                The initialized ShinglesCalc object.
            num_perm (int):
                The number of permutations for a MinHash.
        Returns:
            NewsPage:
                The initialized news page class
        """

        self.title = news_page_dict['title']
        self.content = news_page_dict['content']
        self.contained_urls = news_page_dict['contained_urls']

        self.news_url = news_url
        self.num_perm = num_perm

        self.shingle_list = shingles_calc.create_all_shingles(str_dict_to_shingle={
            **news_page_dict,
            'contained_urls': ''.join(news_page_dict['contained_urls'].keys())
        })
        self.minhash = self.__calc_minhash(shingle_list=self.shingle_list)

    def __calc_minhash(self, shingle_list):
        """
        Calculate the `MinHash <https://ekzhu.com/datasketch/minhash.html>`_
        for the provided key/shingles.
        Usually, you'd want to convert to a `LeanMinHash
        <https://ekzhu.com/datasketch/documentation.html#datasketch.LeanMinHash>`_.

        Args:
            shingle_list (List[str]):
                The shingles to calculate the MinHash for.

        Returns:
            LeanMinHash:
                The LeanMinHash corresponding to the provided input.
        """
        m = MinHash(num_perm=self.num_perm)
        m.update_batch([s.encode('utf-8') for s in shingle_list])
        return LeanMinHash(m)

    def jaccard(self, other):
        """Estimate the `Jaccard similarity`_ (resemblance) between the sets
        represented by this NewsPage and the other.

        Args:
            other (NewsPage): The other NewsPage.

        Returns:
            float: The Jaccard similarity, which is between 0.0 and 1.0.
        """
        return self.minhash.jaccard(other.minhash)


class SimilarTexts:
    def __init__(self, results_path, *, threshold=0.6, num_perm=128, parameters=None,
                 shingles_unique=True, case_sensitive=False):
        """
        Text similarity of a string with a database of other strings using MinHash and LSH.

        Args:
            results_path (str):
                The path to a JSON "database", of format:
                    {base_url: {'Cnt': Cnt, 'results': {news_url: {'title': str, 'content': str,
                    'contained_urls': {URL: URL_TITLE}}}}}
                That after processing has the format:
                    {news_url: {'title': str, 'content': str,
                    'contained_urls': {URL: URL_TITLE}}}
            threshold (float):
                Between [0, 1]. The minimum similarity to use when clustering (in LSH).
            num_perm (int):
                The number of permutations for a MinHash.
            parameters (Dict[str, list]):
                The dict used for selecting what types of shingles enter the MinHash, of format:
                    {news_page_dict__key: [(start_range, end_range), 'WORDS']}
            shingles_unique (bool):
                Should the shingles be unique?
            case_sensitive (bool):
                Should the shingles be case-sensitive?
        Returns:
            SimilarTexts:
                The initialized similarity class
        """
        if parameters is None:
            parameters = {
                'title': [(2, 3), 'WORDS'],
                'content': [(5, 7), 'WORDS'],
                'contained_urls': [(3, 4), 'WORDS']
            }

        self.shingles_calc = ShinglesCalc(shingles_unique=shingles_unique,
                                          case_sensitive=case_sensitive,
                                          parameters=parameters)
        self.threshold = threshold
        self.num_perm = num_perm

        with open(results_path, 'r') as fin:
            logging.info('Started loading the database and calculating the minhashes')
            start_time = time.time()

            results = json.load(fin)
            self.database: Dict[str, NewsPage] = dict(sum([
                [
                    (news_url, NewsPage(news_page_dict,
                                        news_url=news_url,
                                        shingles_calc=self.shingles_calc,
                                        num_perm=self.num_perm))
                    for news_url, news_page_dict in results_per_site['results'].items()
                ] for results_per_site in results.values()
            ], []))

            logging.info(f'It took {time.time() - start_time: .3f} seconds to load the database.')

        self.__calc_lsh()

    def __calc_lsh(self):
        """
        Uses the already calculated `MinHashes <https://ekzhu.com/datasketch/minhash.html>`_
        to create the `LSH <https://ekzhu.com/datasketch/lsh.html>`_.

        Returns:
            MinHashLSH:
                The created LSH.
        """
        logging.info('Started calculating lsh')
        start_time = time.time()

        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        with self.lsh.insertion_session() as session:
            for news_url, news_page in self.database.items():
                session.insert(news_url, news_page.minhash)
        logging.info(f'It took {time.time() - start_time: .3f} seconds to build the lsh.')

        return self.lsh

    def get_similar_news(self, news_url, news_title=None, news_content=None, news_contained_urls=None):
        """
        Get the news that are similar to the provided news info.

        Args:
            news_url (Optional[str]):
                The news website's URL.
            news_title (Optional[str]):
                The news website's title.
            news_content (Optional[str]):
                The news website's content.
            news_contained_urls (Optional[Dict[str, str]]):
                The news website's contained URLs.
        Returns:
            Dict[str, float]:
                A dict with keys as the similar news URLs, and the values the jaccard distances to those URLs web pages.
        """
        if not news_title:
            news_title = ''
        if not news_content:
            news_content = ''
        if not news_contained_urls:
            news_contained_urls = dict()

        news_page_dict = {
            'title': news_title,
            'content': news_content,
            'contained_urls': news_contained_urls,
        }

        news_page = NewsPage(news_page_dict,
                             news_url=news_url,
                             shingles_calc=self.shingles_calc,
                             num_perm=self.num_perm)
        similar_news = self.lsh.query(news_page.minhash)
        return {
            similar_news_url: self.database[similar_news_url].jaccard(news_page)
            for similar_news_url in similar_news
        }
