knots-hub
=========

The top-level application used by artists to use the Knots pipeline.

The app allow to install and use all necessary software on the local user machine.

In its current state, knots-hub is a :abbr:`CLI (Command Line Interface)` meaning
that it must be executed from a terminal as there is no graphical interface yet.

Design
------

The hub is intended to be packaged as a standalone executable application
(done by `knots-pipe-internal <https://github.com/knotsanimation/knots-pipe-internals>`_
repository). Once packaged the app will be split into 2 states: `server` and `local`.

- `server`: is the packaged app stored on a shared network location that is
  always used as the starting point.
- `local`: is the packaged app installed on the user local system, from which
  the bulk of the code is executed for performances reasons.

The hub integrate this paradigm into its code architecture, to include a
local-app update system. It is able to find if the local app is out-of-date
and need an updating to the latest server version.

Along with the hub app itself, it also handle the installing of external software
referred as "vendors", to the local user system. The install recipe for each
vendor is defined in this repository, which can still be modified by an
user-configuration. Vendors also have an auto-update system that is able to keep
the local user system up-to-date.

Be aware that this design force the hub to always be launched from the `server`
variant. The `local` is only launched by the `server` during a restart.

.. container:: only-dark rounded

   .. image:: _static/diagram-overview.dark.svg
      :alt: overview diagram of knots-hub interraction with other software

.. container:: only-light rounded

   .. image:: _static/diagram-overview.svg
      :alt: overview diagram of knots-hub interraction with other software


Install system
______________

The install/auto-update system is always executed when the app starts, but only
run when the app runtime correspond to the `server` variant. 

- If the hub detect the local app is not installed it will
  install it and **restart** [1]_ to it (the runtime will become `local`).
- Else if the hub detect the local app is out-of date it will delete it, then 
  install the latest version and **restart** to the local variant too.

Then when the runtime is `local`, the app will perform an install/update of the
vendors.

Finally the initial command requested is ran once the install system is over.


Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: user

   Home <self>
   cli
   config

.. toctree::
   :maxdepth: 2
   :caption: developer

   contributing
   public-api/index
   GitHub <https://github.com/knotsanimation/knots-hub>
   changelog

----

**Footnotes:**

.. [1] restart means the current runtime (server) is exited, and we seamlessy
       launch a new runtime using the local app.