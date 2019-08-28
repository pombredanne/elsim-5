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
from collections import defaultdict
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
# The resulting object must have a function set_checksum which expect the CheckSum object and a property hash
# You should also implement a meaningful __str__ method.
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

        if compressor:
            self.compressor = Compress.by_name(compressor.upper())
        else:
            self.compressor = Compress.SNAPPY
        self.sim.set_compress_type(self.compressor)

        # Initialize the filters
        # FIXME: this could be replaced by attributes on this class instead of the large dict.
        # FIXME: rethink all the items here... maybe we can remove a few
        self.filters = {
            BASE: F,
            ELEMENTS: defaultdict(list),  # for each iterable, contains all elements
            HASHSUM: defaultdict(list),  # for each iterable, contains all hashes of the elements

            # FIXME: list vs set
            IDENTICAL_ELEMENTS: set(),  # contains all identical elements from both iterables
            SIMILAR_ELEMENTS: [],  # contains all similar elements from both iterables
            NEW_ELEMENTS: set(),  # contains new elements, only from s2
            DELETED_ELEMENTS: [],  # contains deleted elements, only from s1
            SKIPPED_ELEMENTS: [],  # contains all skipped elements from both iterables

            HASHSUM_SIMILAR_ELEMENTS: [],
            SIMILARITY_ELEMENTS: dict(),
            SIMILARITY_SORT_ELEMENTS: dict(),
            }

        # Contains all Hashes of each iterable
        self.set_els = defaultdict(set)
        # Contains a lookup for the hash to get the first element with this hash, for each iterable
        self.ref_set_els = defaultdict(dict)
        # Contains a lookup for the hash to get all elements that share the same hash, for each iterable
        self.ref_set_ident = defaultdict(dict)

        # Starts to add all elements from the two iterators
        # to the filter structure and calculate hashes for all elements.
        self.__init_index_elements(self.e1)
        self.__init_index_elements(self.e2)

        # get all identical items and calculate similarity
        self._init_similarity()
        # Get Most similar item(s) and deletd items
        self._init_sort_elements()
        # Get new items
        self._init_new_elements()

    def __init_index_elements(self, iterable):
        """
        Iterate over all elements and create the Element objects and CheckSum objects
        """
        for element in iterable:
            # Generate the Elements for storing the hashes in
            # This element must have the methods set_checksum, hash
            e = self.filters[BASE][FILTER_ELEMENT_METH](element, iterable)

            # Check if the element shall be skipped
            if self.filters[BASE][FILTER_SKIPPED_METH].skip(e):
                self.filters[SKIPPED_ELEMENTS].append(e)
                continue

            # Add the element to the list of elements for the given Iterable
            self.filters[ELEMENTS][iterable].append(e)
            # Create the Checksum object, which might transform the content
            # and is used to calculate distances and checksum.
            # FIXME: We could reduce this to just a single call of FILTER_ELEMENT_METH.
            # I think the rationale behind this setup was, to be able to skip the creation
            # of the possible expensive call to FILTER_CHECKSUM_METH...
            fm = self.filters[BASE][FILTER_CHECKSUM_METH](e, self.sim)
            e.set_checksum(fm)

            # Hash the content and add the hash to our list of known hashes
            self.filters[HASHSUM][iterable].append(e.hash)

            if e.hash not in self.set_els[iterable]:
                self.set_els[iterable].add(e.hash)
                self.ref_set_els[iterable][e.hash] = e

                self.ref_set_ident[iterable][e.hash] = []
            self.ref_set_ident[iterable][e.hash].append(e)

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
            if j.hash not in self.filters[HASHSUM_SIMILAR_ELEMENTS]:
                self.filters[SIMILAR_ELEMENTS].append(j)
                self.filters[HASHSUM_SIMILAR_ELEMENTS].append(j.hash)

    def _init_sort_elements(self):
        """
        Now we threshold the similarity value and get the most similar item(s)
        If there is no similar item with respect to the threhsold,
        we think this item got deleted.

        In theory, you could return more than one similar item, but this was never done before.
        """
        deleted_elements = []
        for j in self.filters[SIMILAR_ELEMENTS]:
            sort_h = self.filters[BASE][FILTER_SORT_METH](j, self.filters[SIMILARITY_ELEMENTS][j], self.threshold)

            # Store the similar Element(s)
            self.filters[SIMILARITY_SORT_ELEMENTS][j] = set(i[0] for i in sort_h)

            if sort_h == []:
                # After thresholding, the element is not similar to anything
                deleted_elements.append(j)

        for j in deleted_elements:
            self.filters[DELETED_ELEMENTS].append(j)
            self.filters[SIMILAR_ELEMENTS].remove(j)

    def _init_new_elements(self):
        """
        As we have now identified the deleted items,
        We can identify new items.
        We regard all items as new, if they are in the second iterable
        but do not have any connection from the first.
        """
        # Check if some elements in the second file are totally new
        for j in self.filters[ELEMENTS][self.e2]:
            # new elements can't be in similar elements
            # and hashes can't be in first file, i.e. unique to second file
            if j not in self.filters[SIMILAR_ELEMENTS] and j.hash not in self.filters[HASHSUM][self.e1]:
                is_new = True
                # new elements can't be compared to another one
                for diff_element in self.filters[SIMILAR_ELEMENTS]:
                    if j in self.filters[SIMILARITY_SORT_ELEMENTS][diff_element]:
                        is_new = False
                        break

                if is_new and j not in self.filters[NEW_ELEMENTS]:
                    self.filters[NEW_ELEMENTS].add(j)

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
        """
        Show the element and similar ones and print the information to stdout.

        If details is False, do not show similar items.
        This can be useful if there are no similar ones, i.e. elements are identical, new or deleted.
        """
        print("\t", i)

        if not details:
            return

        if i.hash in self.ref_set_els[self.e2]:
            if len(self.ref_set_ident[self.e2][i.hash]) > 1:
                for ident in self.ref_set_ident[self.e2][i.hash]:
                    print("\t\t-->", str(ident))
            else:
                print("\t\t-->", str(self.ref_set_els[self.e2][i.hash]))
        else:
            for j in self.filters[SIMILARITY_SORT_ELEMENTS][i]:
                print("\t\t-->", str(j), self.filters[SIMILARITY_ELEMENTS][i][j])

    def get_element_info(self, i):
        l = []

        if i.hash in self.ref_set_els[self.e2]:
            l.append([i, self.ref_set_els[self.e2][i.hash]])
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
        The default is to count new and deleted items as "not similar".
        This behaviour can be changed by setting the according flags.
        Here is an example:

            s1 = {a, b, c}
            s2 = {a, c', d}

        In this example, element a is identical, c is similar (similarity = 0.75), b is deleted and d is new.
        The similarity score with new and deleted items would be: 1/4 * (1 + 0.75 + 0 + 0) = 43.75%.
        If neither new and deleted items would be counted: 1/2 * (1 + 0.75) = 87.5%
        If only new items would be counted: 1/3 * (1 + 0.75 + 0) = 58.33%

        Skipped Items are never investigated.

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

    def show(self, new=True, deleted=True, details=False):
        """
        Print information about the elements to stdout

        If new or deleted is set, it will print a '**' after the element count to
        indicate that these values are not used for the calculation of the similarity score.

        :param bool new: Should new elements regarded as beeing dissimilar (passed to get_similarity_value)
        :param bool deleted: Should deleted elements regarded as beeing dissimilar (passed to get_similarity_value)
        :param bool details: Print all elements for the categories
        """
        ik = len(self.get_identical_elements())
        s = len(self.get_similar_elements())
        n = len(self.get_new_elements())
        d = len(self.get_deleted_elements())
        sk = len(self.get_skipped_elements())

        # get the length of the digits and at least 3 digits
        max_digits = max(max(map(len, map(str, [ik, s, n, d, sk]))), 3)

        print("Compression:   {}".format(self.compressor.name))
        print("    IDENTICAL: {:>{width}}".format(ik, width=max_digits))
        print("    SIMILAR:   {:>{width}}".format(s, width=max_digits))
        print("    NEW:       {:>{width}}{}".format(n, " **" if not new else "", width=max_digits))
        print("    DELETED:   {:>{width}}{}".format(d, " **" if not deleted else "", width=max_digits))
        print("    SKIPPED:   {:>{width}}".format(sk, width=max_digits))
        print("")
        print("Similarity:    {:>{width}.4f}%".format(self.get_similarity_value(new, deleted), width=max_digits+5))

        if details:
            print()

            if s > 0:
                print("SIMILAR elements:")
                for i in self.get_similar_elements():
                    self.show_element(i)

            if ik > 0:
                print("IDENTICAL elements:")
                for i in self.get_identical_elements():
                    self.show_element(i, False)

            if n > 0:
                print("NEW elements:")
                for i in self.get_new_elements():
                    self.show_element(i, False)

            if d > 0:
                print("DELETED elements:")
                for i in self.get_deleted_elements():
                    self.show_element(i, False)

            if sk > 0:
                print("SKIPPED elements:")
                for i in self.get_skipped_elements():
                    self.show_element(i, False)


ADDED_ELEMENTS = "added elements"
DELETED_ELEMENTS = "deleted elements"
LINK_ELEMENTS = "link elements"
DIFF = "diff"


class Eldiff:
    def __init__(self, iterator, F):
        self.iterator = iterator
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
        for i, j in self.iterator:
            self.filters[ADDED_ELEMENTS][j] = []
            self.filters[DELETED_ELEMENTS][i] = []

            x = self.filters[BASE][DIFF](i, j)

            self.filters[ADDED_ELEMENTS][j].extend(x.get_added_elements())
            self.filters[DELETED_ELEMENTS][i].extend(x.get_deleted_elements())

            self.filters[LINK_ELEMENTS][j] = i

    def show(self):
        for bb in self.filters[LINK_ELEMENTS]:
            print(str(bb), str(self.filters[LINK_ELEMENTS][bb]))

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
