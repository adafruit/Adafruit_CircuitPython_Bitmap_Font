Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-bitmap_font/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/bitmap-font/en/latest/
    :alt: Documentation Status

.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/actions/
    :alt: Build Status

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff

Loads bitmap fonts into CircuitPython's displayio. BDF and PCF files are well supported. TTF
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
    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install adafruit-circuitpython-bitmap_font

Usage Example
=============

.. code-block:: python

    from adafruit_bitmap_font import bitmap_font
    from displayio import Bitmap
    font = bitmap_font.load_font("fonts/LeagueSpartan-Bold-16.bdf", Bitmap)
    print(font.get_glyph(ord("A")))


Creating Fonts
==============

See `this learn guide <https://learn.adafruit.com/custom-fonts-for-pyportal-circuitpython-display>`_ for more information about building custom font files.

The command line tool :code:`otf2bdf` can be used make bdf files for use with this library.

The command line tool :code:`bdftopcf` can be used make pcf files for use with this library.

Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/bitmap-font/en/latest/>`_.

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
