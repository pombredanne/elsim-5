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


def FIX_FORMULA(x, z):
    # FIXME: remove it and only use new sigs
    if "0" in x:
        x = x.replace("and", "&&")
        x = x.replace("or", "||")

        for i in range(0, z):
            t = "%c" % (ord('a') + i)
            x = x.replace("%d" % i, t)

        return x
    return x


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

        # FIXME FORMULA (old version)
        y = FIX_FORMULA(y, len(z))

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


class PublicCSignature:
    def add_file(self, srules):
        l = []
        rules = json.loads(srules)

        ret_type = androconf.is_android(rules[0]["SAMPLE"])
        if ret_type == "APK":
            a = apk.APK(rules[0]["SAMPLE"])
            classes_dex = a.get_dex()
        elif ret_type == "DEX":
            classes_dex = read(rules[0]["SAMPLE"])
        elif ret_type == "ELF":
            elf_file = read(rules[0]["SAMPLE"])
        else:
            return None

        if ret_type == "APK" or ret_type == "DEX":
            vm = dvm.DalvikVMFormat(classes_dex)
            vmx = analysis.Analysis(vm)

        for i in rules[1:]:
            x = {i["NAME"]: []}

            sign = []
            for j in i["SIGNATURE"]:
                z = []
                if j["TYPE"] == "METHSIM":
                    z.append(SimMethod.METH)
                    m = vm.get_method_descriptor(j["CN"], j["MN"], j["D"])
                    if m is None:
                        print("impossible to find", j["CN"], j["MN"], j["D"])
                        raise("ooo")

                    # print m.get_length()

                    z_tmp = create_entropies(vmx, m)
                    print(z_tmp[0])
                    z_tmp[0] = base64.b64encode(z_tmp[0])
                    z.extend(z_tmp)
                elif j["TYPE"] == "CLASSSIM":
                    for c in vm.get_classes():
                        if j["CN"] == c.get_name():
                            z.append(SimMethod.CLASS)
                            value = ""
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

                            z.extend([base64.b64encode(value),
                                      android_entropy/nb_methods,
                                      java_entropy/nb_methods,
                                      hex_entropy/nb_methods,
                                      exception_entropy/nb_methods])
                else:
                    return None

                sign.append(z)

            x[i["NAME"]].append(sign)
            x[i["NAME"]].append(FIX_FORMULA(i["BF"], len(sign)))
            l.append(x)
        print(l)
        return l

    def get_info(self, srules):
        rules = json.loads(srules)

        ret_type = androconf.is_android(rules[0]["SAMPLE"])
        if ret_type == "APK":
            a = apk.APK(rules[0]["SAMPLE"])
            classes_dex = a.get_dex()
        elif ret_type == "DEX":
            classes_dex = read(rules[0]["SAMPLE"])
        # elif ret_type == "ELF":
            #elf_file = read( rules[0]["SAMPLE"])
        else:
            return None

        if ret_type == "APK" or ret_type == "DEX":
            vm = dvm.DalvikVMFormat(classes_dex)
            vmx = analysis.Analysis(vm)

        res = []
        for i in rules[1:]:
            for j in i["SIGNATURE"]:
                if j["TYPE"] == "METHSIM":
                    m = vm.get_method_descriptor(j["CN"], j["MN"], j["D"])
                    if m is None:
                        print("impossible to find", j["CN"], j["MN"], j["D"])
                    else:
                        res.append(m)

                elif j["TYPE"] == "CLASSSIM":
                    for c in vm.get_classes():
                        if j["CN"] == c.get_name():
                            res.append(c)

        return vm, vmx, res


class CSignature:
    def __init__(self, pcs=PublicCSignature):
        self.pcs = pcs()

    def add_file(self, srules):
        return self.pcs.add_file(srules)

    def get_info(self, srules):
        return self.pcs.get_info(srules)

    def list_indb(self, output):
        s = similarity.Similarity()
        s.set_compress_type(similarity.Compress.ZLIB)

        buff = json.loads(read(output, binary=False))
        for i in buff:
            print(i)
            for j in buff[i][0]:
                sign = base64.b64decode(j[1])
                print("\t", j[0], "ENTROPIES:", j[2:], "L:%d" %
                      len(sign), "K:%d" % s.kolmogorov(sign)[0])
            print("\tFORMULA:", buff[i][-1])

    def check_db(self, output):
        ids = {}
        meth_sim = []
        class_sim = []

        buff = json.loads(read(output, binary=False))
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
        buff = json.loads(read(output, binary=False))
        del buff[signature]

        with open(output, "w") as fd:
            fd.write(json.dumps(buff))

    def add_indb(self, signatures, output):
        if signatures is None:
            return

        with open(output, "a+") as fd:
            buff = fd.read()
            if buff == "":
                buff = {}
            else:
                buff = json.loads(buff)

        for i in signatures:
            buff.update(i)

        with open(output, "w") as fd:
            fd.write(json.dumps(buff))
