import gc
import json
import logging
import re
import time
from collections import defaultdict, Counter
from typing import Tuple, List, Dict

import joblib
import numpy as np
from datasketch import MinHash, MinHashLSH, LeanMinHash
from sklearn.cluster import DBSCAN
from tqdm.auto import tqdm

from news_clustering.api import misc

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
    def __init__(self, news_url, news_page_dict, shingles_calc, *, num_perm=128):
        """
        Calculates the MinHash for the news page.

        Args:
            news_url (str):
                The news website URL.
            news_page_dict (Dict[str, Any]):
                The news page dict, of format:
                    {'title': str, 'content': str, 'contained_urls': {URL: URL_TITLE}}
            shingles_calc (ShinglesCalc):
                The initialized ShinglesCalc object.
            num_perm (int):
                The number of permutations for a MinHash.
        Returns:
            NewsPage:
                The initialized news page class
        """

        self.news_title = news_page_dict['title']
        self.news_content = news_page_dict['content']
        self.news_contained_urls = news_page_dict['contained_urls']

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

    def get_minhash(self):
        return self.minhash


class SimilarTexts:
    def __init__(self, news_json_obj=None, *, results_path=None,
                 threshold=0.6, num_perm=128, min_samples=3, eps=0.6,
                 predominant_cluster_min_percentage=0.6,
                 parameters=None,
                 folder_out_path='OUT', overwrite=True, save_noise_points=False,
                 shingles_unique=True, case_sensitive=False):
        """
        Text similarity of a string with a database of other strings using MinHash and LSH.

        Args:
            news_json_obj (Dict[str, Dict[str, Any]]):
                The loaded news JSON object, of format:
                    {news_url: {'title': str, 'content': str,
                    'contained_urls': {URL: URL_TITLE}}}

                If None, results_path must not be None.
            results_path (str):
                The path to a JSON "database", of format:
                    {base_url: {'Cnt': Cnt, 'results': {news_url: {'title': str, 'content': str,
                    'contained_urls': {URL: URL_TITLE}}}}}
                That after processing has the format:
                    {news_url: {'title': str, 'content': str,
                    'contained_urls': {URL: URL_TITLE}}}

                If None, database must not be None.
            threshold (float):
                Between [0, 1]. The minimum similarity to use when finding LSH similarities.
            num_perm (int):
                The number of permutations for a MinHash.
            min_samples (int):
                The minimum number of samples to use when clustering with DBSCAN.
            eps (float):
                Between [0, 1]. The max distance to use when clustering with DBSCAN.
            predominant_cluster_min_percentage (float):
                Between [0, 1]. Min percentage to declare that a key is from a similar cluster.
            parameters (Dict[str, list]):
                The dict used for selecting what types of shingles enter the MinHash, of format:
                    {news_page_dict__key: [(start_range, end_range), 'WORDS']}
            folder_out_path (str):
                The folder path where to write the model's output files.
            overwrite (bool):
                Overwrite the model's output files?
            save_noise_points (bool):
                Save the clustering noise points?
            shingles_unique (bool):
                Should the shingles be unique?
            case_sensitive (bool):
                Should the shingles be case-sensitive?
        Returns:
            SimilarTexts:
                The initialized similarity class
        """
        if not news_json_obj and not results_path:
            raise Exception("One of `news_json_obj` or `results_path` must not be None and have something in them")

        # region DEFAULT INITS
        if parameters is None:
            parameters = {
                'title': [(2, 3), 'WORDS'],
                'content': [(5, 7), 'WORDS'],
                'contained_urls': [(3, 4), 'WORDS']
            }

        # Initialize the object for clusterization (same as self.__init_clusterization())
        self.fitted_clustering = False
        self.clusters = None
        self.noise_points = None
        self.origin_points = None
        self.key_to_cluster_index = None

        # Initialize the object for LSH similarity queries (same as self.__init_similarity())
        self.fitted_similarity = False
        self.lsh = None
        # endregion DEFAULT INITS

        # region INIT FROM PARAMS
        self.shingles_calc = ShinglesCalc(shingles_unique=shingles_unique,
                                          case_sensitive=case_sensitive,
                                          parameters=parameters)
        self.threshold = threshold
        self.num_perm = num_perm
        self.min_samples = min_samples
        self.eps = eps
        self.predominant_cluster_min_percentage = predominant_cluster_min_percentage
        self.folder_out_path = folder_out_path
        self.overwrite = overwrite
        self.save_noise_points = save_noise_points
        # endregion INIT FROM PARAMS

        # region FNAMES
        self.DATABASE_FNAME = "database"
        self.LSH_FNAME = "lsh"
        self.MAPPING_FNAME = "key_to_cluster_index"
        self.CLUSTERS_FNAME = "clusters"
        self.XIN_TO_TEXTLIST_FNAME = "X_in__to__text_list"
        # endregion FNAMES

        # region INIT THE DB
        # TODO: Maybe if needed use multiprocessing here

        logging.info('Started loading the database and calculating the minhashes')
        start_time = time.time()

        if news_json_obj:
            self.database: Dict[str, NewsPage] = {
                news_url: NewsPage(news_url=news_url,
                                   news_page_dict=news_page_dict,
                                   shingles_calc=self.shingles_calc,
                                   num_perm=self.num_perm)
                for news_url, news_page_dict in news_json_obj.items()
            }
        elif results_path:
            with open(results_path, 'r') as fin:
                results = json.load(fin)
                self.database: Dict[str, NewsPage] = dict(sum([
                    [
                        (news_url, NewsPage(news_url=news_url,
                                            news_page_dict=news_page_dict,
                                            shingles_calc=self.shingles_calc,
                                            num_perm=self.num_perm))
                        for news_url, news_page_dict in results_per_site['results'].items()
                    ] for results_per_site in results.values()
                ], []))

        logging.info(f'It took {time.time() - start_time: .3f} seconds to load the database.')
        # endregion INIT THE DB

    # region HELPERS
    def __get_news_page_from_info(self, news_url, news_title=None, news_content=None, news_contained_urls=None):
        """
        Gets a NewsPage object from news info.

        Args:
            news_url (str):
                The news website's URL.
            news_title (str):
                The news website's news_title.
            news_content (str):
                The news website's content.
            news_contained_urls (Dict[str, str]):
                The news website's contained URLs.
        Returns:
            NewsPage:
                The created NewsPage object.
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

        return NewsPage(news_url=news_url,
                        news_page_dict=news_page_dict,
                        shingles_calc=self.shingles_calc,
                        num_perm=self.num_perm)

    def add_to_database(self, news_url, news_title=None, news_content=None, news_contained_urls=None,
                        *, reinit_clusterization=True, reinit_similarity=True):
        """
        Add 1 new news to the database.

        Args:
            news_url (str):
                The news website's URL.
            news_title (str):
                The news website's news_title.
            news_content (str):
                The news website's content.
            news_contained_urls (Dict[str, str]):
                The news website's contained URLs.
            reinit_clusterization (bool):
                Should reinitialize the clusterization fitting after adding to the db?
            reinit_similarity (bool):
                Should reinitialize the similarity fitting after adding to the db?
        """

        self.database[news_url] = self.__get_news_page_from_info(news_url=news_url,
                                                                 news_title=news_title,
                                                                 news_content=news_content,
                                                                 news_contained_urls=news_contained_urls)

        if reinit_clusterization:
            self.__init_clusterization()
        if reinit_similarity:
            self.__init_similarity()
        return

    def save_to_pickles(self, *, data, fname=None, full_file_path=None):
        """
        Save the data to a pickle file named fname.

        Args:
            data: The data to save.
            fname (str): The file name. Saved at join(self.folder_out_path, fname).
            full_file_path (str): The full file_path to save to. Ignores self.folder_out_path and fname.
        """
        misc.save_to_pickles(
            data=data,
            folder_path=self.folder_out_path,
            fname=fname,
            full_file_path=full_file_path,
            overwrite=self.overwrite,
        )

    def load_from_pickles(self, *, fname=None, full_file_path=None):
        """
        Load data from a pickle file and return it.

        Args:
            fname (str): The file name. Loaded from join(self.folder_out_path, fname).
            full_file_path (str): The full file_path to load from. Ignores self.folder_out_path and fname.

        Returns:
            The data loaded from the pickle file.
        """
        return misc.load_from_pickles(
            folder_path=self.folder_out_path,
            fname=fname,
            full_file_path=full_file_path,
        )

    @staticmethod
    def sort_clusters(clusters):
        """
        Sort a list of clusters.

        Args:
            clusters (List[List[str]]):
                The list of clusters to sort.

        Returns:
            List[List[str]]:
                The sorted list of clusters, first based on their length, then on content.
        """
        clusters = [sorted(cluster) for cluster in clusters]
        return sorted(clusters, key=lambda x: (len(x), str(x)), reverse=True)

    # endregion HELPERS

    # region INIT
    def __init_clusterization(self):
        """
        Initialize the object for clusterization.
        """
        self.fitted_clustering = False
        self.clusters = None
        self.noise_points = None
        self.origin_points = None
        self.key_to_cluster_index = None
        return

    def __init_similarity(self):
        """
        Initialize the object for LSH similarity queries.
        """
        self.fitted_similarity = False
        self.lsh = None
        return

    # endregion INIT

    # region FITTING
    def fit_similarity(self):
        """
        Uses the already calculated `MinHashes <https://ekzhu.com/datasketch/minhash.html>`_
        to create the `LSH <https://ekzhu.com/datasketch/lsh.html>`_.

        Returns:
            SimilarTexts:
                The fitted SimilarTexts self.
        """
        logging.info('Started calculating lsh')
        start_time = time.time()

        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        with self.lsh.insertion_session() as session:
            for news_url, news_page in self.database.items():
                session.insert(news_url, news_page.minhash)
        logging.info(f'It took {time.time() - start_time: .3f} seconds to build the lsh.')

        self.fitted_similarity = True
        return self

    def __get_key_to_cluster_index(self, clusters):
        """
        Get the key_to_cluster_index used to find which cluster each key belongs to.

        Args:
            clusters (List[List[str]]): The clusters of keys.

        Returns:
            Dict[str, int]: The key_to_cluster_index.
        """
        # TODO: Make some changes to indexing to adapt to this new index
        # current_date = datetime.today().strftime('%Y-%m-%d') + "_"

        key_to_cluster_index = dict()
        for i, cluster in enumerate(clusters):
            for key in cluster:
                key_to_cluster_index[key] = i
                # key_to_cluster_index[key] = current_date + str(i)

        self.save_to_pickles(data=key_to_cluster_index, fname=self.MAPPING_FNAME)
        return key_to_cluster_index

    def fit_clustering(self, *, keep_database_in_memory=True, keep_lsh_in_memory=True):
        """
        Uses the already calculated `MinHashes <https://ekzhu.com/datasketch/minhash.html>`_
        of NewsPages to clusterize them together.

        Args:
            keep_database_in_memory (bool):
                Should keep the database in RAM at the end of the fitting?
            keep_lsh_in_memory (bool):
                Should keep the LSH in RAM at the end of the fitting?
        Returns:
            SimilarTexts:
                The fitted SimilarTexts self.
        """

        if self.fitted_similarity:
            self.save_to_pickles(data=self.lsh, fname=self.LSH_FNAME)
            del self.lsh
            gc.collect()

        # region minhashes mapping to text_list
        X_in__to__text_list: Dict[Tuple[np.uint32], List[str]] = defaultdict(list)
        for news_url, news_page in self.database.items():
            X_in__to__text_list[tuple(news_page.get_minhash().hashvalues)].append(news_url)
        self.save_to_pickles(data=X_in__to__text_list, fname=self.XIN_TO_TEXTLIST_FNAME)
        del X_in__to__text_list
        gc.collect()
        # endregion minhashes mapping to text_list

        # region X_in & Weights
        minhashes_to_weights = dict(Counter([
            tuple(news_page.get_minhash().hashvalues) for news_page in self.database.values()
        ]).most_common())

        self.save_to_pickles(data=self.database, fname=self.DATABASE_FNAME)
        del self.database  # No longer needed for now
        gc.collect()

        X_in = np.vstack(list(minhashes_to_weights.keys()))
        weights = np.array(list(minhashes_to_weights.values()))
        del minhashes_to_weights
        gc.collect()
        # endregion X_in & Weights

        # region DBSCAN FITTING
        logging.info('Started fitting DBSCAN')
        start_time = time.time()

        with joblib.parallel_backend(backend='loky', n_jobs=- 1):
            # TODO-OPTIMIZATION: "Precomputed sparse input was not sorted by data"
            # noinspection PyTypeChecker
            model: DBSCAN = DBSCAN(min_samples=self.min_samples, eps=self.eps,
                                   metric='hamming', algorithm='ball_tree',
                                   # algorithm is 'ball_tree' or 'brute' or 'auto'
                                   n_jobs=-1).fit(X_in, sample_weight=weights)

        logging.info(f'It took {time.time() - start_time: .3f} seconds to fit DBSCAN.')
        # endregion DBSCAN FITTING

        # region CLUSTERS
        labels: np.ndarray = model.labels_
        del model, weights
        gc.collect()

        # region Get the clusters and noise points
        logging.info('Started getting the clusters')
        start_time = time.time()

        # Get the real clusters
        X_in__to__text_list = self.load_from_pickles(fname=self.XIN_TO_TEXTLIST_FNAME)

        def get_real_cluster(class_member_mask):  # TODO: Optimize this
            real_cluster = sum((
                X_in__to__text_list[tuple(xin)]
                for xin in X_in[class_member_mask]
            ), [])
            return real_cluster

        # Separate the clusters and noise points
        # CLUSTERS
        clusters = [
            get_real_cluster(class_member_mask=(labels == k))
            for k in set(labels)
            if k != -1  # If it's not a noise point, or if yes, if we want to return them
        ]
        # NOISE POINTS
        noise_points = get_real_cluster(class_member_mask=(labels == -1))
        del X_in, X_in__to__text_list
        gc.collect()

        # Sort the clusters and maybe save them
        clusters = self.sort_clusters(clusters)
        self.save_to_pickles(data=clusters, fname=self.CLUSTERS_FNAME)

        logging.info(f'It took {(time.time() - start_time): .3f} seconds to get and save the clusters.')

        # Print some statistics
        n_noise_ = list(labels).count(-1)
        n_OK_ = len(labels) - n_noise_
        logging.info(f"Number of clusters: {len(clusters)}")
        logging.info(f"Number of noise points: {n_noise_}")
        logging.info(f"Number of non-noise points: {n_OK_}")
        # endregion Get the clusters and noise points

        # region REMOVE NOISE POINTS from database and lsh
        logging.info("Removing noise points from database and LSH...")
        start_time = time.time()

        self.database = self.load_from_pickles(fname=self.DATABASE_FNAME)  # Load it back at the end
        for key in tqdm(noise_points, desc='Removing noise points from database'):
            del self.database[key]
        self.save_to_pickles(data=self.database, fname=self.DATABASE_FNAME)
        if keep_database_in_memory:
            del self.database
            gc.collect()

        if self.fitted_similarity:
            self.lsh: MinHashLSH = self.load_from_pickles(fname=self.LSH_FNAME)
            for key in tqdm(noise_points, desc='Removing noise points from lsh'):
                self.lsh.remove(key)
            self.save_to_pickles(data=self.lsh, fname=self.LSH_FNAME)
            if keep_lsh_in_memory:
                del self.lsh
                gc.collect()

        logging.info(f'It took {(time.time() - start_time): .3f} seconds to remove the noise points.')
        # endregion REMOVE NOISE POINTS from database and lsh
        # endregion CLUSTERS

        if not self.save_noise_points:
            noise_points = None
        self.clusters = clusters
        self.noise_points = noise_points

        self.key_to_cluster_index = self.__get_key_to_cluster_index(self.clusters)

        self.fitted_clustering = True

        gc.collect()

        return self

    # endregion FITTING

    # region PREDICT
    def get_similar_news(self, news_page=None,
                         news_url=None, news_title=None, news_content=None, news_contained_urls=None):
        """
        Calculate and return the news that are similar to the provided news info.

        Args:
            news_page (NewsPage):
                The news website's URL.
            news_url (str):
                The news website's URL.
            news_title (str):
                The news website's news_title.
            news_content (str):
                The news website's content.
            news_contained_urls (Dict[str, str]):
                The news website's contained URLs.
        Returns:
            Dict[str, float]:
                A dict with keys as the similar news URLs, and the values the jaccard distances to those URLs web pages.
        """

        if not self.fitted_similarity:
            logging.error("LSH Similarity wasn't fitted. "
                          "Please call fit_similarity() before trying to get the similar news!")
            return dict()

        if not news_page:
            news_page = self.__get_news_page_from_info(news_url=news_url,
                                                       news_title=news_title,
                                                       news_content=news_content,
                                                       news_contained_urls=news_contained_urls)

        similar_news = self.lsh.query(news_page.minhash)
        res = {
            similar_news_url: self.database[similar_news_url].jaccard(news_page)
            for similar_news_url in similar_news
        }
        return res

    def get_similar_clusters(self, news_page=None,
                             news_url=None, news_title=None, news_content=None, news_contained_urls=None):
        """
        Calculate and return the list of similarities between the inputted NewsPage and the fitted clusters.

        Args:
            news_page (NewsPage):
                The news website's URL.
            news_url (str):
                The news website's URL.
            news_title (str):
                The news website's news_title.
            news_content (str):
                The news website's content.
            news_contained_urls (Dict[str, str]):
                The news website's contained URLs.
        Returns:
            Dict[str, float]:
                A dict with keys as the similar news URLs, and the values the jaccard distances to those URLs web pages.
        """

        if not self.fitted_similarity or not self.fitted_clustering:
            logging.error("Error, both similarity and clustering must be fitted. "
                          "Please call fit_similarity() and fit_clustering() "
                          "before trying to get the similar clusters!")
            return dict()

        if not news_page:
            news_page = self.__get_news_page_from_info(news_url=news_url,
                                                       news_title=news_title,
                                                       news_content=news_content,
                                                       news_contained_urls=news_contained_urls)
        key = news_page.news_url

        # region FIND THE SIMILAR CLUSTERS
        # Get the similar urls by querying the lsh
        similar_news: Dict[str, float] = self.get_similar_news(news_page=news_page)
        if len(similar_news) == 0:
            logging.info(f"text_clustering-predict_single() - No cluster found that's similar to the key "
                         f"'{key}' - No similar URLs")
            return -1

        # Find the counts for each of the clusters from each similar url
        clusters_indices_counts: List[Tuple[int, int]] = Counter([
            self.key_to_cluster_index[key]
            for key in similar_news.keys()
        ]).most_common()
        # TODO: CONTINUE

        # endregion FIND THE SIMILAR CLUSTERS

        # region FIND THE CLUSTER INDEX
        # Get the cluster associated to the given url
        cluster_index = self.key_to_cluster_index.get(key, None)
        if cluster_index is None:  # Not found in existing clusters, rebuild
            # Choose the most predominant one
            predominant_cluster_index, predominant_cluster_count = clusters_indices_counts[0]
            # Check that the percentage the cluster is found is higher than the minimum from the config
            if predominant_cluster_count / len(similar_news) > self.predominant_cluster_min_percentage:
                logging.info(f"text_clustering-predict_single() - Found a cluster that has keys similar to "
                             f"the key: {key}")
                # If it is, then get the most predominant cluster
                cluster_index = predominant_cluster_index
            else:
                logging.info(f"text_clustering-predict_single() - No cluster found that's similar to the key "
                             f"'{key}' - Not predominant")
                return -1
        else:
            logging.info(f"text_clustering-predict_single() - Found the cluster directly for the key '{key}'")
        # endregion FIND THE CLUSTER INDEX

        # Return the cluster index, usually for usage either with the clusters themselves, or with ClustersResults
        return cluster_index

    # def get_origin_points(self):
    #     """
    #     Calculate and return the origin points for the clustering.
    #
    #     Returns:
    #         Dict[str, float]:
    #             A dict with keys as the similar news URLs, and the values the .
    #     """
    #
    #     if not self.fitted_similarity or not self.fitted_clustering:
    #         logging.error("Error, both similarity and clustering must be fitted. "
    #                       "Please call fit_similarity() and fit_clustering() "
    #                       "before trying to get the origin points!")
    #         return dict()
    #
    #     # news_page = self.__get_news_page_from_info(news_url=news_url,
    #     #                                            news_title=news_title,
    #     #                                            news_content=news_content,
    #     #                                            news_contained_urls=news_contained_urls)
    #     #
    #     # similar_news = self.lsh.query(news_page.minhash)
    #     # return {
    #     #     similar_news_url: self.database[similar_news_url].jaccard(news_page)
    #     #     for similar_news_url in similar_news
    #     # }
    # endregion PREDICT
