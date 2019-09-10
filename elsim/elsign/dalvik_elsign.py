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

import os
import sys
import json
import base64
import enum

from pprint import pprint

from androguard.core.bytecodes import apk
from androguard.core.bytecodes import dvm

from androguard.core.analysis import analysis
from androguard.core import androconf
from androguard.util import read

from elsim.elsign.libelsign import Elsign, entropy
from elsim import similarity
from elsim import sign
from elsim import utils


class SimMethod(enum.IntEnum):
    """Similarity method type"""
    METH = 0
    CLASS = 1


def create_entropies(vmx, m):
    """
    :param elsim.sign.Signature vmx:
    :param androguard.core.bytecodes.dvm.EncodedMethod m:
    """
    return [vmx.get_method_signature(m, predef_sign=sign.PredefinedSignature.L0_4).get_string(),
            entropy(vmx.get_method_signature(m, "L4", {"L4": {"arguments": ["Landroid"]}}).get_string()),
            entropy(vmx.get_method_signature(m, "L4", {"L4": {"arguments": ["Ljava"]}}).get_string()),
            entropy(vmx.get_method_signature(m, "hex").get_string()),
            entropy(vmx.get_method_signature(m, "L2").get_string()),
            ]


class DalvikElsign:
    def __init__(self):
        self.debug = False
        self.meth_elsign = Elsign()
        self.class_elsign = Elsign()

    def raz(self):
        self.meth_elsign.raz()
        self.class_elsign.raz()

    def load_config(self, buff):
        if self.debug:
            pprint(buff)

        methsim = buff["METHSIM"]
        self.meth_elsign.set_distance(methsim["DISTANCE"].encode('ascii'))
        self.meth_elsign.set_method(methsim["METHOD"].encode('ascii'))
        self.meth_elsign.set_weight(methsim["WEIGHTS"])
        self.meth_elsign.set_sim_method(0)  # NCD
        self.meth_elsign.set_threshold_low(methsim["THRESHOLD_LOW"])
        self.meth_elsign.set_threshold_high(methsim["THRESHOLD_HIGH"])
        self.meth_elsign.set_ncd_compression_algorithm(similarity.Compress.BZ2.value)

        classsim = buff["CLASSSIM"]
        self.class_elsign.set_distance(classsim["DISTANCE"].encode('ascii'))
        self.class_elsign.set_method(classsim["METHOD"].encode('ascii'))
        self.class_elsign.set_weight(classsim["WEIGHTS"])
        #self.class_elsign.set_cut_element( 1 )
        self.class_elsign.set_sim_method(0)  # NCD
        self.class_elsign.set_threshold_low(classsim["THRESHOLD_LOW"])
        self.class_elsign.set_threshold_high(classsim["THRESHOLD_HIGH"])
        self.class_elsign.set_ncd_compression_algorithm(similarity.Compress.BZ2.value)

    def add_signature(self, type_signature, x, y, z):
        """
        Adds a given signature to the elsign module

        :param int type_signature:
        :param str x: the name of the siganture
        :param str y: the formular
        :param list z: the signature
        """
        if self.debug:
            print("add_signature", type_signature, x)

        # FIXME ENTROPIES (old version)
        for j in z:
            if len(j[0]) == 5:
                j[0].pop(0)

        if type_signature == SimMethod.METH:
            return self.meth_elsign.add_signature(x, y, z)
        if type_signature == SimMethod.CLASS:
            return self.class_elsign.add_signature(x, y, z)
        return

    def set_debug(self, debug):
        self.debug = debug
        self.meth_elsign.set_debug_log(self.debug)
        self.class_elsign.set_debug_log(self.debug)

    def load_meths(self, dx, vmx):
        """
        Load all methods for further analysis in METHSIM
        
        :param androguard.core.analysis.analysis.Analysis dx:
        :param elsim.sign.Signature vmx:
        """
        for mca in dx.find_methods(no_external=True):
            method = mca.get_method()
            if method.get_length() < 15:
                continue

            entropies = create_entropies(vmx, method)
            self.meth_elsign.add_element(entropies[0], entropies[1:])

    def load_classes(self, dx, vmx):
        """
        Load all classes for further analysis in CLASSSIM
        
        :param androguard.core.analysis.analysis.Analysis dx:
        :param elsim.sign.Signature vmx:
        """
        for ca in dx.find_classes(no_external=True):
            c = ca.get_vm_class()

            value = b""
            android_entropy = 0.0
            java_entropy = 0.0
            hex_entropy = 0.0
            exception_entropy = 0.0
            nb_methods = 0

            class_data = c.get_class_data()
            if class_data is None:
                continue

            for m in c.get_methods():
                z_tmp = create_entropies(vmx, m)

                value += z_tmp[0]
                android_entropy += z_tmp[1]
                java_entropy += z_tmp[2]
                hex_entropy += z_tmp[3]
                exception_entropy += z_tmp[4]

                nb_methods += 1

            if nb_methods != 0:
                self.class_elsign.add_element(value, [android_entropy/nb_methods,
                                                      java_entropy/nb_methods,
                                                      hex_entropy/nb_methods,
                                                      exception_entropy/nb_methods])
                del value, z_tmp

    def check(self, vm, vmx):
        """
        :param androguard.core.analysis.analysis.Analysis dx:
        :param elsim.sign.Signature vmx:
        """
        self.load_meths(vm, vmx)

        if self.debug:
            print("CM", end=' ')
            sys.stdout.flush()
        ret = self.meth_elsign.check()

        if self.debug:
            dt = self.meth_elsign.get_debug()
            debug_nb_sign = dt[0]
            debug_nb_clusters = dt[1]
            debug_nb_cmp_clusters = dt[2]
            debug_nb_elements = dt[3]
            debug_nb_cmp_elements = dt[4]

            debug_nb_cmp_max = debug_nb_sign * debug_nb_elements
            print("[SIGN:%d CLUSTERS:%d CMP_CLUSTERS:%d ELEMENTS:%d CMP_ELEMENTS:%d" % (
                debug_nb_sign, debug_nb_clusters, debug_nb_cmp_clusters, debug_nb_elements, debug_nb_cmp_elements), end=' ')
            try:
                percentage = debug_nb_cmp_elements/float(debug_nb_cmp_max)
            except:
                percentage = 0
            finally:
                print("-> %d %f%%]" %
                      (debug_nb_cmp_max, percentage * 100), end=' ')

            print(ret[1:], end=' ')

        if ret[0] is None:
            self.load_classes(vm, vmx)

            if self.debug:
                print("CC", end=' ')
                sys.stdout.flush()
            ret = self.class_elsign.check()

            if self.debug:
                dt = self.class_elsign.get_debug()
                debug_nb_sign = dt[0]
                debug_nb_clusters = dt[1]
                debug_nb_cmp_clusters = dt[2]
                debug_nb_elements = dt[3]
                debug_nb_cmp_elements = dt[4]

                debug_nb_cmp_max = debug_nb_sign * debug_nb_elements
                print("[SIGN:%d CLUSTERS:%d CMP_CLUSTERS:%d ELEMENTS:%d CMP_ELEMENTS:%d" % (
                    debug_nb_sign, debug_nb_clusters, debug_nb_cmp_clusters, debug_nb_elements, debug_nb_cmp_elements), end=' ')
                try:
                    percentage = debug_nb_cmp_elements/float(debug_nb_cmp_max)
                except:
                    percentage = 0
                finally:
                    print("-> %d %f%%]" %
                          (debug_nb_cmp_max, percentage * 100), end=' ')

                print(ret[1:], end=' ')

        return ret[0], ret[1:]


