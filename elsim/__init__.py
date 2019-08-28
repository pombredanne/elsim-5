# This file is part of Elsim
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Elsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Elsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Elsim.  If not, see <http://www.gnu.org/licenses/>.

import logging
from elsim.similarity import Similarity, Compress

ELSIM_VERSION = 0.2

log_elsim = logging.getLogger("elsim")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
log_elsim.addHandler(console_handler)


def set_debug():
    log_elsim.setLevel(logging.DEBUG)


def get_debug():
    return log_elsim.getEffectiveLevel() == logging.DEBUG


def warning(x):
    log_elsim.warning(x)


def error(x):
    log_elsim.error(x)
    raise Exception("waht")


def debug(x):
    log_elsim.debug(x)


# The following constants are used in the Filter dict
# They require certain objects or functions...
# The process is explained here

# Object to store element information in
# This will be applied to every element in the iterable.
# from an element, we construct an Element...
# Arguments to this function: the element itself, the iterable (Proxy Object)
FILTER_ELEMENT_METH = "FILTER_ELEMENT_METH"
# Object to checksum an element
# Next this Object is created, which might be used
# to normalized the content of the Element
# In general it is used to transform the content.
# All Checksums and Similarities are calculated on this.
# We call this now Checksum but it is actually contained in the Element itself
FILTER_CHECKSUM_METH = "FILTER_CHECKSUM_METH"
# function to calculate the similarity between two elements
# Arguments: Similarity(), Element_1, Element_2
FILTER_SIM_METH = "FILTER_SIM_METH"
# function to sort all similar elements using threshold
FILTER_SORT_METH = "FILTER_SORT_METH"
# object to skip elements
# this object has to implement a `skip` function
# and should return True if the given element shall be skipped.
FILTER_SKIPPED_METH = "FILTER_SKIPPED_METH"

BASE = "base"
ELEMENTS = "elements"
HASHSUM = "hashsum"
SIMILAR_ELEMENTS = "similar_elements"
HASHSUM_SIMILAR_ELEMENTS = "hash_similar_elements"
NEW_ELEMENTS = "newelements"
HASHSUM_NEW_ELEMENTS = "hash_new_elements"
DELETED_ELEMENTS = "deletedelements"
IDENTICAL_ELEMENTS = "identicalelements"
SKIPPED_ELEMENTS = "skippedelements"
SIMILARITY_ELEMENTS = "similarity_elements"
SIMILARITY_SORT_ELEMENTS = "similarity_sort_elements"


class ElsimNeighbors:
    def __init__(self, x, ys):
        import numpy as np
        from sklearn.neighbors import NearestNeighbors

        CI = np.array([x.checksum.get_signature_entropy(),
                       x.checksum.get_entropy()])

        for i in ys:
            CI = np.vstack(
                (CI, [i.checksum.get_signature_entropy(), i.checksum.get_entropy()]))

        self.neigh = NearestNeighbors(2, 0.4)
        self.neigh.fit(np.array(CI))

        self.CI = CI
        self.ys = ys

    def cmp_elements(self):
        z = self.neigh.kneighbors(self.CI[0], 5)
        l = []

        cmp_values = z[0][0]
        cmp_elements = z[1][0]
        idx = 1
        for i in cmp_elements[1:]:
            l.append(self.ys[i - 1])
            idx += 1

        return l


def split_elements(element, iterable):
    """Returns a list of associated elements from the given element"""
    return {i: element.get_associated_element(i) for i in iterable}


class Proxy:
    """
    Proxy can be used as hashable iterable for the use with :class:`Elsim`.
    """
    def __init__(self, iterable):
        self.iterable = iterable

    def __iter__(self):
        yield from self.iterable

    def __len__(self):
        return len(self.iterable)


