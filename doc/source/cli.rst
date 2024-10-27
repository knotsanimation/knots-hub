CLI
===

Command Line Interface documentation.

Usage
-----

Assuming knots-hub and its dependencies are installed:

.. code-block:: shell

   python -m knots-hub --help

Commands
--------

``--help``
__________

.. exec_code::
   :hide_code:

   import knots_hub
   knots_hub.get_cli(None, None, ["--help"])

kloch
_____

Directly call the `kloch <https://knotsanimation.github.io/kloch/>`_ tool that
is integrated in the hub.

All arguments are directly passed to the kloch
CLI so check the kloch documentation for details.


uninstall
_________

.. exec_code::
   :hide_code:

   import knots_hub
   knots_hub.get_cli(None, None, ["uninstall", "--help"])


about
_____

.. exec_code::
   :hide_code:

   import knots_hub
   knots_hub.get_cli(None, None, ["about", "--help"])