class PublicSignature:
    def __init__(self, database, config, debug=False):
        self.debug = debug

        self.DE = DalvikElsign()
        self.DE.set_debug(debug)

        self.database = database
        self.config = config

        if self.debug:
            print("Database File:", self.database, "Config File:", self.config)

        self._load()

    def _load(self):
        with open(self.config, 'r') as fp:
            self.DE.load_config(json.load(fp))

        with open(self.database, 'r') as fp:
            buff = json.load(fp)

        for sig_name, sig_data in buff.items():
            type_signature = None
            sub_signatures = []
            for j in sig_data[0]:
                if j[0] == SimMethod.METH:
                    type_signature = SimMethod.METH
                    sub_signatures.append([j[2:], base64.b64decode(j[1])])
                elif j[0] == SimMethod.CLASS:
                    type_signature = SimMethod.CLASS
                    sub_signatures.append([j[2:], base64.b64decode(j[1])])

            if type_signature is not None:
                self.DE.add_signature(type_signature, sig_name, sig_data[1], sub_signatures)
            else:
                print("ERROR no signature type set for signature named '{}'".format(sig_name))

    def check(self, dx, vmx):
        """

        :param androguard.core.analysis.analysis.Analysis dx:
        :param elsim.sign.Signature vmx:
        """
        ret = self.DE.check(dx, vmx)
        self.DE.raz()
        return ret


