# Python GEDCOM Parser
#
# Copyright (C) 2018 Damon Brodie (damon.brodie at gmail.com)
# Copyright (C) 2018 Nicklas Reincke (contact at reynke.com)
# Copyright (C) 2016 Andreas Oberritter
# Copyright (C) 2012 Madeleine Price Ball
# Copyright (C) 2005 Daniel Zappala (zappala at cs.byu.edu)
# Copyright (C) 2005 Brigham Young University
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Further information about the license: http://www.gnu.org/licenses/gpl-2.0.html

import re as regex
from sys import version_info

__all__ = ["Gedcom", "Element", "GedcomParseError"]

# Relationship to a mother.
GEDCOM_PROGRAM_DEFINED_TAG_MREL = "_MREL"

# Relationship to a father.
GEDCOM_PROGRAM_DEFINED_TAG_FREL = "_FREL"

# The event of entering into life.
GEDCOM_TAG_BIRTH = "BIRT"

# The event of the proper disposing of the mortal remains of a deceased person.
GEDCOM_TAG_BURIAL = "BURI"

# The event of the periodic count of the population for a designated locality, such as a national or state Census.
GEDCOM_TAG_CENSUS = "CENS"

# Indicates a change, correction, or modification. Typically used in connection
# with a DATE to specify when a change in information occurred.
GEDCOM_TAG_CHANGE = "CHAN"

# The natural, adopted, or sealed (LDS) child of a father and a mother.
GEDCOM_TAG_CHILD = "CHIL"

# An indicator that additional data belongs to the superior value. The information from the CONC value is to be
# connected to the value of the superior preceding line without a space and without a carriage return and/or
# new line character. Values that are split for a CONC tag must always be split at a non-space. If the value is
# split on a space the space will be lost when concatenation takes place. This is because of the treatment that
# spaces get as a GEDCOM delimiter, many GEDCOM values are trimmed of trailing spaces and some systems look for
# the first non-space starting after the tag to determine the beginning of the value.
GEDCOM_TAG_CONCATENATION = "CONC"

# An indicator that additional data belongs to the superior value. The information from the CONT value is to be
# connected to the value of the superior preceding line with a carriage return and/or new line character.
# Leading spaces could be important to the formatting of the resultant text. When importing values from CONT lines
# the reader should assume only one delimiter character following the CONT tag. Assume that the rest of the leading
# spaces are to be a part of the value.
GEDCOM_TAG_CONTINUED = "CONT"

# The time of an event in a calendar format.
GEDCOM_TAG_DATE = "DATE"

# The event when mortal life terminates.
GEDCOM_TAG_DEATH = "DEAT"

# Identifies a legal, common law, or other customary relationship of man and woman and their children,
# if any, or a family created by virtue of the birth of a child to its biological father and mother.
GEDCOM_TAG_FAMILY = "FAM"

# Identifies the family in which an individual appears as a child.
GEDCOM_TAG_FAMILY_CHILD = "FAMC"

# Identifies the family in which an individual appears as a spouse.
GEDCOM_TAG_FAMILY_SPOUSE = "FAMS"

# An information storage place that is ordered and arranged for preservation and reference.
GEDCOM_TAG_FILE = "FILE"

# A given or earned name used for official identification of a person.
GEDCOM_TAG_GIVEN_NAME = "GIVN"

# An individual in the family role of a married man or father.
GEDCOM_TAG_HUSBAND = "HUSB"

# A person.
GEDCOM_TAG_INDIVIDUAL = "INDI"

# A legal, common-law, or customary event of creating a family unit of a man and a woman as husband and wife.
GEDCOM_TAG_MARRIAGE = "MARR"

# A word or combination of words used to help identify an individual, title, or other item.
# More than one NAME line should be used for people who were known by multiple names.
GEDCOM_TAG_NAME = "NAME"

# Pertaining to a grouping of attributes used in describing something. Usually referring to the data required
# to represent a multimedia object, such an audio recording, a photograph of a person, or an image of a document.
GEDCOM_TAG_OBJECT = "OBJE"

# The type of work or profession of an individual.
GEDCOM_TAG_OCCUPATION = "OCCU"

