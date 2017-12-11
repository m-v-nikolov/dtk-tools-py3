Migrate from Python 2.7
=======================


=============================================
Differences between Python 2.7 and Python 3.6
=============================================


.. contents::
    :local:


Changed library names
---------------------

+-----------------------------+-----------------------------+
|       Python2.7 Name        |    Python 3.6 Name          |
+=============================+=============================+
| ConfigParser                | configparser                |
+-----------------------------+-----------------------------+
| Queue                       | queue                       |
+-----------------------------+-----------------------------+
| SocketServer                | socketserver                |
+-----------------------------+-----------------------------+
| ...                         | ...                         |
+-----------------------------+-----------------------------+

print
-----

Python 2.7::

    print 'Hello...'

Python 3.6, print is a function: ::

    print('Hello...')

exec
----

Python 2.7, exec is a statement.

Python 3.6, exec is a function.


str
---

Python 2.7, implicit str type is ASCII, separate unicode(), but no byte type.

Python 3.6, all text (str) is UNICODE, unicode() is gone and encoded text is binary data (bytes).

UNICODE
-------

Python 2.7::

    print unicode('this is like a python3 str type')

Python 3.6, it has Unicode (utf-8) strings, and 2 byte classes: byte and bytearrays::

    print('strings are now utf-8 \u03BCnico\u0394é!')

StringIO
--------

Python 2.7::

    from StringIO import StringIO
    # or:
    from cStringIO import StringIO

Python 3.6::

    from io import BytesIO     # for handling byte strings
    from io import StringIO    # for handling unicode strings

Dictionary Methods.
-------------------

Example: ::

    d = {'key1': 'value1',
         'key2': 'value2',
         'key3': 'value3'}

Python 2.7::

    d.iterkeys(),
    d.itervalues(),
    d.iteriterms(),
    if d.has_key('key'):

.. note::
        has_key(...) method has been removed in Python 3.

Python 3.6: ::

    d.keys(),
    d.values(),
    d.iterms(),
    if 'key' in d:

file
----

Python 2.7::

    with file(filename) as f:
        text = f.read()

Python 3.6: ::

    with open(filename, "r") as f:
        text = f.read()

input
-----

Python 2.7::

    raw_input('...')

Python 3.6: ::

    input('...')

long
----
Python 2.7::

    has two type: int and long

Python 3.6: ::

    combine int and long into one type: int

compare
-------

Python 2.7, there are two ways: ::

    a <> b
    a != b

Python 3.6, <> has been removed: ::

    a != b

except
------

Python 2.7::

    except (Exception1, Exception2), target:

Python 3.6: ::

    except (Exception1, Exception2) as target:

range() and xrange()
--------------------

Python 2.7:

    In Python 2 `range()` returns a list, and `xrange()` returns an object that will only generate the items in the range when needed, saving memory.

Python 3.6:

    In Python 3, the `range()` function is gone, and `xrange()` has been renamed `range()`. In addition the `range()` object support slicing in Python 3.2 and later.


class
-----

Python 2.7:

    In Python 2 there are two types of classes, “old-style” and “new”.

Python 3.6:

    The “old-style” classes have been removed in Python 3, so all classes now subclass from object, even if they don’t do so explicitly.

Metaclasses
-----------

Suppose we have::

    class BaseForm(object):
        pass

    class FormType(type):
        pass

Python 2.7::

    # Python 2 only:
    class Form(BaseForm):
        __metaclass__ = FormType
        pass

Python 3.6::

    # Python 3 only:
    class Form(BaseForm, metaclass=FormType):
        pass


cStringIO
---------

Python 2.7::

    import cStringIO

Python 3.6: ::

    import io
    f = io.StringIO("some initial text data")

Queue
-----

Python 2.7::

    from Queue import Queue

Python 3.6: ::

    from queue import Queue

basestring
----------

Python 2.7::

    if isinstance(filepath, basestring):

Python 3.6:

The built-in basestring abstract type was removed. Use str instead::

    if isinstance(filepath, str):


ImportError
-----------
Property message has been changed to msg.

Python 2.7::

    try:
        return import_module(module_name)
    except ImportError as e:
        e.args = ("'%s' during loading module '%s' in %s files: %s." %
              (e.message, module_name, os.getcwd(), os.listdir(os.getcwd())),)
        raise e

Python 3.6::

    try:
        return import_module(module_name)
    except ImportError as e:
        e.args = ("'%s' during loading module '%s' in %s files: %s." %
              (e.msg, module_name, os.getcwd(), os.listdir(os.getcwd())),)
        raise e


Raising exceptions
------------------

Python 2.7, accepts both notations, the ‘old’ and the ‘new’ syntax::

    raise IOError, "file error"
    raise IOError("file error")

Python 3.6, chokes (and raises a SyntaxError in turn) if we don’t enclose the exception argument in parentheses::

    raise IOError("file error")

