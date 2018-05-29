sshadduser
==========

Problem
-------

Imagine that you have SSH access to a server and you need to grant access to a
coworker. You must remember to perform multiple steps, such as creating a home
directory, setting a password, making sure the user is included in the correct
groups, etc. If the server requires public key authentication (the default for
Amazon EC2), then you must also put the keys in the right place, with the right
ownership and permissions. Screw up any tiny part and OpenSSH will stubbornly
and unhelpfully block the new user without any explanation why.

    Yo dawg, I heard you like ``-vvv`` flags so I put some ``LogLevel VERBOSE``
    in your ``sshd_config`` so you can debug your SSH when you debug your SSH.

    -Xzibit's endorsement of ``sshadduser`` (paraphrased)

Solution
--------

The ``sshadduser`` script does the following things:

* Create account and home directory.
* Prompt for password or generate random password.
* Append keys to user's ``authorized_keys``, creating if necessary and setting
  correct ownership/permissions. (optional)
* Add user to supplemental groups. (optional)

You could do these things yourself, but if you're like me, you tend to miss a
step every now and then. Or you could write a bash script to do it, but then
you'd have to copy that bash script everywhere you ever wanted to use it. And
if you wanted somebody else to grant SSH access *to you*, then you'd have to
explain to them how to use your script first.

On the other hand, ``sshadduser`` has super simple syntax. It runs
interactively, so you don't need to memorize a bunch of command line flags to
use it. It's easy to install on any reasonably modern \*nix. And if you want
somebody else to use it, just point them at this README.

Installation
------------

This package requires Python 3.

If you have ``pip3`` installed, then you can quickly install ``sshadduser`` as 
follows:

.. code:: bash

    $ sudo -H pip3 install sshadduser

If you do not have ``pip3``, then you should install from a tarball instead:

.. code:: bash

    $ wget https://github.com/TeamHG-Memex/sshadduser/archive/1.0.tar.gz -O sshadduser.tgz
    $ tar xzf sshadduser.tgz
    $ cd sshadduser-1.0 && sudo python3 setup.py install

Whichever installation path you take, you should verify correct installation
by running the following:

.. code:: bash

    $ sshadduser --version
    sshadduser, version 1.0

Usage
-----

Specify the name of the user to create followed by supplemental groups (if
any). You will be prompted for a password and optional OpenSSH keys. For
example to create a user ``jane`` and add her to ``sudo`` and ``rockstar``
groups:

.. code:: bash

    $ sudo sshadduser jane sudo rockstar
    Enter a password (or leave blank to generate random password):

    Path to shell (or leave blank for system default):
    /bin/bash
    Enter SSH keys one per line. A blank line terminates.
    ssh-rsa AAAAB3NzaC1yc2EAAAAblahblahblah jane@laptop
    ssh-rsa AAAAB3NzaC1yc2EAAAAdoowopdoowop jane@desktop

    Created an account named jane with password e0UkMmvPW6mT and 2 SSH keys.
    Added supplemental groups: sudo and rockstar.

That's it! If something goes wrong, remove the user and try again:

.. code:: bash

    $ sudo userdel -r jane

If you want to file a bug report, run the command with verbose logging enabled
and attach the complete output:

.. code:: bash

    $ sudo sshadduser -v debug jane

Compatibility
-------------

Designed for POSIX environments, this is still a beta-quality project and it
has not been tested on many platforms. It has been tested on Ubuntu 14.04 and
16.04, and it should work on other systems, too. If you find that it does not
run somewhere that you need it, file an issue or — better yet — submit a pull
request.

----

.. image:: https://hyperiongray.s3.amazonaws.com/define-hg.svg
	:target: https://www.hyperiongray.com/?pk_campaign=github&pk_kwd=sshadduser
	:alt: define hyperiongray