class MSignature:
    def __init__(self, dbname, dbconfig, debug=False, ps=PublicSignature):
        """
        Check if signatures from a database is present in an android application (apk/dex)

        :param str dbname: the filename of the database
        :param str dbconfig: the filename of the configuration
        :param bool debug: shall debug output be activated  # FIXME, remove
        """

        self.debug = debug
        self.p = ps(dbname, dbconfig, self.debug)

    def load(self):
        """
        Load the database
        """
        self.p.load()

    def set_debug(self):
        """
        Enable Debug mode
        """
        self.debug = True
        self.p.set_debug()

    def check(self, dx):
        """
        Check if a signature mathes the application

        :param androguard.core.analysis.analysis.Analysis dx: the Analysis module
        """
        vmx = sign.Signature(dx)
        return self.p.check(dx, vmx)


class SigCompileError(Exception):
    """Base class for compiler errors"""
    pass


class SignatureCompiler:
    """
    This is an interface to compile signatures into the form which can be used
    to match samples
    """
    def __init__(self):
        pass

    def compile(self, fname):
        """
        Compile the given file.
        The resulting signature is not yet added to the database!
        If must be put into the database manually by using :meth:`add_indb`.

        The file must be a JSON file containing the signature.

        :param str fname: filename to add
        :raises SigCompileError: if the signature can not be compiled
        """
        l = []
        with open(fname, "r") as fp:
            rules = json.load(fp)

        dx = utils.load_analysis(rules[0]["SAMPLE"])
        if dx is None:
            raise SigCompileError("Original File can not be loaded!")

        vmx = sign.Signature(dx)

        for i in rules[1:]:
            x = {i["NAME"]: []}

            signature = []
            for j in i["SIGNATURE"]:
                z = []
                if j["TYPE"] == "METHSIM":
                    m = dx.get_method_by_name(j["CN"], j["MN"], j["D"])
                    if m is None:
                        raise SigCompileError("impossible to find {}->{} {}".format(j["CN"], j["MN"], j["D"]))

                    z.append(SimMethod.METH.value)
                    z_tmp = create_entropies(vmx, m)
                    z_tmp[0] = base64.b64encode(z_tmp[0]).decode('ascii')
                    z.extend(z_tmp)
                elif j["TYPE"] == "CLASSSIM":
                    c = dx.get_class_analysis(j["CN"]).get_vm_class()
                    if c is None:
                        raise SigCompileError("impossible to find {}".format(j["CN"]))

                    z.append(SimMethod.CLASS.value)
                    value = b""
                    android_entropy = 0.0
                    java_entropy = 0.0
                    hex_entropy = 0.0
                    exception_entropy = 0.0
                    nb_methods = 0
                    for m in c.get_methods():
                        z_tmp = create_entropies(vmx, m)

                        value += z_tmp[0]
                        android_entropy += z_tmp[1]
                        java_entropy += z_tmp[2]
                        hex_entropy += z_tmp[3]
                        exception_entropy += z_tmp[4]

                        nb_methods += 1

                    z.extend([base64.b64encode(value).decode('ascii'),
                              android_entropy/nb_methods,
                              java_entropy/nb_methods,
                              hex_entropy/nb_methods,
                              exception_entropy/nb_methods])
                else:
                    raise SigCompileError("Unknown method {}".format(j["TYPE"]))

                signature.append(z)

            x[i["NAME"]].append(signature)
            x[i["NAME"]].append(i["BF"])
            l.append(x)
        return l

    @staticmethod
    def get_info(fname):
        """
        Searches for the specified contents of the signature
        in the given sample.

        A list is returned containing all EncodedMethods or ClassDefItems
        which are specified in the signature.

        The file must be a JSON file containing the signature.

        :param str fname: filename to load
        """
        with open(fname, "r") as fp:
            rules = json.load(fp)

        if "SAMPLE" not in rules[0]:
            raise ValueError("Not a valid Signature, no sample attached!")
        dx = utils.load_analysis(rules[0]["SAMPLE"])
        if dx is None:
            return []

        res = []
        for i in rules[1:]:
            for j in i["SIGNATURE"]:
                if j["TYPE"] == "METHSIM":
                    m = dx.get_method_by_name(j["CN"], j["MN"], j["D"])
                    if not m:
                        print("impossible to find", j["CN"], j["MN"], j["D"])
                    else:
                        res.append(m)

                elif j["TYPE"] == "CLASSSIM":
                    for c in dx.find_classes(j["CN"], no_external=True):
                        res.append(c.get_vm_class())

        return res

    def list_indb(self, output):
        """
        Lists information about the content of a signature database

        :param str output: the filename to load the database from
        """
        s = similarity.Similarity()
        # FIXME: why ZLIB? Any special reason?
        s.set_compress_type(similarity.Compress.ZLIB)

        with open(output, "r") as fp:
            buff = json.load(fp)
        for i in buff:
            print(i)
            for j in buff[i][0]:
                signature = base64.b64decode(j[1])
                print("\t{} ENTROPIES: {} L:{} K:{}".format(j[0], j[2:], len(signature), s.kolmogorov(signature)))
            print("\tFORMULA:", buff[i][-1])

    def check_db(self, output):
        ids = {}
        meth_sim = []
        class_sim = []

        with open(output, "r") as fp:
            buff = json.load(fp)
        for i in buff:
            nb = 0
            for ssign in buff[i][0]:
                if ssign[0] == SimMethod.METH:
                    value = base64.b64decode(ssign[1])
                    if value in ids:
                        print("IDENTICAL", ids[value], i, nb)
                    else:
                        ids[value] = (i, nb)
                        meth_sim.append(value)
                elif ssign[0] == SimMethod.CLASS:
                    ids[base64.b64decode(ssign[1])] = (i, nb)
                    class_sim.append(base64.b64decode(ssign[1]))
                nb += 1

        s = similarity.Similarity()
        s.set_compress_type(similarity.Compress.BZ2)

        self.__check_db(s, ids, meth_sim)
        self.__check_db(s, ids, class_sim)

    def __check_db(self, s, ids, elem_sim):
        problems = {}
        for i in elem_sim:
            for j in elem_sim:
                if i != j:
                    ret = s.ncd(i, j)[0]
                    if ret < 0.3:
                        ids_cmp = ids[i] + ids[j]
                        if ids_cmp not in problems:
                            s.set_compress_type(similarity.Compress.BZ2)
                            ret = s.ncd(i, j)[0]
                            print("[-] ", ids[i], ids[j], ret)
                            problems[ids_cmp] = 0
                            problems[ids[j] + ids[i]] = 0

    def remove_indb(self, signature, output):
        with open(output, "r") as fp:
            buff = json.load(fp)
        del buff[signature]

        with open(output, "w") as fd:
            fd.write(json.dumps(buff))

    def add_indb(self, signatures, output, pretty=False):
        """
        Adds the signatures compiled using :meth:`add_file` to a json database

        Existing Signatures with the same name are overwritten without notice!

        :param signature: the signature dict
        :param str output: the output file
        :param bool pretty: should the output file be indented
        """
        if signatures is None or signatures == []:
            return

        if os.path.isfile(output):
            with open(output, "r") as fd:
                try:
                    buff = json.load(fd)
                except json.decoder.JSONDecodeError:
                    print("ERROR can not load database, seems corrupted. Deleting database.")
                    os.unlink(output)
                    buff = dict()
        else:
            buff = dict()

        for i in signatures:
            buff.update(i)

        with open(output, "w") as fd:
            json.dump(buff, fd, indent=2 if pretty else None)
