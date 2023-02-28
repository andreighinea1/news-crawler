import logging
import os
import pickle


def save_to_pickles(*, data, folder_path: str = None, fname: str = None, full_file_path: str = None, overwrite=False):
    if full_file_path is None:
        full_file_path = f'{folder_path}/{fname}'
    if not full_file_path.endswith('.pkl'):
        full_file_path += '.pkl'

    if overwrite or not os.path.exists(full_file_path):
        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

        with open(full_file_path, 'wb') as fout:
            pickle.dump(data, fout)
        logging.info(f"{fname} saved to {full_file_path}\n")
    else:
        logging.info(f"{full_file_path} already saved, delete it to save again, or enable overwriting!!\n")


def load_from_pickles(*, folder_path: str = None, fname: str = None, full_file_path: str = None):
    if full_file_path is None:
        full_file_path = f'{folder_path}/{fname}'
    if not full_file_path.endswith('.pkl'):
        full_file_path += '.pkl'

    with open(full_file_path, 'rb') as fin:
        data = pickle.load(fin)
    return data
