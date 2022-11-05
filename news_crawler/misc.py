from operator import itemgetter


# https://stackoverflow.com/questions/50493838/fastest-way-to-sort-a-python-3-7-dictionary
def sort_dict_by_values(d, reverse=False, top=None):
    r = {k: v for k, v in sorted(d.items(), key=itemgetter(1), reverse=reverse)}
    if top:
        return dict(list(r.items())[:top])
    return r


def sort_dict_by_keys(d, reverse=False, top=None):
    r = {k: v for k, v in sorted(d.items(), key=itemgetter(0), reverse=reverse)}
    if top is not None:
        return dict(list(r.items())[:top])
    return r
