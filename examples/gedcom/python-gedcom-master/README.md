# Python GEDCOM Parser

[![PyPI](https://img.shields.io/pypi/v/python-gedcom.svg)](https://pypi.org/project/python-gedcom/)
[![GitHub release](https://img.shields.io/github/release/nickreynke/python-gedcom.svg)](https://github.com/nickreynke/python-gedcom/releases)
[![Build Status](https://travis-ci.org/nickreynke/python-gedcom.svg?branch=master)](https://travis-ci.org/nickreynke/python-gedcom)
![](https://img.shields.io/badge/GEDCOM%20format%20version-5.5-yellowgreen.svg)
![](https://img.shields.io/badge/Python%20versions-2.7%20and%203.7-yellowgreen.svg)

A Python module for parsing, analyzing, and manipulating GEDCOM files.

GEDCOM files contain ancestry data. The parser is currently supporting
the GEDCOM 5.5 format which is detailed [here](https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf).

> **NOTE**: This module is currently under development and **should not be used in production** yet!
> The current development process can be tracked in the ["develop" branch](https://github.com/reynke/python-gedcom/tree/develop).

## Installation

The module can be installed via [pip](https://pip.pypa.io/).

Run `pip<version> install python-gedcom` to install or `pip<version> install python-gedcom --upgrade`
to upgrade to the newest version uploaded to the [PyPI repository](https://pypi.org/project/python-gedcom/).

If you want to use the latest pre-release of the `python-gedcom` package,
simply append the `--pre` option to `pip`: `pip<version> install python-gedcom --pre`

## Usage

When successfully installed you may import the `gedcom` module and use
it like so:

```python
from gedcom import Gedcom

file_path = '' # Path to your `.ged` file
gedcom = Gedcom(file_path)
```

### GEDCOM Quirks

Large sites like Ancestry and MyHeritage (among others) don't always produce perfectly formatted GEDCOM files.  If you encounter errors in parsing, you might consider disabling strict parsing which will make a best effort to parse the file:

```python
from gedcom import Gedcom

file_path = '' # Path to your `.ged` file
gedcom = Gedcom(file_path, False) # Disable strict parsing
```

Disabling strict parsing will allow the parser to gracefully handle the following quirks:

- Multi-line fields that don't use CONC or CONT
- Handle the last line not ending in a CRLF

### Iterate through all records, search last names and print matches

```python
all_records = gedcom.get_root_child_elements()
for record in all_records:
    if record.is_individual():
        if record.surname_match('Brodie'):
            (first, last) = record.get_name()
            print(first + " " + last)
```

## Reference

The `Element` class contains all the information for a single record in the GEDCOM file, for example and individual.

### `Element` methods

Method | Parameters | Returns | Description
-------|------------|---------|------------
`get_child_elements`   | none          | List of Element | Returns all the child elements of this record
`get_parent_element`   | none          | Element | Returns parent Element
`new_child_element`    | String tag, String pointer, String value | Element | Create a new Element
`add_child_element`    | Element child | Element | Adds the child record
`set_parent_element`   | Element parent| none | Not normally required to be called (add_child_element calls this automatically
`is_individual`        | none          | Boolean | Returns True if the record is that of a person
`is_family`            | none          | Boolean | Returns True if thet record of a family.  Family records can be passed to get_family_members()
`is_file`              | none          | Boolean | Returns True if the record is a pointer to an external file
`is_object`            | none          | Boolean | Returns True if the record is an object (for example multi-media) stored inside the gedcom
`is_private`           | none          | Boolean | Returns True if the record is marked Private
`is_deceased`          | none          | Boolean | Returns True if the individual is marked deceased
`is_child`             | none          | Boolean | Returns True if the individual is a child
`criteria_match`       | colon separated string "surname=[name]:name=[name]:birth][year]:birth_range=[year-to-year]:death=[year]:death_range[year-to-year]"| Boolean | Returns True if the criteria matches
`surname_match`        | String | Boolean | Returns True if the case insensitive substring matches the supplied string
`given_match`          | String | Boolean | Returns True if the case insensitive substring matches the supplied string
`death_range_match`    | Int from, Int to | Boolean | Returns True if Death Year is in the supplied range
`death_year_match`     | Int | Boolean | Returns True if Death Year equals parameter
`birth_range_match`    | Int from, Int to | Boolean | Returns True if Birth Year is in the supplied range
`birth_year_match`     | Int | Boolean | Returns True if Birth Year equals parameter
`get_name`             | none | (String given, String surname) | Returns the Given name(s) and Surname in a tuple
`get_gender`           | none | String | Returns individual's gender
`get_birth_data`       | none | (String date, String place, Array sources) | Returns a tuple of the birth data
`get_birth_year`       | none | Int | Returns the Birth Year
`get_death_data`       | none | (String date, String place, Array sources) | Returns a tuple of the death data
`get_death_year`       | none | Int | Returns the Death Year
`get_burial`           | none | (String date, String place, Array sources) | Returns a tuple of the burial data
`get_census`           | none | List [String date, String place, Array sources] | Returns a List of tuple of the census data
`get_last_change_date` | none | String | Returns the date of the last update to this individual
`get_occupation`       | none | String | Returns the individual's occupation
`get_individual`       | none | Individual | Returns the individual

### `Gedcom` method

Method | Parameters | Returns | Description 
-------|------------|---------|------------
`get_root_element`        | none | Element root | Returns the virtual "root" individual
`get_root_child_elements` | none | List of Element | Returns a List of all Elements
`get_element_dictionary`  | none | Dict of Element | Returns a Dict of all Elements
`get_element_list`        | none | List of Element | Returns a List of all Elements
`get_marriages`           | Element individual | List of Marriage ("Date", "Place") | Returns List of Tuples of Marriage data (Date and Place)
`find_path_to_ancestors`  | Element descendant, Element ancestor| List of Element| Returns list of individuals from the descendant Element to the ancestor Element.  Returns None if there is no direct path
`get_family_members`      | Element family, optional String members_type - one of "ALL" (default), "PARENTS", "HUSB", "WIFE", "CHIL" | List of Element individuals | Returns a list of individuals for the supplied family record, filtered by the members_type
`get_parents`             | Element individual, optional String parent_type - one of "ALL" (default) or "NAT" | List of Element individuals | Returns the individual's parents as a List
`get_ancestors`           | Element individual, optional String ancestor_type - one of "All" (default) or "NAT" | List of Element individuals | Recursively retrieves all the parents starting with the supplied individual
`get_families`            | Element individual optional String family_type - one of "FAMS" (default), "FAMC"|List of Family records | Family Records can be used in get_family_members()
`marriage_range_match`    | Element individual, Int from, Int to| Boolean | Check if individual is married within the specified range
`marriage_year_match`     | Element individual, Int year| Boolean | Check if individual is married in the year specified
`get_marriage_years`      | Element individual |List of Int| Returns Marriage event years
`print_gedcom`            | none | none | Prints the gedcom to STDOUT
`save_gedcom`             | String filename | none | Writes gedcom to specified filename

## Local development

I suggest using [pyenv](https://github.com/pyenv/pyenv) for local development.

### Running tests

1. Run `pip<version> install --no-cache-dir -r requirements.txt` to install dependencies
1. Run tests with [tox](https://tox.readthedocs.io/en/latest/index.html)
    * For Python 2.7 run `tox -e py27` (you need to have Python 2.7 installed)
    * For Python 3.4 run `tox -e py34` (you need to have Python 3.6 installed)
    * For Python 3.5 run `tox -e py35` (you need to have Python 3.6 installed)
    * For Python 3.6 run `tox -e py36` (you need to have Python 3.6 installed)

### Uploading a new package to PyPI

1. Run `pip<version> install --no-cache-dir -r requirements.txt` to install dependencies
1. Run `python<version> setup.py sdist bdist_wheel` to generate distribution archives
1. Run `twine upload --repository-url https://test.pypi.org/legacy/ dist/*` to upload the archives to the Test Python Package Index repository

> When the package is ready to be published to the real Python Package Index
the `repository-url` is `https://upload.pypi.org/legacy/`.

## History

This module was originally based on a GEDCOM parser written by 
Daniel Zappala at Brigham Young University (Copyright (C) 2005) which
was licensed under the GPL v2 and then continued by
[Mad Price Ball](https://github.com/madprime) in 2012.

Further updates by [Nicklas Reincke](https://github.com/nickreynke) and [Damon Brodie](https://github.com/nomadyow) in 2018.

## Changelog

**v0.2.5dev**

- Updated project structure ([#18](https://github.com/nickreynke/python-gedcom/issues/18))
- Fixed `setup.py` outputting correct markdown when reading the `README.md` ([#16](https://github.com/nickreynke/python-gedcom/issues/16))
- Applied Flake8 code style and **added explicit error handling**
- Set up test suite

**v0.2.4dev**

- Made `surname_match` and `given_match` case insensitive ([#10](https://github.com/nickreynke/python-gedcom/issues/10))
- Added new `is_child` method ([#10](https://github.com/nickreynke/python-gedcom/issues/10))

**v0.2.3dev**

- Assemble marriages properly ([#9](https://github.com/nickreynke/python-gedcom/issues/9))
- Return the top NAME record instead of the last one ([#9](https://github.com/nickreynke/python-gedcom/issues/9))

**v0.2.2dev**

- Support BOM control characters ([#5](https://github.com/nickreynke/python-gedcom/issues/5))
- Support the last line not having a CR and/or LF
- Support incorrect line splitting generated by Ancestry.  Insert CONT/CONC tag as necessary ([#6](https://github.com/nickreynke/python-gedcom/issues/6))

**v0.2.1dev**

- Changed broken links to GEDCOM format specification ([#2](https://github.com/nickreynke/python-gedcom/issues/2))

**v0.2.0dev**

- Added `develop` branch to track and update current development process
- Applied PEP 8 Style Guide conventions
- **Renamed variables and methods** to make their purpose more clear
- **Outsourced GEDCOM tags to module level**
- **Added missing inline documentation**
- Optimized `README.md` (sections and better description)
- Added `LICENSE` file
- Cleaned up and optimized code

**v0.1.1dev**

- initial release; [forked](https://github.com/madprime/python-gedcom)

## License

Licensed under the [GNU General Public License v2](http://www.gnu.org/licenses/gpl-2.0.html)

**Python GEDCOM Parser**
<br>Copyright (C) 2018 Damon Brodie (damon.brodie at gmail.com)
<br>Copyright (C) 2018 Nicklas Reincke (contact at reynke.com)
<br>Copyright (C) 2016 Andreas Oberritter
<br>Copyright (C) 2012 Madeleine Price Ball
<br>Copyright (C) 2005 Daniel Zappala (zappala at cs.byu.edu)
<br>Copyright (C) 2005 Brigham Young University

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
