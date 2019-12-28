Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-bitmap_font/badge/?version=latest
    :target: https://circuitpython.readthedocs.io/projects/bitmap_font/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://discord.gg/nBQh6qu
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/actions/
    :alt: Build Status

Loads bitmap fonts into CircuitPython's displayio. BDF files are well supported. PCF and TTF
support is not yet complete.

Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://github.com/adafruit/Adafruit_CircuitPython_Bundle>`_.

Installing from PyPI
--------------------
On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-bitmap_font/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-bitmap_font

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-bitmap_font

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-bitmap_font

Usage Example
=============

.. code-block::python

    from adafruit_bitmap_font import bitmap_font
    from displayio import Bitmap
    font = bitmap_font.load_font("scientifica-11.bdf", Bitmap)
    print(font.get_glyph(ord("A")))


Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/blob/master/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
