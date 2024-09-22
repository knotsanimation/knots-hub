Configurations
==============


Tweak the behavior of the knots-hub runtime using a configuration system.

Each config key is set using an individual environment variable:

.. exec_code::
   :hide_code:
   :filename: _injected/exec-config-envvar.py


Content
-------

.. program:: config

.. exec-inject::
   :filename: _injected/exec-config-autodoc.py


Vendor Installers Config
------------------------

A configuration file in the ``json`` syntax that define a list of
program installer that must be installed on the user local system and how each of them
must be configured.

The abstract configuration is defined as:

.. code-block::

   {
      "{installer_name}": {
         ...  # installer configuration arguments
      },
      # next installer
      ...
   }

The list of supported installers and their configuration is as follow:

.. exec-inject::
   :filename: _injected/exec-config-vendor-installers.py

