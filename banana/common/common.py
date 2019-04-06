import logging

import math
import unidecode

logger = logging.getLogger(__name__)


def canonical_movie_title(title, year=None):
    # remove some common prefixes
    title = title.replace("IMAX", "")
    title = title.replace("IMAX: ", "")
    if year is None:
        return unidecode.unidecode(title)
    return unidecode.unidecode(u"{} ({})".format(title, year))


def total_pages(total_items, items_per_page):
    return math.ceil(total_items / items_per_page)
