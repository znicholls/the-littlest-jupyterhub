The Littlest JupyterHub
=======================

.. image:: https://circleci.com/gh/znicholls/the-littlest-jupyterhub.svg?style=shield
   :target: https://circleci.com/gh/znicholls/the-littlest-jupyterhub

At the moment I don't know how to test my setup with automated SSL so the build is failing.

A simple JupyterHub distribution for 1-50 users on a single server.

This project is currently in pre-alpha state & extremely prone to breaking!

See `this blog post <http://words.yuvi.in/post/the-littlest-jupyterhub/>`_ for
more information.

Quick Start
-----------

*Warning:* I have destroyed this for now, will have to fix later. For now you have to do all the Let's Encrypt, GitLab and user specification authentication stuff first.

On a fresh Ubuntu 18.04 server, you can install The Littlest JupyterHub with:

.. code-block:: bash

   sudo apt-get update
   sudo apt-get install git
   curl https://raw.githubusercontent.com/znicholls/the-littlest-jupyterhub/master/installer/install.bash | sudo bash -

This takes 2-5 minutes to run. When completed, you can access your new JupyterHub
at the public IP of your server (on the default http port 80)!

For more information (including other installation methods), check out the
`documentation <https://the-littlest-jupyterhub.readthedocs.io>`_.

TODO: Think up a good way to test the text below

Notation
--------

``<name>`` indicates that you should replace ``<name>`` including the ``<>`` with the appropriate file, variable, path etc. For example, ``ls <path>`` could become ``ls the-littlest-jupyterhub/tests``