# A jurisdictional name to identify the place or location of an event.
GEDCOM_TAG_PLACE = "PLAC"

# Flag for private address or event.
GEDCOM_TAG_PRIVATE = "PRIV"

# Indicates the sex of an individual--male or female.
GEDCOM_TAG_SEX = "SEX"

# The initial or original material from which information was obtained.
GEDCOM_TAG_SOURCE = "SOUR"

# A family name passed on or used by members of a family.
GEDCOM_TAG_SURNAME = "SURN"

# An individual in the role as a mother and/or married woman.
GEDCOM_TAG_WIFE = "WIFE"


class Gedcom:
    """Parses and manipulates GEDCOM 5.5 format data

    For documentation of the GEDCOM 5.5 format, see:
    http://homepages.rootsweb.ancestry.com/~pmcbride/gedcom/55gctoc.htm

    This parser reads and parses a GEDCOM file.
    Elements may be accessed via:
      - a list (all elements, default order is same as in file)
      - a dict (only elements with pointers, which are the keys)
    """

    def __init__(self, file_path, use_strict=True):
        """Initialize a GEDCOM data object. You must supply a GEDCOM file
        :type file_path: str
        """
        self.__element_list = []
        self.__element_dictionary = {}
        self.invalidate_cache()
        self.__root_element = Element(-1, "", "ROOT", "")
        self.__parse(file_path, use_strict)
        self.__use_strict = use_strict

    def invalidate_cache(self):
        """Cause get_element_list() and get_element_dictionary() to return updated data

        The update gets deferred until each of the methods actually gets called.
        """
        self.__element_list = []
        self.__element_dictionary = {}

    def get_element_list(self):
        """Return a list of all the elements in the GEDCOM file

        By default elements are in the same order as they appeared in the file.

        This list gets generated on-the-fly, but gets cached. If the database
        was modified, you should call invalidate_cache() once to let this
        method return updated data.

        Consider using `get_root_element()` or `get_root_child_elements()` to access
        the hierarchical GEDCOM tree, unless you rarely modify the database.

        :rtype: list of Element
        """
        if not self.__element_list:
            for element in self.get_root_child_elements():
                self.__build_list(element, self.__element_list)
        return self.__element_list

    def get_element_dictionary(self):
        """Return a dictionary of elements from the GEDCOM file

        Only elements identified by a pointer are listed in the dictionary.
        The keys for the dictionary are the pointers.

        This dictionary gets generated on-the-fly, but gets cached. If the
        database was modified, you should call invalidate_cache() once to let
        this method return updated data.

        :rtype: dict of Element
        """
        if not self.__element_dictionary:
            self.__element_dictionary = {
                element.get_pointer(): element for element in self.get_root_child_elements() if element.get_pointer()
            }

        return self.__element_dictionary

    def get_root_element(self):
        """Returns a virtual root element containing all logical records as children

        When printed, this element converts to an empty string.

        :rtype: Element
        """
        return self.__root_element

    def get_root_child_elements(self):
        """Return a list of logical records in the GEDCOM file

        By default, elements are in the same order as they appeared in the file.

        :rtype: list of Element
        """
        return self.get_root_element().get_child_elements()

    # Private methods

    def __parse(self, file_path, use_strict=True):
        """Open and parse file path as GEDCOM 5.5 formatted data
        :type file_path: str
        """
        gedcom_file = open(file_path, 'rb')
        line_number = 1
        last_element = self.__root_element
        for line in gedcom_file:
            last_element = self.__parse_line(line_number, line.decode('utf-8-sig'), last_element, use_strict)
            line_number += 1

    @staticmethod
    def __parse_line(line_number, line, last_element, use_strict=True):
        """Parse a line from a GEDCOM 5.5 formatted document

        Each line should have the following (bracketed items optional):
        level + ' ' + [pointer + ' ' +] tag + [' ' + line_value]

        :type line_number: int
        :type line: str
        :type last_element: Element
        :rtype: Element
        """

        # Level must start with non-negative int, no leading zeros.
        level_regex = '^(0|[1-9]+[0-9]*) '

        # Pointer optional, if it exists it must be flanked by `@`
        pointer_regex = '(@[^@]+@ |)'

        # Tag must be alphanumeric string
        tag_regex = '([A-Za-z0-9_]+)'

        # Value optional, consists of anything after a space to end of line
        value_regex = '( [^\n\r]*|)'

        # End of line defined by `\n` or `\r`
        end_of_line_regex = '([\r\n]{1,2})'

        # Complete regex
        gedcom_line_regex = level_regex + pointer_regex + tag_regex + value_regex + end_of_line_regex
        regex_match = regex.match(gedcom_line_regex, line)

        if regex_match is None:
            if use_strict:
                error_message = ("Line %d of document violates GEDCOM format 5.5" % line_number
                                 + "\nSee: https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf")
                raise SyntaxError(error_message)
            else:
                # Quirk check - see if this is a line without a CRLF (which could be the last line)
                last_line_regex = level_regex + pointer_regex + tag_regex + value_regex
                regex_match = regex.match(last_line_regex, line)
                if regex_match is not None:
                    line_parts = regex_match.groups()

                    level = int(line_parts[0])
                    pointer = line_parts[1].rstrip(' ')
                    tag = line_parts[2]
                    value = line_parts[3][1:]
                    crlf = '\n'
                else:
                    # Quirk check - Sometimes a gedcom has a text field with a CR.
                    # This creates a line without the standard level and pointer.
                    # If this is detected then turn it into a CONC or CONT.
                    line_regex = '([^\n\r]*|)'
                    cont_line_regex = line_regex + end_of_line_regex
                    regex_match = regex.match(cont_line_regex, line)
                    line_parts = regex_match.groups()
                    level = last_element.get_level()
                    tag = last_element.get_tag()
                    pointer = None
                    value = line_parts[0][1:]
                    crlf = line_parts[1]
                    if tag != GEDCOM_TAG_CONTINUED and tag != GEDCOM_TAG_CONCATENATION:
                        # Increment level and change this line to a CONC
                        level += 1
                        tag = GEDCOM_TAG_CONCATENATION
        else:
            line_parts = regex_match.groups()

            level = int(line_parts[0])
            pointer = line_parts[1].rstrip(' ')
            tag = line_parts[2]
            value = line_parts[3][1:]
            crlf = line_parts[4]

        # Check level: should never be more than one higher than previous line.
        if level > last_element.get_level() + 1:
            error_message = ("Line %d of document violates GEDCOM format 5.5" % line_number
                             + "\nLines must be no more than one level higher than previous line."
                             + "\nSee: https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf")
            raise SyntaxError(error_message)

        # Create element. Store in list and dict, create children and parents.
        element = Element(level, pointer, tag, value, crlf, multi_line=False)

        # Start with last element as parent, back up if necessary.
        parent_element = last_element

        while parent_element.get_level() > level - 1:
            parent_element = parent_element.get_parent_element()

        # Add child to parent & parent to child.
        parent_element.add_child_element(element)

        return element

    def __build_list(self, element, element_list):
        """Recursively add elements to a list containing elements
        :type element: Element
        :type element_list: list of Element
        """
        element_list.append(element)
        for child in element.get_child_elements():
            self.__build_list(child, element_list)

    # Methods for analyzing individuals and relationships between individuals

    def get_marriages(self, individual):
        """Return list of marriage tuples (date, place) for an individual
        :type individual: Element
        :rtype: tuple
        """
        marriages = []
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag" % GEDCOM_TAG_INDIVIDUAL)
        # Get and analyze families where individual is spouse.
        families = self.get_families(individual, GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            for family_data in family.get_child_elements():
                if family_data.get_tag() == GEDCOM_TAG_MARRIAGE:
                    date = ''
                    place = ''
                    for marriage_data in family_data.get_child_elements():
                        if marriage_data.get_tag() == GEDCOM_TAG_DATE:
                            date = marriage_data.get_value()
                        if marriage_data.get_tag() == GEDCOM_TAG_PLACE:
                            place = marriage_data.get_value()
                    marriages.append((date, place))
        return marriages

    def get_marriage_years(self, individual):
        """Return list of marriage years (as int) for an individual
        :type individual: Element
        :rtype: list of int
        """
        dates = []
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag" % GEDCOM_TAG_INDIVIDUAL)
        # Get and analyze families where individual is spouse.
        families = self.get_families(individual, GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            for child in family.get_child_elements():
                if child.get_tag() == GEDCOM_TAG_MARRIAGE:
                    for childOfChild in child.get_child_elements():
                        if childOfChild.get_tag() == GEDCOM_TAG_DATE:
                            date = childOfChild.get_value().split()[-1]
                            try:
                                dates.append(int(date))
                            except ValueError:
                                pass
        return dates

    def marriage_year_match(self, individual, year):
        """Check if one of the marriage years of an individual matches the supplied year. Year is an integer.
        :type individual: Element
        :type year: int
        :rtype: bool
        """
        years = self.get_marriage_years(individual)
        return year in years

    def marriage_range_match(self, individual, from_year, to_year):
        """Check if one of the marriage years of an individual is in a given range. Years are integers.
        :type individual: Element
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        years = self.get_marriage_years(individual)
        for year in years:
            if from_year <= year <= to_year:
                return True
        return False

    def get_families(self, individual, family_type=GEDCOM_TAG_FAMILY_SPOUSE):
        """Return family elements listed for an individual

        family_type can be `GEDCOM_TAG_FAMILY_SPOUSE` (families where the individual is a spouse) or
        `GEDCOM_TAG_FAMILY_CHILD` (families where the individual is a child). If a value is not
        provided, `GEDCOM_TAG_FAMILY_SPOUSE` is default value.

        :type individual: Element
        :type family_type: str
        :rtype: list of Element
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag." % GEDCOM_TAG_INDIVIDUAL)
        families = []
        element_dictionary = self.get_element_dictionary()
        for child_element in individual.get_child_elements():
            is_family = (child_element.get_tag() == family_type
                         and child_element.get_value() in element_dictionary
                         and element_dictionary[child_element.get_value()].is_family())
            if is_family:
                families.append(element_dictionary[child_element.get_value()])
        return families

    def get_ancestors(self, individual, ancestor_type="ALL"):
        """Return elements corresponding to ancestors of an individual

        Optional `ancestor_type`. Default "ALL" returns all ancestors, "NAT" can be
        used to specify only natural (genetic) ancestors.

        :type individual: Element
        :type ancestor_type: str
        :rtype: list of Element
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag." % GEDCOM_TAG_INDIVIDUAL)
        parents = self.get_parents(individual, ancestor_type)
        ancestors = []
        ancestors.extend(parents)
        for parent in parents:
            ancestors.extend(self.get_ancestors(parent))
        return ancestors

    def get_parents(self, individual, parent_type="ALL"):
        """Return elements corresponding to parents of an individual

        Optional parent_type. Default "ALL" returns all parents. "NAT" can be
        used to specify only natural (genetic) parents.

        :type individual: Element
        :type parent_type: str
        :rtype: list of Element
        """
        if not individual.is_individual():
            raise ValueError("Operation only valid for elements with %s tag." % GEDCOM_TAG_INDIVIDUAL)
        parents = []
        families = self.get_families(individual, GEDCOM_TAG_FAMILY_CHILD)
        for family in families:
            if parent_type == "NAT":
                for family_member in family.get_child_elements():
                    if family_member.get_tag() == GEDCOM_TAG_CHILD and family_member.get_value() == individual.get_pointer():
                        for child in family_member.get_child_elements():
                            if child.get_value() == "Natural":
                                if child.get_tag() == GEDCOM_PROGRAM_DEFINED_TAG_MREL:
                                    parents += self.get_family_members(family, GEDCOM_TAG_WIFE)
                                elif child.get_tag() == GEDCOM_PROGRAM_DEFINED_TAG_FREL:
                                    parents += self.get_family_members(family, GEDCOM_TAG_HUSBAND)
            else:
                parents += self.get_family_members(family, "PARENTS")
        return parents

    def find_path_to_ancestor(self, descendant, ancestor, path=None):
        """Return path from descendant to ancestor
        :rtype: object
        """
        if not descendant.is_individual() and ancestor.is_individual():
            raise ValueError("Operation only valid for elements with %s tag." % GEDCOM_TAG_INDIVIDUAL)
        if not path:
            path = [descendant]
        if path[-1].get_pointer() == ancestor.get_pointer():
            return path
        else:
            parents = self.get_parents(descendant, "NAT")
            for parent in parents:
                potential_path = self.find_path_to_ancestor(parent, ancestor, path + [parent])
                if potential_path is not None:
                    return potential_path
        return None

    def get_family_members(self, family, members_type="ALL"):
        """Return array of family members: individual, spouse, and children

        Optional argument `members_type` can be used to return specific subsets.
        "ALL": Default, return all members of the family
        "PARENTS": Return individuals with "HUSB" and "WIFE" tags (parents)
        "HUSB": Return individuals with "HUSB" tags (father)
        "WIFE": Return individuals with "WIFE" tags (mother)
        "CHIL": Return individuals with "CHIL" tags (children)

        :type family: Element
        :type members_type: str
        :rtype: list of Element
        """
        if not family.is_family():
            raise ValueError("Operation only valid for element with %s tag." % GEDCOM_TAG_FAMILY)
        family_members = []
        element_dictionary = self.get_element_dictionary()
        for child_element in family.get_child_elements():
            # Default is ALL
            is_family = (child_element.get_tag() == GEDCOM_TAG_HUSBAND
                         or child_element.get_tag() == GEDCOM_TAG_WIFE
                         or child_element.get_tag() == GEDCOM_TAG_CHILD)
            if members_type == "PARENTS":
                is_family = (child_element.get_tag() == GEDCOM_TAG_HUSBAND
                             or child_element.get_tag() == GEDCOM_TAG_WIFE)
            elif members_type == "HUSB":
                is_family = child_element.get_tag() == GEDCOM_TAG_HUSBAND
            elif members_type == "WIFE":
                is_family = child_element.get_tag() == GEDCOM_TAG_WIFE
            elif members_type == "CHIL":
                is_family = child_element.get_tag() == GEDCOM_TAG_CHILD
            if is_family and child_element.get_value() in element_dictionary:
                family_members.append(element_dictionary[child_element.get_value()])
        return family_members

    # Other methods

    def print_gedcom(self):
        """Write GEDCOM data to stdout"""
        from sys import stdout
        self.save_gedcom(stdout)

    def save_gedcom(self, open_file):
        """Save GEDCOM data to a file
        :type open_file: file
        """
        if version_info[0] >= 3:
            open_file.write(self.get_root_element().get_individual())
        else:
            open_file.write(self.get_root_element().get_individual().encode('utf-8'))


class GedcomParseError(Exception):
    """Exception raised when a GEDCOM parsing error occurs"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Element:
    """GEDCOM element

    Each line in a GEDCOM file is an element with the format

    level [pointer] tag [value]

    where level and tag are required, and pointer and value are
    optional.  Elements are arranged hierarchically according to their
    level, and elements with a level of zero are at the top level.
    Elements with a level greater than zero are children of their
    parent.

    A pointer has the format @pname@, where pname is any sequence of
    characters and numbers.  The pointer identifies the object being
    pointed to, so that any pointer included as the value of any
    element points back to the original object.  For example, an
    element may have a FAMS tag whose value is @F1@, meaning that this
    element points to the family record in which the associated person
    is a spouse.  Likewise, an element with a tag of FAMC has a value
    that points to a family record in which the associated person is a
    child.

    See a GEDCOM file for examples of tags and their values.
    """

    def __init__(self, level, pointer, tag, value, crlf="\n", multi_line=True):
        """Initialize an element

        You must include a level, a pointer, a tag, and a value.
        Normally initialized by the GEDCOM parser, not by a user.

        :type level: int
        :type pointer: str
        :type tag: str
        :type value: str
        :type crlf: str
        :type multi_line: bool
        """

        # basic element info
        self.__level = level
        self.__pointer = pointer
        self.__tag = tag
        self.__value = value
        self.__crlf = crlf

        # structuring
        self.__children = []
        self.__parent = None

        if multi_line:
            self.set_multi_line_value(value)

    def get_level(self):
        """Return the level of this element
        :rtype: int
        """
        return self.__level

    def get_pointer(self):
        """Return the pointer of this element
        :rtype: str
        """
        return self.__pointer

    def get_tag(self):
        """Return the tag of this element
        :rtype: str
        """
        return self.__tag

    def get_value(self):
        """Return the value of this element
        :rtype: str
        """
        return self.__value

    def set_value(self, value):
        """Set the value of this element
        :type value: str
        """
        self.__value = value

    def get_multi_line_value(self):
        """Return the value of this element including continuations
        :rtype: str
        """
        result = self.get_value()
        last_crlf = self.__crlf
        for element in self.get_child_elements():
            tag = element.get_tag()
            if tag == GEDCOM_TAG_CONCATENATION:
                result += element.get_value()
                last_crlf = element.__crlf
            elif tag == GEDCOM_TAG_CONTINUED:
                result += last_crlf + element.get_value()
                last_crlf = element.__crlf
        return result

    def __available_characters(self):
        """Get the number of available characters of the elements original string
        :rtype: int
        """
        element_characters = len(self.__unicode__())
        return 0 if element_characters > 255 else 255 - element_characters

    def __line_length(self, line):
        """@TODO Write docs.
        :type line: str
        :rtype: int
        """
        total_characters = len(line)
        available_characters = self.__available_characters()
        if total_characters <= available_characters:
            return total_characters
        spaces = 0
        while spaces < available_characters and line[available_characters - spaces - 1] == ' ':
            spaces += 1
        if spaces == available_characters:
            return available_characters
        return available_characters - spaces

    def __set_bounded_value(self, value):
        """@TODO Write docs.
        :type value: str
        :rtype: int
        """
        line_length = self.__line_length(value)
        self.set_value(value[:line_length])
        return line_length

    def __add_bounded_child(self, tag, value):
        """@TODO Write docs.
        :type tag: str
        :type value: str
        :rtype: int
        """
        child = self.new_child_element(tag)
        return child.__set_bounded_value(value)

    def __add_concatenation(self, string):
        """@TODO Write docs.
        :rtype: str
        """
        index = 0
        size = len(string)
        while index < size:
            index += self.__add_bounded_child(GEDCOM_TAG_CONCATENATION, string[index:])

    def set_multi_line_value(self, value):
        """Set the value of this element, adding continuation lines as necessary
        :type value: str
        """
        self.set_value('')
        self.get_child_elements()[:] = [child for child in self.get_child_elements() if
                                        child.get_tag() not in (GEDCOM_TAG_CONCATENATION, GEDCOM_TAG_CONTINUED)]

        lines = value.splitlines()
        if lines:
            line = lines.pop(0)
            n = self.__set_bounded_value(line)
            self.__add_concatenation(line[n:])

            for line in lines:
                n = self.__add_bounded_child(GEDCOM_TAG_CONTINUED, line)
                self.__add_concatenation(line[n:])

    def get_child_elements(self):
        """Return the child elements of this element
        :rtype: list of Element
        """
        return self.__children

    def get_parent_element(self):
        """Return the parent element of this element
        :rtype: Element
        """
        return self.__parent

    def new_child_element(self, tag, pointer="", value=""):
        """Create and return a new child element of this element

        :type tag: str
        :type pointer: str
        :type value: str
        :rtype: Element
        """
        child_element = Element(self.get_level() + 1, pointer, tag, value, self.__crlf)
        self.add_child_element(child_element)
        return child_element

    def add_child_element(self, element):
        """Add a child element to this element

        :type element: Element
        """
        self.get_child_elements().append(element)
        element.set_parent_element(self)

    def set_parent_element(self, element):
        """Add a parent element to this element

        There's usually no need to call this method manually,
        add_child_element() calls it automatically.

        :type element: Element
        """
        self.__parent = element

    def is_individual(self):
        """Check if this element is an individual
        :rtype: bool
        """
        return self.get_tag() == GEDCOM_TAG_INDIVIDUAL

    def is_child(self):
        """Check if this element is a child
        :rtype: bool
        """
        if not self.is_individual():
            raise ValueError("Operation only valid for elements with %s tag" % GEDCOM_TAG_INDIVIDUAL)
        found_child = False
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_FAMILY_CHILD:
                found_child = True
        return found_child

    def is_family(self):
        """Check if this element is a family
        :rtype: bool
        """
        return self.get_tag() == GEDCOM_TAG_FAMILY

    def is_file(self):
        """Check if this element is a file
        :rtype: bool
        """
        return self.get_tag() == GEDCOM_TAG_FILE

    def is_object(self):
        """Check if this element is an object
        :rtype: bool
        """
        return self.get_tag() == GEDCOM_TAG_OBJECT

    # criteria matching

    def criteria_match(self, criteria):
        """Check in this element matches all of the given criteria

        `criteria` is a colon-separated list, where each item in the
        list has the form [name]=[value]. The following criteria are supported:

        surname=[name]
             Match a person with [name] in any part of the surname.
        name=[name]
             Match a person with [name] in any part of the given name.
        birth=[year]
             Match a person whose birth year is a four-digit [year].
        birth_range=[from_year-to_year]
             Match a person whose birth year is in the range of years from
             [from_year] to [to_year], including both [from_year] and [to_year].
        death=[year]
        death_range=[from_year-to_year]

        :type criteria: str
        :rtype: bool
        """

        # Check if criteria is a valid criteria
        try:
            for criterion in criteria.split(':'):
                criterion.split('=')
        except ValueError:
            return False

        match = True

        for criterion in criteria.split(':'):
            key, value = criterion.split('=')
            if key == "surname" and not self.surname_match(value):
                match = False
            elif key == "name" and not self.given_match(value):
                match = False
            elif key == "birth":
                try:
                    year = int(value)
                    if not self.birth_year_match(year):
                        match = False
                except ValueError:
                    match = False
            elif key == "birth_range":
                try:
                    from_year, to_year = value.split('-')
                    from_year = int(from_year)
                    to_year = int(to_year)
                    if not self.birth_range_match(from_year, to_year):
                        match = False
                except ValueError:
                    match = False
            elif key == "death":
                try:
                    year = int(value)
                    if not self.death_year_match(year):
                        match = False
                except ValueError:
                    match = False
            elif key == "death_range":
                try:
                    from_year, to_year = value.split('-')
                    from_year = int(from_year)
                    to_year = int(to_year)
                    if not self.death_range_match(from_year, to_year):
                        match = False
                except ValueError:
                    match = False

        return match

    def surname_match(self, name):
        """Match a string with the surname of an individual
        :type name: str
        :rtype: bool
        """
        (first, last) = self.get_name()
        return regex.search(name, last, regex.IGNORECASE)

    def given_match(self, name):
        """Match a string with the given names of an individual
        :type name: str
        :rtype: bool
        """
        (first, last) = self.get_name()
        return regex.search(name, first, regex.IGNORECASE)

    def birth_year_match(self, year):
        """Match the birth year of an individual
        :type year: int
        :rtype: bool
        """
        return self.get_birth_year() == year

    def birth_range_match(self, from_year, to_year):
        """Check if the birth year of an individual is in a given range
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        birth_year = self.get_birth_year()
        if from_year <= birth_year <= to_year:
            return True
        return False

    def death_year_match(self, year):
        """Match the death year of an individual.
        :type year: int
        :rtype: bool
        """
        return self.get_death_year() == year

    def death_range_match(self, from_year, to_year):
        """Check if the death year of an individual is in a given range. Years are integers
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        death_year = self.get_death_year()
        if from_year <= death_year <= to_year:
            return True
        return False

    def get_name(self):
        """Return a person's names as a tuple: (first, last)
        :rtype: tuple
        """
        first = ""
        last = ""
        if not self.is_individual():
            return first, last

        # Return the first GEDCOM_TAG_NAME that is found.  Alternatively
        # as soon as we have both the GEDCOM_TAG_GIVEN_NAME and _SURNAME return those
        found_given_name = False
        found_surname_name = False
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_NAME:
                # some GEDCOM files don't use child tags but instead
                # place the name in the value of the NAME tag
                if child.get_value() != "":
                    name = child.get_value().split('/')
                    if len(name) > 0:
                        first = name[0].strip()
                        if len(name) > 1:
                            last = name[1].strip()
                    return first, last
                else:
                    for childOfChild in child.get_child_elements():
                        if childOfChild.get_tag() == GEDCOM_TAG_GIVEN_NAME:
                            first = childOfChild.get_value()
                            found_given_name = True
                        if childOfChild.get_tag() == GEDCOM_TAG_SURNAME:
                            last = childOfChild.get_value()
                            found_surname_name = True
                    if found_given_name and found_surname_name:
                        return first, last

        # If we reach here we are probably returning empty strings
        return first, last

    def get_gender(self):
        """Return the gender of a person in string format
        :rtype: str
        """
        gender = ""
        if not self.is_individual():
            return gender
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_SEX:
                gender = child.get_value()
        return gender

    def is_private(self):
        """Return if the person is marked private in boolean format
        :rtype: bool
        """
        private = False
        if not self.is_individual():
            return private
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_PRIVATE:
                private = child.get_value()
                if private == 'Y':
                    private = True
        return private

    def get_birth_data(self):
        """Return the birth tuple of a person as (date, place, sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []
        if not self.is_individual():
            return date, place, sources
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_BIRTH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())
        return date, place, sources

    def get_birth_year(self):
        """Return the birth year of a person in integer format
        :rtype: int
        """
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_BIRTH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == GEDCOM_TAG_DATE:
                        date_split = childOfChild.get_value().split()
                        date = date_split[len(date_split) - 1]
        if date == "":
            return -1
        try:
            return int(date)
        except ValueError:
            return -1

    def get_death_data(self):
        """Return the death tuple of a person as (date, place, sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []
        if not self.is_individual():
            return date, place
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_DEATH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())
        return date, place, sources

    def get_death_year(self):
        """Return the death year of a person in integer format
        :rtype: int
        """
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_DEATH:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == GEDCOM_TAG_DATE:
                        date_split = childOfChild.get_value().split()
                        date = date_split[len(date_split) - 1]
        if date == "":
            return -1
        try:
            return int(date)
        except ValueError:
            return -1

    def get_burial(self):
        """Return the burial tuple of a person as (date, place, sources)
        :rtype: tuple
        """
        date = ""
        place = ""
        sources = []
        if not self.is_individual():
            return date, place
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_BURIAL:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())
        return date, place, sources

    def get_census(self):
        """Return list of census tuples (date, place, sources) for an individual
        :rtype: tuple
        """
        census = []
        if not self.is_individual():
            raise ValueError("Operation only valid for elements with %s tag" % GEDCOM_TAG_INDIVIDUAL)
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_CENSUS:
                date = ''
                place = ''
                sources = []
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
                    if childOfChild.get_tag() == GEDCOM_TAG_PLACE:
                        place = childOfChild.get_value()
                    if childOfChild.get_tag() == GEDCOM_TAG_SOURCE:
                        sources.append(childOfChild.get_value())
                census.append((date, place, sources))
        return census

    def get_last_change_date(self):
        """Return the last updated date of a person as (date)
        :rtype: str
        """
        date = ""
        if not self.is_individual():
            return date
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_CHANGE:
                for childOfChild in child.get_child_elements():
                    if childOfChild.get_tag() == GEDCOM_TAG_DATE:
                        date = childOfChild.get_value()
        return date

    def get_occupation(self):
        """Return the occupation of a person as (date)
        :rtype: str
        """
        occupation = ""
        if not self.is_individual():
            return occupation
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_OCCUPATION:
                occupation = child.get_value()
        return occupation

    def is_deceased(self):
        """Check if a person is deceased
        :rtype: bool
        """
        if not self.is_individual():
            return False
        for child in self.get_child_elements():
            if child.get_tag() == GEDCOM_TAG_DEATH:
                return True
        return False

    def get_individual(self):
        """Return this element and all of its sub-elements
        :rtype: str
        """
        result = self.__unicode__()
        for child_element in self.get_child_elements():
            result += child_element.get_individual()
        return result

    def __str__(self):
        """:rtype: str"""
        if version_info[0] >= 3:
            return self.__unicode__()
        else:
            return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        """Format this element as its original string
        :rtype: str
        """
        if self.get_level() < 0:
            return ''
        result = str(self.get_level())
        if self.get_pointer() != "":
            result += ' ' + self.get_pointer()
        result += ' ' + self.get_tag()
        if self.get_value() != "":
            result += ' ' + self.get_value()
        result += self.__crlf
        return result