Handling exceptions
-------------------

Python 2.7, ::

    try:
        let_us_cause_a_NameError
    except NameError, err:
        print err, '--> our error message'

Python 3.6, we have to use the “as” keyword now::

    try:
        let_us_cause_a_NameError
    except NameError as err:
        print(err, '--> our error message')


Integer division
----------------

Python 2.7:

    In Python 2, the result of dividing two integers will itself be an integer; in other words 3/2 returns 1.

Python 3.6:

    In Python 3 integer division will always return a float. So 3/2 will return 1.5 and 4/2 will return 2.0.

Imports relative to a package
-----------------------------

Suppose the package is::

    mypackage/
        __init__.py
        submodule1.py
        submodule2.py

and the code below is in submodule1.py:

Python 2.7::

    # Python 2 only:
    import submodule2

Python 3.6::

    # Python 2 and 3:
    from . import submodule2

map
---

Python 2.7:

In Python 2 map() returns a list, for example::

    map(self.add_analyzer, analyzers)

.. note::
    add_analyzer method gets executed.


Python 3.6:

In Python 3 it returns an iterator not a list::

    map(self.add_analyzer, analyzers)

.. note::
    add_analyzer method does not get executed.

In Python 3 to make sure add_analyzer method gets executed, we can do something like::

    list(map(self.add_analyzer, analyzers))

urllib2
-------

Python 2.7:

Example::

    import urllib2

    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    data = resp.read()

Python 3.6:

The urllib2 module has been split across several modules in Python 3 named urllib.request and urllib.error. ::

    from urllib.request import Request, urlopen

    req = Request(url)
    resp = urlopen(req)
    data = resp.read()



dictionary and next()
---------------------

Example: ::

    d = {'key1': 'value1',
         'key2': 'value2',
         'key3': 'value3'}

Python 2.7, the following return a generator::

    d.iterkeys(),
    d.itervalues(),
    d.iteriterms(),

We can go through each item by using .next() or next(...), for example::

    key = d.iterkeys().next()
    key = next(d.iterkeys())


Python 3.6, the following does not return a generator::

    d.keys(),
    d.values(),
    d.iterms(),

and we can not do below, for example::

    key = d.keys().next()
    key = next(d.keys())

But you can do: ::

    for key in d.keys():
        ...

Misc.
-----

Some commonly used functions and methods that don’t return lists anymore in Python 3::

    * zip()
    * map()
    * filter()
    * dictionary’s .keys() method
    * dictionary’s .values() method
    * dictionary’s .items() method


For-loop variables and the global namespace leak.

Python 2.7, ::

    i = 1
    print 'before: i =', i
    print 'comprehension: ', [i for i in range(5)]
    print 'after: i =', i


results::

    before: i = 1
    comprehension:  [0, 1, 2, 3, 4]
    after: i = 4

Python 3.6, ::

    i = 1
    print('before: i =', i)
    print('comprehension: ', [i for i in range(5)])
    print('after: i =', i)

results::

    before: i = 1
    comprehension: [0, 1, 2, 3, 4]
    after: i = 1

Banker’s Rounding
-----------------

Python 2.7, decimals are rounded to the nearest number (float). ::

    round(15.5)
    round(16.5)


results::

    16.0
    17.0

Python 3.6, decimals are rounded to the nearest even number. ::

    round(15.5)
    round(16.5)


results::

    16
    16


lambda function
---------------

Sometimes in DTK-TOOLS we encounter error something like::

    AttributeError: Can't pickle local object 'config_setup_fn.<locals>.<lambda>'

To fix the issue above, we changed original function, for example,

Python 2.7::

    def config_setup_fn(duration=21915):
        return lambda cb: cb.update_params({'Simulation_Duration' : duration,
                                    'Infection_Updates_Per_Timestep' : 8})


Python 3.6: ::

    def config_setup_fn(duration=21915):
        def fn(cb):
            cb.update_params({'Simulation_Duration' : duration,
                              'Infection_Updates_Per_Timestep' : 8})
        return fn


Resources
---------

* Porting Python 2 Code to Python 3

  https://docs.python.org/3/howto/pyporting.html
* Moving from Python 2 to Python 3

  http://ptgmedia.pearsoncmg.com/imprint_downloads/informit/promotions/python/python2python3.pdf
* Python 2 vs. Python 3

  https://www.slideshare.net/pablito56/python-2-vs-python-3
* Cheat Sheet: Writing Python 2-3 compatible code

  http://python-future.org/compatible_idioms.html
* Cheat Sheet: Writing Python 2-3 compatible code

  http://python-future.org/compatible_idioms.html
* Dive Into Python 3

  http://www.diveintopython3.net/
* Python 3 Tutorial

  https://www.tutorialspoint.com/python3/