In code, ``[]`` denotes things which are optional. For example ``command [-f] output.py`` means that you can either execute ``command -f output.py`` or ``command output.py``. We will always explain what the different options mean (and if we don't, please make an issue or a pull request to remedy this!).

Stopping JupyterHub
-------------------

The hub can be stopped with

.. code-block:: bash

    sudo systemctl stop jupyterhub

Generating an SSL Certificate
-----------------------------

You have to be really sure if you want to use JupyterHub without a Secure Sockets Layer (SSL). In most cases, it's not what you want to do if you're going to allow public access to your server. Fortunately, adding an SSL certificate is not too difficult.

If you have a domain name e.g. <my-website.com.au> (more precisely a Fully Qualified Domain Name (FQDN) i.e. a domain name which is associated with an ip address) then you should use "Let's Encrypt". Otherwise you can generate a self-signed certificate.

*A note on FQDNs:* As far as I can tell, all you need to do to get an FQDN is get the ip address of your server, then login to whichever service you've bought the domain name from and tell them to make an 'A record'. An 'A record' associates your ip address with the domain name. For example, if your domains are bought from [strato.de] then you would follow the [instructions here](https://www.strato.de/faq/article/1829/Welche-Einstellungen-kann-ich-im-Konfigurationsdialog-A-Record-vornehmen.html) (yes they're in German, I'm sure there are english versions too if you google 'make A record <your-domain-name-provider>' e.g. `United Domains Help <https://help.uniteddomains.com/hc/en-us/articles/207237229-Creating-an-A-Record-or-Static-IP-Address note that in this resource>`_ [Note that in this resource, 'Destination', means the ip-address of your machine]).

Let's Encrypt
~~~~~~~~~~~~~

Resources: `Certbot home
<https://certbot.eff.org/>`_

To generate your SSL certificate, all you need to do is (remove the ``-y`` flags if you want to interact with the installers):

*Note:* If you've already followed the `Quick Start`_ guide then you will need to stop the JupyterHub and configurable-http-proxy services with ``sudo systemctl stop jupyterhub configurable-http-proxy``

.. code-block:: sh

    sudo apt-get update
    sudo apt-get [-y] install software-properties-common
    sudo add-apt-repository [-y] ppa:certbot/certbot
    sudo apt-get update
    sudo apt-get [-y] install certbot
    sudo certbot certonly --keep-until-expiring --standalone --email '<your-contact-email>' -d <domain-name>

e.g.

.. code-block:: sh

    sudo apt-get update
    sudo apt-get [-y] install software-properties-common
    sudo add-apt-repository [-y] ppa:certbot/certbot
    sudo apt-get update
    sudo apt-get [-y] install certbot
    sudo certbot certonly --standalone --email 'billblogs@gmail.com' -d myawesomecourse.com.au

If successful, the output will include a line like

.. code-block:: sh

   - Congratulations! Your certificate and chain have been saved at:
     /etc/letsencrypt/live/<your-domain>/fullchain.pem

**Automatic Renewal whilst Running JupyterHub**

Having added an SSL certificate with Certbot, you can then set your machine to automatically check if the certificate is due to expire and renew it if required, all with only a brief drop in access to your server (at 3am which shouldn't be a problem).

Firstly, start up an instance of JupyterHub by following the `Quick Start`_ guide. Now go to your server's ip-address and check that the JupyterHub login page is loaded. This means that your server is now running a working setup of JupyterHub.

Next run the following command, which checks that the renewal settings we are going to use will work

.. code-block::

    sudo certbot renew --dry-run --pre-hook "systemctl stop jupyterhub configurable-http-proxy" --post-hook "systemctl restart jupyterhub"

If the output includes a line like 'Congratulations, all renewals succeeded' and your JupyterHub server is still accessible via your ip-address then you know that the renewal command is working.

Open ``/etc/cron.d/certbot`` with ``sudo <editor-of-choice> /etc/cron.d/certbot`` e.g. ``sudo nano /etc/cron.d/certbot``. You should see something like (if haven't used Cron before, check out an `intro to Cron here <https://www.linode.com/docs/tools-reference/tools/schedule-tasks-with-cron/>`_)

.. code-block::

    # /etc/cron.d/certbot: crontab entries for the certbot package
    #
    # Upstream recommends attempting renewal twice a day
    #
    # Eventually, this will be an opportunity to validate certificates
    # haven't been revoked, etc.  Renewal will only occur if expiration
    # is within 30 days.
    SHELL=/bin/sh
    PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

    0 */12 * * * root test -x /usr/bin/certbot -a \! -d /run/systemd/system && perl -e 'sleep int(rand(43200))' && certbot -q renew

Change the last line to

.. code-block::

    0 3 * * * root test -x /usr/bin/certbot -a \! -d /run/systemd/system && perl -e 'sleep int(rand(43200))' && certbot -q renew --pre-hook "systemctl stop jupyterhub configurable-http-proxy" --post-hook "systemctl restart jupyterhub"

Finally, add the following to ``./the-littlest-jupyterhub/tljh/jupyterhub_config.py``

.. code-block:: python

    # use SSL port
    c.JupyterHub.port = 443
    c.JupyterHub.ssl_key = '/etc/letsencrypt/live/course.magicc.org/privkey.pem'
    c.JupyterHub.ssl_cert = '/etc/letsencrypt/live/course.magicc.org/fullchain.pem'

    # redirect http queries to https
    c.ConfigurableHTTPProxy.command = ['configurable-http-proxy', '--redirect-port', '80']

Self-signed Certificate
~~~~~~~~~~~~~~~~~~~~~~~

Resources: `JupyterHub docs
<http://jupyterhub.readthedocs.io/en/latest/getting-started/config-basics.html>`_

You could store the certificate anywhere but convention seems to be to store it in ``/etc`` somewhere, e.g. ``/etc/selfsigned``. With this in mind, to actually generate the certificate do the following

.. code-block:: sh

    cd <path-to-certificate-location>
    openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout jupyterhub.key -out jupyterhub.crt

For example,

.. code-block:: sh

    cd /etc/selfsigned
    openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout jupyterhub.key -out jupyterhub.crt

Example answers to questions:

- *Country*: AU
- *State*: VIC
- *Locality*: Melbourne
- *Organization Name*: University of Melbourne
- *Organizational Unit*: Department of Pyschology
- *Common Name*: Bill Blogs
- *Email Address*: bbblogs@gmail.com

TODO: Add bit telling you what to add to `jupyterhub_config.py` to use this certificate

Adding GitLab/GitHub Authentication
-----------------------------------

Resources: `Min's Overview Video <https://www.youtube.com/watch?v=gSVvxOchT8Y&feature=youtu.be>`_

GitLab
~~~~~~

TODO: Add switch to make this a choice, not the default

Resources: `JupyterHub GitLab Authenticator Example <https://github.com/jupyterhub/oauthenticator#gitlab-setup>`_

Login to `<gitlab.com>`_ then go to *Settings* (click on your photo in the top right-hand corner then select from the drop-down menu) --> *Applications* (in left-hand sidebar) and fill out the form. Redirect URL must be `https://<your-domain-or-ip-address>/hub/oauth_callback`. Don't tick any of the scope boxes. Hit *Save Application*. The information on the page you see next is what we now need so don't close it.

Next make a file called ``env`` in ``/root/jupyterhubenv/env`` (if you want to change this path or filename then you're going to have to change where ``tljh`` looks for its environment too) by executing the following in a shell:

.. code-block:: bash

    sudo <editor-of-choice> /root/jupyterhubenv/env

Once in the editor, make the contents of the file

.. code-block:: bash

    GITLAB_CLIENT_ID=<copy_application_id_from_gitlab>
    GITLAB_CLIENT_SECRET=<copy_secret_from_gitlab>
    OAUTH_CALLBACK_URL=https://<YOURDOMAIN>/hub/oauth_callback

Next, add the following to ``./the-littlest-jupyterhub/tljh/jupyterhub_config.py``

.. code-block:: python

    from oauthenticator.gitlab import LocalGitLabOAuthenticator
    c.JupyterHub.authenticator_class = LocalGitLabOAuthenticator
    # make a user on the system if they don't already exist
    c.LocalGitLabOAuthenticator.create_system_users = True
    c.LocalGitLabOAuthenticator.delete_invalid_users = True

and finally, to ``/opt/tljh/config.yaml`` add

.. code-block:: yaml

    auth:
      type: GitLab # at the moment this could be any string but that's a bug fix for future


GitHub
~~~~~~

TODO: add switch to actually make this possible in one line

Resources: `Min's Overview Video <https://www.youtube.com/watch?v=gSVvxOchT8Y&feature=youtu.be>`_

Go to `<https://github.com/settings/applications/new>`_. Fill out the boxes with whatever you want (the first 3 don't actually matter). The one that matters is the *Authorization callback URL*. This must be `https://<your-domain-or-ip-address>/hub/oauth_callback`. Hit *Register application*. The information on the page you see next is what we now need so don't close it.

Next make a file called ``jupyterhub-env`` in ``/root/jupyterhubenv/env`` (if you want to change this path or filename then you're going to have to change where ``tljh`` looks for its environment too) by executing the following in a shell:

.. code-block:: bash

    sudo <editor-of-choice> /root/jupyterhubenv/env

Once in the editor, make the contents of the file

.. code-block:: bash

    GITHUB_CLIENT_ID=<copy_from_github>
    GITHUB_CLIENT_SECRET=<also_copy_from_github>
    OAUTH_CALLBACK_URL=https://<YOURDOMAIN>/hub/oauth_callback

Next, add the following to ``./the-littlest-jupyterhub/tljh/jupyterhub_config.py``

.. code-block:: python

    from oauthenticator.github import LocalGitHubOAuthenticator
    c.JupyterHub.authenticator_class = LocalGitHubOAuthenticator
    # make a user on the system if they don't already exist
    c.LocalGitLabOAuthenticator.create_system_users = True
    c.LocalGitLabOAuthenticator.delete_invalid_users = True

and finally, to ``/opt/tljh/config.yaml``, add

.. code-block:: yaml

    auth:
      type: GitHub # at the moment this could be any string but that's a bug fix for future

AAF Authorisation
~~~~~~~~~~~~~~~~~

TODO: Find someone clever to write this

Specifying Users
----------------

As the hub is set up by default, anyone who can authenticate will also be able to create a user profile. Whilst this is simple, it may not exactly be our desired behaviour. Fortunately, the hub provides the ability to control who can access the hub and who cannot as shown.

We can specify users by adding the following text to ``/opt/tljh/config.yaml``. ``admin`` will have full access to configure the hub whilst ``allowed`` users specifies all users who can login.

.. code-block:: yaml

    users:
      allowed:
        - <allowed-user-1>
        - <allowed-user-2>
        - <allowed-user-3>
      admin:
        - <admin-user-1>
        - <admin-user-2>

Using Git
---------

To do this, you need to make sure that you can access git repositories from the server. If they're public, it's all ok. If they're private, you're going to need to add an ssh-key to your GitHub/GitLab/etc. account. This can be done with the following

.. code-block:: bash

    ssh-keygen -t rsa -C "<your-email>" -b 4096 -f ~/.ssh/<name-of-key>

Then copy the contents of ``<name-of-key>.pub`` (not ``<name-of-key>``!, that's your private key) to your GitHub/GitLab account. Then add the following to your ``~/.ssh/config``

.. code-block::

    # <Hostname> server
    Host gitlab.com # or github.com
        RSAAuthentication yes
        IdentityFile ~/.ssh/<name-of-key>
