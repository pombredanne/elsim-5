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


FILTER_ELEMENT_METH = "FILTER_ELEMENT_METH"
# function to checksum an element
FILTER_CHECKSUM_METH = "FILTER_CHECKSUM_METH"
# function to calculate the similarity between two elements
FILTER_SIM_METH = "FILTER_SIM_METH"
# function to sort all similar elements
FILTER_SORT_METH = "FILTER_SORT_METH"
# value which used in the sort method to eliminate not interesting comparisons
FILTER_SORT_VALUE = "FILTER_SORT_VALUE"
# object to skip elements
FILTER_SKIPPED_METH = "FILTER_SKIPPED_METH"
# function to modify values of the similarity
FILTER_SIM_VALUE_METH = "FILTER_SIM_VALUE_METH"

BASE = "base"
ELEMENTS = "elements"
HASHSUM = "hashsum"
SIMILAR_ELEMENTS = "similar_elements"
HASHSUM_SIMILAR_ELEMENTS = "hash_similar_elements"
NEW_ELEMENTS = "newelements"
HASHSUM_NEW_ELEMENTS = "hash_new_elements"
DELETED_ELEMENTS = "deletedelements"
IDENTICAL_ELEMENTS = "identicalelements"
INTERNAL_IDENTICAL_ELEMENTS = "internal identical elements"
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
    Such a function must return and object which has the following properties:
    :code:`set_checksum`, :code:`getsha256`.

    The filter is required to have the following keys:

    * FILTER_ELEMENT_METH
    * FILTER_SKIPPED_METH
    * FILTER_CHECKSUM_METH
    * FILTER_SIM_METH
    * FILTER_SIM_VALUE_METH
    * FILTER_SORT_METH
    * FILTER_SORT_VALUE
    """
    def __init__(self, e1, e2, F, threshold=None, compressor=None):
        """
        
        :param Proxy e1: the first element to compare
        :param Proxy e2: the second element to compare
        :param dict F: Some Filter dictionary
        :param float threshold: threshold for filtering similar items, which overwrites the one in the Filter
        :param str compressor: compression method name, or None to use the default one
        """
        self.e1 = e1
        self.e2 = e2
        if F is None:
            raise ValueError("A valid filter dict is required!")

        if threshold is not None:
            # overwrite the threshold if specified
            debug("Overwriting threshold {} with {}".format(F[FILTER_SORT_VALUE], threshold))
            F[FILTER_SORT_VALUE] = threshold

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
        self.__init_index_elements(self.e1)
        self.__init_index_elements(self.e2)

    def __init_index_elements(self, iterable):
        self.set_els[iterable] = set()
        self.ref_set_els[iterable] = {}
        self.ref_set_ident[iterable] = {}

        for element in iterable:
            e = self.filters[BASE][FILTER_ELEMENT_METH](element, iterable)

            if self.filters[BASE][FILTER_SKIPPED_METH].skip(e):
                self.filters[SKIPPED_ELEMENTS].append(e)
                continue

            self.filters[ELEMENTS][iterable].append(e)
            fm = self.filters[BASE][FILTER_CHECKSUM_METH](e, self.sim)
            e.set_checksum(fm)

            sha256 = e.getsha256()
            self.filters[HASHSUM][iterable].append(sha256)

            if sha256 not in self.set_els[iterable]:
                self.set_els[iterable].add(sha256)
                self.ref_set_els[iterable][sha256] = e

                self.ref_set_ident[iterable][sha256] = []
            self.ref_set_ident[iterable][sha256].append(e)

    def _init_similarity(self):
        intersection_elements = self.set_els[self.e2].intersection(self.set_els[self.e1])
        difference_elements = self.set_els[self.e2].difference(intersection_elements)

        self.filters[IDENTICAL_ELEMENTS].update([self.ref_set_els[self.e1][i] for i in intersection_elements])
        available_e2_elements = [self.ref_set_els[self.e2][i] for i in difference_elements]

        # Check if some elements in the first file has been modified
        for j in self.filters[ELEMENTS][self.e1]:
            self.filters[SIMILARITY_ELEMENTS][j] = dict()

            #debug("SIM FOR %s" % (j.get_info()))
            if j.getsha256() not in self.filters[HASHSUM][self.e2]:
                #eln = ElsimNeighbors( j, available_e2_elements )
                # for k in eln.cmp_elements():
                for k in available_e2_elements:
                    #debug("%s" % k.get_info())
                    self.filters[SIMILARITY_ELEMENTS][j][k] = self.filters[BASE][FILTER_SIM_METH](self.sim, j, k)
                    if j.getsha256() not in self.filters[HASHSUM_SIMILAR_ELEMENTS]:
                        self.filters[SIMILAR_ELEMENTS].append(j)
                        self.filters[HASHSUM_SIMILAR_ELEMENTS].append(j.getsha256())

    def _init_sort_elements(self):
        deleted_elements = []
        for j in self.filters[SIMILAR_ELEMENTS]:
            sort_h = self.filters[BASE][FILTER_SORT_METH](j, self.filters[SIMILARITY_ELEMENTS][j], self.filters[BASE][FILTER_SORT_VALUE])
            self.filters[SIMILARITY_SORT_ELEMENTS][j] = set(i[0] for i in sort_h)

            if sort_h == []:
                deleted_elements.append(j)

        for j in deleted_elements:
            self.filters[DELETED_ELEMENTS].append(j)
            self.filters[SIMILAR_ELEMENTS].remove(j)

    def __checksort(self, x, y):
        return y in self.filters[SIMILARITY_SORT_ELEMENTS][x]

    def _init_new_elements(self):
        # Check if some elements in the second file are totally new !
        for j in self.filters[ELEMENTS][self.e2]:
            # new elements can't be in similar elements
            if j not in self.filters[SIMILAR_ELEMENTS]:
                # new elements hashes can't be in first file
                if j.getsha256() not in self.filters[HASHSUM][self.e1]:
                    ok = True
                    # new elements can't be compared to another one
                    for diff_element in self.filters[SIMILAR_ELEMENTS]:
                        if self.__checksort(diff_element, j):
                            ok = False
                            break

                    if ok:
                        if j.getsha256() not in self.filters[HASHSUM_NEW_ELEMENTS]:
                            self.filters[NEW_ELEMENTS].add(j)
                            self.filters[HASHSUM_NEW_ELEMENTS].append(j.getsha256())

    def get_similar_elements(self):
        """ Return the similar elements
            @rtype : a list of elements
        """
        return self.get_elem(SIMILAR_ELEMENTS)

    def get_new_elements(self):
        """ Return the new elements
            @rtype : a list of elements
        """
        return self.get_elem(NEW_ELEMENTS)

    def get_deleted_elements(self):
        """ Return the deleted elements
            @rtype : a list of elements
        """
        return self.get_elem(DELETED_ELEMENTS)

    def get_internal_identical_elements(self, ce):
        """ Return the internal identical elements
            @rtype : a list of elements
        """
        return self.get_elem(INTERNAL_IDENTICAL_ELEMENTS)

    def get_identical_elements(self):
        """ Return the identical elements
            @rtype : a list of elements
        """
        return self.get_elem(IDENTICAL_ELEMENTS)

    def get_skipped_elements(self):
        return self.get_elem(SKIPPED_ELEMENTS)

    def get_elem(self, attr):
        return [x for x in self.filters[attr]]

    def show_element(self, i, details=True):
        print("\t", i.get_info())

        if not details:
            return

        if i.getsha256() is None:
            pass
        elif i.getsha256() in self.ref_set_els[self.e2]:
            if len(self.ref_set_ident[self.e2][i.getsha256()]) > 1:
                for ident in self.ref_set_ident[self.e2][i.getsha256()]:
                    print("\t\t-->", ident.get_info())
            else:
                print(
                    "\t\t-->", self.ref_set_els[self.e2][i.getsha256()].get_info())
        else:
            for j in self.filters[SIMILARITY_SORT_ELEMENTS][i]:
                print("\t\t-->", j.get_info(),
                      self.filters[SIMILARITY_ELEMENTS][i][j])

    def get_element_info(self, i):
        l = []

        if i.getsha256() == None:
            pass
        elif i.getsha256() in self.ref_set_els[self.e2]:
            l.append([i, self.ref_set_els[self.e2][i.getsha256()]])
        else:
            for j in self.filters[SIMILARITY_SORT_ELEMENTS][i]:
                l.append([i, j, self.filters[SIMILARITY_ELEMENTS][i][j]])
        return l

    def get_associated_element(self, i):
        return list(self.filters[SIMILARITY_SORT_ELEMENTS][i])[0]

    def get_similarity_value(self, new=True):
        """
        Returns a score in percent of how similar the two files are

        The similarity value is calculated as the average similarity
        between all elements. (?)

        :param bool new: ???
        """
        values = []

        for j in self.filters[SIMILAR_ELEMENTS]:
            k = self.get_associated_element(j)
            value = self.filters[BASE][FILTER_SIM_METH](self.sim, j, k)
            # filter value
            value = self.filters[BASE][FILTER_SIM_VALUE_METH](value)

            values.append(value)

        values.extend([self.filters[BASE][FILTER_SIM_VALUE_METH](0.0)
                       for i in self.filters[IDENTICAL_ELEMENTS]])
        if new:
            values.extend([self.filters[BASE][FILTER_SIM_VALUE_METH](1.0)
                           for i in self.filters[NEW_ELEMENTS]])
        else:
            values.extend([self.filters[BASE][FILTER_SIM_VALUE_METH](1.0)
                           for i in self.filters[DELETED_ELEMENTS]])

        # So actually we are calculating the NCS here from all the NCD values...
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
            #self.filters[ LINK_ELEMENTS ][ i ] = j

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
