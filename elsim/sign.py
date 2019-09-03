# This file is part of Androguard.
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from collections import OrderedDict
from operator import itemgetter
from androguard.core.bytecodes import dvm
import binascii

TAINTED_PACKAGE_CREATE = 0
TAINTED_PACKAGE_CALL = 1
TAINTED_PACKAGE_INTERNAL_CALL = 2

SIGNATURE_L0_0 = "L0_0"
SIGNATURE_L0_1 = "L0_1"
SIGNATURE_L0_2 = "L0_2"
SIGNATURE_L0_3 = "L0_3"
SIGNATURE_L0_4 = "L0_4"
SIGNATURE_L0_5 = "L0_5"
SIGNATURE_L0_6 = "L0_6"
SIGNATURE_L0_0_L1 = "L0_0:L1"
SIGNATURE_L0_1_L1 = "L0_1:L1"
SIGNATURE_L0_2_L1 = "L0_2:L1"
SIGNATURE_L0_3_L1 = "L0_3:L1"
SIGNATURE_L0_4_L1 = "L0_4:L1"
SIGNATURE_L0_5_L1 = "L0_5:L1"
SIGNATURE_L0_0_L2 = "L0_0:L2"
SIGNATURE_L0_0_L3 = "L0_0:L3"
SIGNATURE_HEX = "hex"
SIGNATURE_SEQUENCE_BB = "sequencebb"

SIGNATURES = {
    SIGNATURE_L0_0: {"type": 0},
    SIGNATURE_L0_1: {"type": 1},
    SIGNATURE_L0_2: {"type": 2,
                     "arguments": ["Landroid"]},
    SIGNATURE_L0_3: {"type": 2,
                     "arguments": ["Ljava"]},
    SIGNATURE_L0_4: {"type": 2,
                     "arguments": ["Landroid", "Ljava"]},
    SIGNATURE_L0_5: {"type": 3,
                     "arguments": ["Landroid"]},
    SIGNATURE_L0_6: {"type": 3,
                     "arguments": ["Ljava"]},
    SIGNATURE_SEQUENCE_BB: {},
    SIGNATURE_HEX: {},
}


class Sign:
    """
    The Sign object contains the signature for a single Method.
    """
    def __init__(self):
        self.levels = OrderedDict()

    def add(self, level, value):
        self.levels[level] = value

    def get_level(self, l):
        return self.levels["L%d" % l]

    def get_string(self):
        return ''.join(self.levels.values())

    def get_list(self):
        return self.levels["sequencebb"]