class Elsim:
    """
    This is the main class to use when calculating similarities between objects.

    In order to have a universal method for every object you like to compare,
    you have to implement some iterator, which is hashable, for your objects.
    The Proxy class is such a wrapper, which supports hashing and is an iterator
    for generic iterators.

    The next important part is the Filter.
    A Filter is basically a dictionary with some pre-defined keys, which has as value
    some function pointers.
    Each function is called for specific tasks and types of the input.

    The filter is required to have the following keys:

    * FILTER_ELEMENT_METH
    * FILTER_SKIPPED_METH
    * FILTER_CHECKSUM_METH
    * FILTER_SIM_METH
    * FILTER_SORT_METH

    A reasonable threshold might be a different per method.
    The following thresholds were used in the past:

    * Text diffing: 0.6
    * x86: 0.6
    * DEX: 0.4
    * DEX Strings: 0.8
    * DEX BasicBlocks: 0.8

    The whole process of comparing the two iterables can be described as such:

    - input: A:set(), B:set()
      where A and B are sets of elements

    - output: I:set(), S:set(), N:set(), D:set(), Sk:set()
      where I: identical elements, S: similar elements, N: new elements,
      D: deleted elements, Sk: skipped elements

    - Sk: Skipped elements by using a "filtering" function (helpful if we
      wish to skip some elements from a set (small size, known element from
      a library, etc.)

    - Identify internal identical elements in each set

    - I: Identify "identical" elements by the intersection of A and B

    - Get all others elements by removing identical elements

    - Perform the "NCD" between each element of A and B

    - S: "Sort" all similarities elements by using a threshold
      This returns the most similar element per element or
      no element if the threshold is not reached (i.e. we think the items are
      not similar at all).

    - N,D: Get all new/deleted elements if they are not present in one of
      the previous sets

    The following diagram describes this algorithm:


    .. code-block:: none

        |--A--|                 |--B--|
        |  A1 |                 |  B1 |
        |  A2 |                 |  B2 |
        |  A3 |                 |  B3 |
        |--An-|                 |--Bn-|
           |      |---------|      |
           |- --->|FILTERING|<-----|
                  |---------|
                     |   |
                     |   |--------->|Sk|
                     |
                     |      |---------|
                     |----->|IDENTICAL|------>|I|
                            |---------|
                                 |
                                 |
                                 |     |---|---use-->|Kolmogorov|
                                 |---->|NCD|
                                       |---|
                                         |
                                         |
                                         |
                                         |         |---------|-->|Threshold|
                                         |-------->| SORTING |
                                                   |---------|
                                                        |
                                                        |
                                                       /|\
                                                      / | \
                                                     /  |  \
                                                    /   |   \
                                                   /    |    \
                                                  /     |     \
                                 |N|<------------/      |      \-------->|D|
                                                        |
                                                        |---->|S|


    Moreover we can calculate a similarity "score" using the number of
    identical elements and the value of the similar elements.
    """
    def __init__(self, e1, e2, F, threshold=0.8, compressor=None, similarity_threshold=0.2):
        """
        
        :param Proxy e1: the first element to compare
        :param Proxy e2: the second element to compare
        :param dict F: Some Filter dictionary
        :param float threshold: value which used in the sort method to eliminate not interesting comparisons
        :param str compressor: compression method name, or None to use the default one
        :param float similarity_threshold: value to threshold similarity values with
        """
        if F is None:
            raise ValueError("A valid filter dict is required!")

        if not (0 <= threshold <= 1):
            raise ValueError("threshold must be a number between 0 and 1!")
        self.threshold = threshold

        if not (0 <= similarity_threshold <= 1):
            raise ValueError("similarity_threshold must be a number between 0 and 1!")
        self.similarity_threshold = similarity_threshold

        self.e1 = e1
        self.e2 = e2

        self.sim = Similarity()

        if compressor is not None:
            self.compressor = Compress.by_name(compressor.upper())
        else:
            self.compressor = Compress.SNAPPY
        self.sim.set_compress_type(self.compressor)

        # Initialize the filters
        # FIXME: this could be replaced by attributes on this class instead of the large dict.
        self.filters = {
            BASE: F,
            ELEMENTS: dict(),
            HASHSUM: dict(),
            IDENTICAL_ELEMENTS: set(),
            SIMILAR_ELEMENTS: [],
            HASHSUM_SIMILAR_ELEMENTS: [],
            NEW_ELEMENTS: set(),
            HASHSUM_NEW_ELEMENTS: [],
            DELETED_ELEMENTS: [],
            SKIPPED_ELEMENTS: [],
            SIMILARITY_ELEMENTS: dict(),
            SIMILARITY_SORT_ELEMENTS: dict(),
            }

        self._init_filters()
        self._init_index_elements()
        self._init_similarity()
        self._init_sort_elements()
        self._init_new_elements()

    def _init_filters(self):
        """Initialize all the dictionary structures"""
        self.filters[ELEMENTS][self.e1] = []
        self.filters[HASHSUM][self.e1] = []

        self.filters[ELEMENTS][self.e2] = []
        self.filters[HASHSUM][self.e2] = []

        self.set_els = dict()
        self.ref_set_els = dict()
        self.ref_set_ident = dict()

    def _init_index_elements(self):
        """
        Starts to add all elements from the two iterators
        to the filter structure and calculate hashes for all elements.
        """
        self.__init_index_elements(self.e1)
        self.__init_index_elements(self.e2)

    def __init_index_elements(self, iterable):
        # TODO: We can probably spare some of those dicts...
        self.set_els[iterable] = set()
        self.ref_set_els[iterable] = dict()
        self.ref_set_ident[iterable] = dict()

        for element in iterable:
            # Generate the Elements for storing the hashes in
            # This element must have the methods get_info, set_checksum, __hash__
            e = self.filters[BASE][FILTER_ELEMENT_METH](element, iterable)

            # Check if the element shall be skipped
            if self.filters[BASE][FILTER_SKIPPED_METH].skip(e):
                self.filters[SKIPPED_ELEMENTS].append(e)
                continue

            # Add the element to the list of elements for the given Iterable
            self.filters[ELEMENTS][iterable].append(e)
            # Create the Checksum object, which might transform the content
            # and is used to calculate distances and checksum.
            fm = self.filters[BASE][FILTER_CHECKSUM_METH](e, self.sim)
            e.set_checksum(fm)

            # Hash the content and add the hash to our list of known hashes
            element_hash = hash(e)
            self.filters[HASHSUM][iterable].append(element_hash)

            if element_hash not in self.set_els[iterable]:
                self.set_els[iterable].add(element_hash)
                self.ref_set_els[iterable][element_hash] = e

                self.ref_set_ident[iterable][element_hash] = []
            self.ref_set_ident[iterable][element_hash].append(e)

    def _init_similarity(self):
        """
        Calculate the similarites between all elements

        As a first step, we identify all identical elements.
        Then we iterate over the leftovers and calculate the similarity.
        """
        # Get all elements which are in common -> these are identical
        intersection_elements = self.set_els[self.e2].intersection(self.set_els[self.e1])
        # Get all elements which are different
        difference_elements = self.set_els[self.e2].difference(intersection_elements)
        # We remove the set of intersected elements from e1
        to_test = self.set_els[self.e1].difference(intersection_elements)

        # Update the IDENTICAL_ELEMENTS with the actual Elements
        self.filters[IDENTICAL_ELEMENTS].update([self.ref_set_els[self.e1][i] for i in intersection_elements])

        available_e2_elements = [self.ref_set_els[self.e2][i] for i in difference_elements]

        # Check if some elements in the first file has been modified
        # We compare all different elements from e1 with all different elements from e2
        # Hence, we create a similarity matrix with size n * m
        # where n is the number of different items in e1
        # and m is the number of different items in e2
        for j in [self.ref_set_els[self.e1][i] for i in to_test]:
            self.filters[SIMILARITY_ELEMENTS][j] = dict()
            for k in available_e2_elements:
                # Calculate and store the similarity between j and k
                self.filters[SIMILARITY_ELEMENTS][j][k] = self.filters[BASE][FILTER_SIM_METH](self.sim, j, k)

            # Store, that j has similar elements
            if hash(j) not in self.filters[HASHSUM_SIMILAR_ELEMENTS]:
                self.filters[SIMILAR_ELEMENTS].append(j)
                self.filters[HASHSUM_SIMILAR_ELEMENTS].append(hash(j))

    def _init_sort_elements(self):
        """
        Now we threshold the similarity value and get the most similar item
        If there is no similar item with respect to the threhsold,
        we think this item got deleted.
        """
        deleted_elements = []
        for j in self.filters[SIMILAR_ELEMENTS]:
            sort_h = self.filters[BASE][FILTER_SORT_METH](j, self.filters[SIMILARITY_ELEMENTS][j], self.threshold)
            self.filters[SIMILARITY_SORT_ELEMENTS][j] = set(i[0] for i in sort_h)

            if sort_h == []:
                deleted_elements.append(j)

        for j in deleted_elements:
            self.filters[DELETED_ELEMENTS].append(j)
            self.filters[SIMILAR_ELEMENTS].remove(j)

    def __checksort(self, x, y):
        return y in self.filters[SIMILARITY_SORT_ELEMENTS][x]

    def _init_new_elements(self):
        """
        As we have now identified the deleted items,
        We can identify new items.
        We regard all items as new, if they are in the second iterable
        but do not have any connection from the first.
        """
        # Check if some elements in the second file are totally new !
        for j in self.filters[ELEMENTS][self.e2]:
            # new elements can't be in similar elements
            if j not in self.filters[SIMILAR_ELEMENTS]:
                # new elements hashes can't be in first file
                if hash(j) not in self.filters[HASHSUM][self.e1]:
                    ok = True
                    # new elements can't be compared to another one
                    for diff_element in self.filters[SIMILAR_ELEMENTS]:
                        if self.__checksort(diff_element, j):
                            ok = False
                            break

                    if ok:
                        if hash(j) not in self.filters[HASHSUM_NEW_ELEMENTS]:
                            self.filters[NEW_ELEMENTS].add(j)
                            self.filters[HASHSUM_NEW_ELEMENTS].append(hash(j))

    def get_similar_elements(self):
        """
        Return the similar elements
        """
        return self.get_elem(SIMILAR_ELEMENTS)

    def get_new_elements(self):
        """
        Return the new elements
        """
        return self.get_elem(NEW_ELEMENTS)

    def get_deleted_elements(self):
        """
        Return the deleted elements
        """
        return self.get_elem(DELETED_ELEMENTS)

    def get_identical_elements(self):
        """
        Return the identical elements
        """
        return self.get_elem(IDENTICAL_ELEMENTS)

    def get_skipped_elements(self):
        """
        Get a list if skipped Elements
        """
        return self.get_elem(SKIPPED_ELEMENTS)

    def get_elem(self, attr):
        """
        Wrapper to get elements from the list with name attr
        """
        return [x for x in self.filters[attr]]

    def show_element(self, i, details=True):
        print("\t", i.get_info())

        if not details:
            return

        if hash(i) in self.ref_set_els[self.e2]:
            if len(self.ref_set_ident[self.e2][hash(i)]) > 1:
                for ident in self.ref_set_ident[self.e2][hash(i)]:
                    print("\t\t-->", ident.get_info())
            else:
                print(
                    "\t\t-->", self.ref_set_els[self.e2][hash(i)].get_info())
        else:
            for j in self.filters[SIMILARITY_SORT_ELEMENTS][i]:
                print("\t\t-->", j.get_info(),
                      self.filters[SIMILARITY_ELEMENTS][i][j])

    def get_element_info(self, i):
        l = []

        if hash(i) in self.ref_set_els[self.e2]:
            l.append([i, self.ref_set_els[self.e2][hash(i)]])
        else:
            for j in self.filters[SIMILARITY_SORT_ELEMENTS][i]:
                l.append([i, j, self.filters[SIMILARITY_ELEMENTS][i][j]])
        return l

    def get_associated_element(self, i):
        return list(self.filters[SIMILARITY_SORT_ELEMENTS][i])[0]

    def _similarity_threshold(self, value):
        # This basically sets the distance to maximum if a certain value is reached
        # TODO: I do not fully understand the rationale behind this...
        return 1.0 if value >= self.similarity_threshold else value

    def get_similarity_value(self, new=True, deleted=True):
        """
        Returns a score in percent of how similar the two files are

        The similarity value is calculated as the average similarity
        between all filtered elements.

        :param bool new: Should new elements regarded as beeing dissimilar
        :param bool deleted: Should deleted elements regarded as beeing dissimilar
        """
        values = []

        for j in self.filters[SIMILAR_ELEMENTS]:
            k = self.get_associated_element(j)
            value = self.filters[BASE][FILTER_SIM_METH](self.sim, j, k)
            # filter value
            values.append(self._similarity_threshold(value))

        # Identical Elements have a distance of 0
        values.extend([self._similarity_threshold(0.0) for i in self.filters[IDENTICAL_ELEMENTS]])

        if new:
            # New Elements have a distance of 1
            values.extend([self._similarity_threshold(1.0) for i in self.filters[NEW_ELEMENTS]])

        if deleted:
            # Deleted Elements have a distance of 1
            values.extend([self._similarity_threshold(1.0) for i in self.filters[DELETED_ELEMENTS]])

        # So actually we are calculating the NCS here from all the NCD values...
        # As NCS = 1 - NCD, we just need to calculate that.
        # Then we take the arithmetic mean and return it as percentage
        return sum([1.0 - i for i in values]) / max(len(values), 1) * 100

    def show(self):
        """
        Print information about the elements to stdout
        """
        print("Compression:   {}".format(self.compressor.name))
        print("Elements:")
        print("    IDENTICAL: {}".format(len(self.get_identical_elements())))
        print("    SIMILAR:   {}".format(len(self.get_similar_elements())))
        print("    NEW:       {}".format(len(self.get_new_elements())))
        print("    DELETED:   {}".format(len(self.get_deleted_elements())))
        print("    SKIPPED:   {}".format(len(self.get_skipped_elements())))
        print("")
        print("Similarity:    {: 3.4f}%".format(self.get_similarity_value()))


