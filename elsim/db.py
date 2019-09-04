#!/usr/bin/env python

# This file is part of Elsim.
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

import re
import json
from collections import defaultdict
from operator import itemgetter

from hashes.simhash import simhash

from elsim import sign


class DBFormat:
    def __init__(self, filename):
        self.filename = filename

        try:
            with open(self.filename, "r+") as fd:
                self.D = json.load(fd)
        except IOError:
            print("Impossible to open filename: " + filename)
            self.D = dict()

        # H is used as a lookup structure. Only D is ever saved!
        self.H = defaultdict(lambda: defaultdict(dict))

        for i, v in self.D.items():
            for j, vv in v.items():
                for k, vvv in vv.items():
                    if isinstance(vvv, dict):
                        self.H[i][j][k] = set(map(int, vvv.keys()))

    def add_element(self, name, sname, sclass, size, elem):
        """
        Adds a single method to the tree structure
        if the method is not already in the tree.

        :param str name: first tree element
        :param str sname: second tree element
        :param str sclass: the class name (third tree element)
        :param int size: size of the method
        :param int elem: simhash of the method
        """
        if name not in self.D:
            self.D[name] = dict()

        if sname not in self.D[name]:
            self.D[name][sname] = dict()
            self.D[name][sname]["SIZE"] = 0

        if sclass not in self.D[name][sname]:
            self.D[name][sname][sclass] = dict()

        if elem not in self.D[name][sname][sclass]:
            self.D[name][sname]["SIZE"] += size
            self.D[name][sname][sclass][elem] = size

    def is_present(self, elem):
        for i in self.D:
            if elem in self.D[i]:
                return True, i
        return False, None

    def elems_are_presents(self, elems):
        ret = defaultdict(lambda: defaultdict(dict))
        info = defaultdict(lambda: defaultdict(dict))

        for i in self.H:
            for j in self.H[i]:
                for k in self.H[i][j]:
                    val = [self.H[i][j][k].intersection(elems), len(self.H[i][j][k]), 0, 0]

                    size = 0
                    for z in val[0]:
                        size += self.D[i][j][k][str(z)]

                    val[2] = (float(len(val[0]))/(val[1])) * 100
                    val[3] = size

                    if val[3] != 0:
                        ret[i][j][k] = val

                info[i][j]["SIZE"] = self.D[i][j]["SIZE"]

        return ret, info

    def show(self):
        """
        print the database to stdout
        """
        for i in self.D:
            print(i)
            for j in self.D[i]:
                print("\t", j, len(self.D[i][j]))
                for k in self.D[i][j]:
                    if isinstance(self.D[i][j][k], dict):
                        print("\t\t", k, len(self.D[i][j][k]))
                    else:
                        print("\t\t", k, self.D[i][j][k])

    def save(self):
        """
        Save the database as JSON file to disk
        """
        with open(self.filename, "w") as fd:
            json.dump(self.D, fd)


class ElsimDB:
    """
    Provides an interface to import data into the Elsim Database
    and lookup percentages of similarity later.

    If the interface is used using context guards,
    it will save the database to disk by default!

    .. todo::
        although simhashes are computed here, they are never used
        in the lookup!
    """
    def __init__(self, output, autosave=True):
        """
        :param str output: the filename of the database
        """
        self.db = DBFormat(output)
        self.__autosave = autosave

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        if self.__autosave:
            self.save()

    def _eval_res(self, ret, info, threshold=10.0):
        """
        :param ret:
        :param info:
        :param float threshold: threshold in percent when outputs shall be produced
        """
        sorted_elems = defaultdict(list)

        for name, name_values in ret.items():
            for subname, subname_values in name_values.items():
                t_size = 0
                elems = set()

                for k, val in subname_values.items():
                    if len(val[0]) == 1 and val[1] > 1:
                        continue

                    t_size += val[-1]
                    elems.add(k)

                percentage_size = (t_size / float(info[name][subname]["SIZE"])) * 100

                if percentage_size > threshold:
                    sorted_elems[name].append((subname, percentage_size, elems))

        return sorted_elems

    def percentages(self, vmx, threshold=10):
        elems_hash = set()

        signature_module = sign.Signature(vmx)

        for _cls in vmx.get_classes():
            if _cls.is_external():
                continue
            _class = _cls.get_vm_class()

            for method in _class.get_methods():
                code = method.get_code()
                if code is None:
                    continue
                # FIXME: shouldnt here not apply the same rules as on import?
                # Like skip constructors and too short methods?
                for i in signature_module.get_method_signature(method, predef_sign=sign.PredefinedSignature.SEQUENCE_BB).get_list():
                    elems_hash.add(int(simhash(i)))

        ret, info = self.db.elems_are_presents(elems_hash)
        sorted_ret = self._eval_res(ret, info, threshold)

        info = defaultdict(list)

        for k, values in sorted_ret.items():
            for j in sorted(values, key=itemgetter(1), reverse=True):
                info[k].append([j[0], j[1]])

        return info

    def add(self, dx, name, sname, regexp_pattern=None, regexp_exclude_pattern=None):
        """
        Add all classes which match certain rules to the database.

        Only methods with a length >= 50 are added.
        No constructor (static and normal) methods are added.

        Additional exlcludes or whitelists can be defined by classnames
        as regexes.
        
        :param androguard.core.analysis.analysis.Analysis dx:
        :param str name: name, the first key in the tree
        :param str sname: subname, the second key in the tree
        :param str regexp_pattern: whitelist regex pattern
        :param str regexp_exclude_pattern: blacklist regex pattern
        """
        sign_module = sign.Signature(dx)

        for _cls in dx.get_classes():
            if _cls.is_external():
                continue
            _class = _cls.get_vm_class()

            # whitelist
            if regexp_pattern and not re.match(regexp_pattern, _class.get_name()):
                continue

            # blacklist
            if regexp_exclude_pattern and re.match(regexp_exclude_pattern, _class.get_name()):
                continue

            print("\tadding", _class.get_name())
            for method in _class.get_methods():
                code = method.get_code()
                if not code or method.get_length() < 50 or method.get_name() in ("<clinit>", "<init>"):
                    continue

                buff_list = sign_module.get_method_signature(method, predef_sign=sign.PredefinedSignature.SEQUENCE_BB).get_list()
                if len(set(buff_list)) == 1:
                    continue

                for e in buff_list:
                    self.db.add_element(name, sname, str(_class.get_name()), method.get_length(), int(simhash(e)))

    def save(self):
        self.db.save()