class Signature:
    """
    The Signature is a variant of the grammar described in:

    Cesare & Xiang (2010): Classification of Malware Using Structured Control Flow

    It wraps around an :class:`~androguard.core.analysis.analysis.Analysis` object.
    """
    def __init__(self, dx):
        """
        :param androguard.core.analysis.analysis.Analysis dx:
        """
        self.dx = dx

        # Contains Sign objects for faster lookup
        self._cached_signatures = {}

        # Contains the lower level signatures for faster lookup
        self._global_cached = {}

        self.levels = {
            # Classical method signature with basic blocks, strings, fields, packages
            "L0": {
                0: ("_get_strings_a", "_get_fields_a", "_get_packages_a"),
                1: ("_get_strings_pa", "_get_fields_a", "_get_packages_a"),
                2: ("_get_strings_a", "_get_fields_a", "_get_packages_pa_1"),
                3: ("_get_strings_a", "_get_fields_a", "_get_packages_pa_2"),
            },
            # strings
            "L1": ["_get_strings_a1"],
            # exceptions
            "L2": ["_get_exceptions"],
            # fill array data
            "L3": ["_get_fill_array_data"],
        }

    def get_method_signature(self, method, grammar_type="", options={}, predef_sign=""):
        """
        Return a specific signature for a specific method

        predef_sign is a shortcut to defining grammar_type and options.

        :param androguard.core.bytecodes.dvm.EncodedMethod method: The method to create the sign
        :param str grammar_type: the type of the signature (optional)
        :param dict options: the options of the signature (optional)
        :param str predef_sign: used a predefined signature (optional)

        :rtype: Sign
        """
        if predef_sign == "" and grammar_type == "" and options == {}:
            raise ValueError("you must either specify predef_sign or grammar_type and options!")

        if predef_sign != "":
            grammar_type = []
            options = {}

            for i in predef_sign.split(":"):
                if "_" in i:
                    grammar_type.append("L0")
                    options["L0"] = SIGNATURES[i]
                else:
                    grammar_type.append(i)
            grammar_type = ':'.join(grammar_type)

        return self.get_method(self.dx.get_method(method), grammar_type, options)

    @staticmethod
    def _get_method_info(analysis_method):
        """
        Returns a string which describes the method in a unique fashion

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        """
        encmeth = analysis_method.get_method()
        return "%s-%s-%s" % (encmeth.get_class_name(), encmeth.get_name(), encmeth.get_descriptor())

    @staticmethod
    def _get_sequence_bb(analysis_method, min_instructions=6):
        """
        Returns the names of the opcodes for each non empty basic block
        which has more than n opcodes.

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :param int min_instructions: give the minimal number of instr. the function must have
        :rtype: List[str]
        """
        l = []

        for i in analysis_method.basic_blocks.get():
            instructions = [j for j in i.get_instructions()]
            if len(instructions) >= min_instructions:
                l.append(''.join(map(lambda x: x.get_name(), instructions)))

        return l

    @staticmethod
    def _get_hex(analysis_method):
        """
        Returns the decoded bytecode as text without any newlines

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        """
        buff = ""
        for i in analysis_method.get_method().get_instructions():
            buff += dvm.clean_name_instruction(i)
            buff += dvm.static_operand_instruction(i)
        return buff

    def _get_bb(self, analysis_method, functions, options):
        # FIXME: needs tests
        """

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :param List[str] functions: the functions to call
        :param options: the options which might get passed to the functions
        """
        bbs = []
        for b in analysis_method.basic_blocks.get():
            l = []
            l.append((b.start, "B"))
            l.append((b.start, "["))

            internal = []

            op_value = b.get_last().get_op_value()

            # return
            if op_value >= 0x0e and op_value <= 0x11:
                internal.append((b.end - 1, "R"))

            # if
            elif op_value >= 0x32 and op_value <= 0x3d:
                internal.append((b.end - 1, "I"))

            # goto
            elif op_value >= 0x28 and op_value <= 0x2a:
                internal.append((b.end - 1, "G"))

            # sparse or packed switch
            elif op_value >= 0x2b and op_value <= 0x2c:
                internal.append((b.end - 1, "G"))

            for f in functions:
                try:
                    internal.extend(getattr(self, f)(analysis_method, options))
                except TypeError:
                    # FIXME: okay this looks a little bit how'ya'doing...
                    internal.extend(getattr(self, f)(analysis_method))

            internal.sort()

            for i in internal:
                if i[0] >= b.start and i[0] < b.end:
                    l.append(i)

            del internal

            l.append((b.end, "]"))

            bbs.append(''.join(i[1] for i in l))
        return bbs

    @staticmethod
    def _get_fill_array_data(analysis_method):
        """
        Returns the content of fill-array-data-payloads commands

        .. warning::
            we actually have no idea what was meant here, but we assume that
            he wanted the content of the array as a hex string.
            How it was implemented did not even worked in the old androguard version...

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :rtype: str
        """
        buff = ""
        for b in analysis_method.basic_blocks.get():
            for i in b.get_instructions():
                if i.get_name() == "fill-array-data-payload":
                    buff += binascii.hexlify(i.get_data()).decode('ascii')
        return buff

    @staticmethod
    def _get_exceptions(analysis_method):
        """
        Returns the class types of the handlers as one monolithic string

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :rtype: str
        """
        buff = ""

        method = analysis_method.get_method()
        code = method.get_code()
        if code is None or code.get_tries_size() <= 0:
            # No exception handlers in the method, or no code at all
            return buff

        for handler_catch in code.get_handlers().get_list():
            for handler in handler_catch.get_handlers():
                buff += str(analysis_method.get_vm().get_cm_type(handler.get_type_idx()))
        return buff

    def _get_all_strings_by_method(self, analysis_method):
        """
        TODO: This method belongs to androguard

        :rtype: Generator[(int, str), None, None]
        """
        meth = analysis_method.get_method()
        # FIXME: this is super slow, as we always check all strings...
        for real_string, string_analysis in self.dx.get_strings_analysis().items():
            for _, src_meth, off in string_analysis.get_xref_from(withoffset=True):
                if meth == src_meth:
                    yield off, real_string

    def _get_all_fields_by_method(self, analysis_method):
        """
        TODO: This method belongs to androguard

        :rtype: Generator[(int, int), None, None]
        """
        meth = analysis_method.get_method()
        for field_analysis in self.dx.get_fields():
            # FIXME the return type is crap... should use an enum
            for _, src_meth, off in field_analysis.get_xref_read(withoffset=True):
                if meth == src_meth:
                    yield off, 0
            for _, src_meth, off in field_analysis.get_xref_write(withoffset=True):
                if meth == src_meth:
                    yield off, 1

    def _get_packages_by_method(self, analysis_method):
        """
        TODO: This method belongs to androguard

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        """
        # FIXME: this should be fixed in androguard, so that we combine MethodAnalysis and MethodClassAnalysis
        mca = self.dx.get_method_analysis(analysis_method.get_method())

        # If something is here, this is clearly a PACKAGE_CALL.
        for _, em, off in mca.get_xref_to():
            yield off, em, TAINTED_PACKAGE_CALL

        # In order to get the PACKAGE_CREATE, we need to check the ClassAnalysis objects...
        # It stores the source, if and only if the xrefs is a create.
        for ca in self.dx.get_classes():
            for called_class, values in ca.get_xref_to().items():
                for ref, meth, off in values:
                    if ref == 0x22:  # FIXME: Use the same as TAINTED did for now, might add 0x1c later
                        if meth == analysis_method.get_method():
                            yield off, meth, TAINTED_PACKAGE_CREATE

    def _get_strings_a1(self, analysis_method):
        """
        Returns one long string with all used strings in the method,
        where all newlines are replaced by whitespaces.

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :rtype: str
        """
        return ''.join([str(k).replace('\n', ' ') for _, k in self._get_all_strings_by_method(analysis_method)])

    def _get_strings_pa(self, analysis_method):
        """
        Returns a list of tuples with the offset of the string usage and S plus the length of the string as second entry.

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :rtype: List[(int, str)]
        """
        return [(k, 'S{}'.format(len(v))) for k, v in self._get_all_strings_by_method(analysis_method)]

    def _get_strings_a(self, analysis_method):
        """
        Returns a list of tuples with the offsets of the string usage and 'S' as the second entry.

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :rtype: List[(int, str)]
        """
        key = "SA-%s" % self._get_method_info(analysis_method)
        if key not in self._global_cached:
            self._global_cached[key] = [(k, 'S') for k, _ in self._get_all_strings_by_method(analysis_method)]

        return self._global_cached[key]

    def _get_fields_a(self, analysis_method):
        """
        Returns a list of tuples with field accesses inside the method.
        The first item is the offset in the method, the second the accesstype.
        0 is for read and 1 for write access to the fields.

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :rtype: List[(int, str)]
        """
        key = "FA-%s" % self._get_method_info(analysis_method)
        if key not in self._global_cached:
            self._global_cached[key] = [(k, 'F{}'.format(v)) for k, v in self._get_all_fields_by_method(analysis_method)]

        return self._global_cached[key]

    def _get_packages_a(self, analysis_method):
        """
        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        """
        return [(offset, 'P{}'.format(access)) for offset, meth, access in self._get_packages_by_method(analysis_method)]

    def _get_packages(self, analysis_method, include_packages):
        """
        returns just the package access flags, otherwise same as :meth:`_get_packages_pa_1`.

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :param List[str] include_packages:
        :rtype: str
        """
        return ''.join(map(itemgetter(1), self._get_packages_pa_1(analysis_method, include_packages)))

    def _get_packages_pa_1(self, analysis_method, include_packages):
        """
        Returns a list of tuples in the form (offset, str).
        The offset gives the bytecode offset where the method is used and the str
        has the form Px{name}.
        Px is the package access.
        
        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :param List[str] include_packages:
        :rtype: List[int, str]
        """
        key = "PA1-%s-%s" % (self._get_method_info(analysis_method), include_packages)
        if key not in self._global_cached:
            l = []

            for offset, meth, access in self._get_packages_by_method(analysis_method):
                cls_name = meth.class_name
                # Check if parts if the classname are in the list of to include packages
                present = any(map(lambda x, c=cls_name: x in c, include_packages))

                # Here we check what kind of call it is...
                # 1 => call
                # 0 => create
                # the special call 2 is used to define that this is not an API but an internal package
                # but the access flag itself is always 0 or 1
                if access == 1:
                    # This is used of the package is called
                    if isinstance(meth, dvm.EncodedMethod):
                        # If not external, then the call is 2.
                        # In that sense, we are only monitoring calls to APIs here!
                        # If the call is internal, we never print the name.
                        l.append((offset, "P{}".format(2)))
                    else:
                        if present:
                            l.append((offset, "P{}{{{}{}{}}}".format(access, cls_name, meth.name, meth.get_descriptor())))
                        else:
                            l.append((offset, "P{}".format(access)))
                else:
                    # This is called if the package is created
                    if present:
                        l.append((offset, "P{}{{{}}}".format(access, cls_name)))
                    else:
                        l.append((offset, "P{}".format(access)))

            self._global_cached[key] = l
        return self._global_cached[key]

    def _get_packages_pa_2(self, analysis_method, include_packages):
        """
        Returns a list of tuples in the form (offset, str).
        The offset gives the bytecode offset where the method is used and the str
        has the form Px{name}.
        Px is the package access.
        
        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :param List[str] include_packages:
        :rtype: List[int, str]
        """
        l = []
        for offset, meth, access in self._get_packages_by_method(analysis_method):
            cls_name = meth.class_name
            # Check if parts if the classname are in the list of to include packages
            present = any(map(lambda x, c=cls_name: x in c, include_packages))

            if present:
                l.append((offset, "P{}".format(access)))
                continue

            if access == 1:
                l.append((offset, "P{}{{{}{}{}}}".format(access, cls_name, meth.name, meth.get_descriptor())))
            else:
                l.append((offset, "P{}{{{}}}".format(access, cls_name)))

        return l

    def get_method(self, analysis_method, signature_type, signature_arguments={}) -> Sign:
        """
        Returns the Sign object for the given Method.

        The signature type is a string of the different signature methods which shall be used.
        Multiple signature methods can be used by separating them with a colon (:).

        :param androguard.core.analysis.analysis.MethodAnalysis analysis_method:
        :param str signature_type:
        :param dict signature_arguments:
        :rtype: Sign
        """
        key = "%s-%s-%s" % (self._get_method_info(analysis_method), signature_type, signature_arguments)

        if key in self._cached_signatures:
            return self._cached_signatures[key]

        s = Sign()

        #print signature_type, signature_arguments
        for i in signature_type.split(":"):
            #    print i, signature_arguments[ i ]
            if i == "L0":
                _type = self.levels[i][signature_arguments[i]["type"]]
                try:
                    _arguments = signature_arguments[i]["arguments"]
                except KeyError:
                    _arguments = []

                value = self._get_bb(analysis_method, _type, _arguments)
                s.add(i, ''.join(z for z in value))

            elif i == "L4":
                try:
                    _arguments = signature_arguments[i]["arguments"]
                except KeyError:
                    _arguments = []

                value = self._get_packages(analysis_method, _arguments)
                s.add(i, value)

            elif i == "hex":
                value = self._get_hex(analysis_method)
                s.add(i, value)

            elif i == "sequencebb":
                value = self._get_sequence_bb(analysis_method)
                s.add(i, value)

            else:
                value = ''
                for func_name in self.levels[i]:
                    # FIXME: why this complicated? You can store function pointers! But it looks like this is much more complicated, see code above...
                    value += getattr(self, func_name)(analysis_method)
                s.add(i, value)

        self._cached_signatures[key] = s
        return s