ADDED_ELEMENTS = "added elements"
DELETED_ELEMENTS = "deleted elements"
LINK_ELEMENTS = "link elements"
DIFF = "diff"


class Eldiff(object):
    def __init__(self, elsim, F):
        self.elsim = elsim
        self.F = F

        self._init_filters()
        self._init_diff()

    def _init_filters(self):
        self.filters = {}

        self.filters[BASE] = {}
        self.filters[BASE].update(self.F)
        self.filters[ELEMENTS] = {}
        self.filters[ADDED_ELEMENTS] = {}
        self.filters[DELETED_ELEMENTS] = {}
        self.filters[LINK_ELEMENTS] = {}

    def _init_diff(self):
        for i, j in self.elsim.get_elements():
            self.filters[ADDED_ELEMENTS][j] = []
            self.filters[DELETED_ELEMENTS][i] = []

            x = self.filters[BASE][DIFF](i, j)

            self.filters[ADDED_ELEMENTS][j].extend(x.get_added_elements())
            self.filters[DELETED_ELEMENTS][i].extend(x.get_deleted_elements())

            self.filters[LINK_ELEMENTS][j] = i

    def show(self):
        for bb in self.filters[LINK_ELEMENTS]:
            print(bb.get_info(), self.filters[LINK_ELEMENTS][bb].get_info())

            print("Added Elements(%d)" %
                  (len(self.filters[ADDED_ELEMENTS][bb])))
            for i in self.filters[ADDED_ELEMENTS][bb]:
                print("\t", end=' ')
                i.show()

            print("Deleted Elements(%d)" % (
                len(self.filters[DELETED_ELEMENTS][self.filters[LINK_ELEMENTS][bb]])))
            for i in self.filters[DELETED_ELEMENTS][self.filters[LINK_ELEMENTS][bb]]:
                print("\t", end=' ')
                i.show()
            print()

    def get_added_elements(self):
        return self.filters[ADDED_ELEMENTS]

    def get_deleted_elements(self):
        return self.filters[DELETED_ELEMENTS]
