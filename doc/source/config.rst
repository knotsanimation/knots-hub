Configuration
=============


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
program installer that must be installed on the user local system.

Additionally each installer can be configured.

The abstract configuration is defined as:

.. tip::

   If needed the reading of the configuration is performed by :func:`knots_hub.installer.read_vendor_installers_from_file`

.. code-block::

   {
      "{installer_name}": { ... },
      ...
   }

The list of supported installers is as follow:

.. exec-inject::
   :filename: _injected/exec-config-vendor-installers.py



