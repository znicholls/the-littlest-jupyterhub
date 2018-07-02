"""
JupyterHub config for the littlest jupyterhub.
"""
import os
from systemdspawner import SystemdSpawner
from tljh import user, configurer

INSTALL_PREFIX = os.environ.get('TLJH_INSTALL_PREFIX', '/opt/tljh')
USER_ENV_PREFIX = os.path.join(INSTALL_PREFIX, 'user')

class CustomSpawner(SystemdSpawner):
    def start(self):
        """
        Perform system user activities before starting server
        """
        # FIXME: Move this elsewhere? Into the Authenticator?
        print(os.environ('GITLAB_CLIENT_ID'))
        user.ensure_user(self.user.name)
        user.ensure_user_group(self.user.name, 'jupyterhub-users')
        if self.user.admin:
            user.ensure_user_group(self.user.name, 'jupyterhub-admins')
        else:
            user.remove_user_group(self.user.name, 'jupyterhub-admins')
        return super().start()

c.JupyterHub.spawner_class = CustomSpawner

# use SSL port
c.JupyterHub.port = 443
c.JupyterHub.ssl_key = '/etc/letsencrypt/live/course.magicc.org/privkey.pem'
c.JupyterHub.ssl_cert = '/etc/letsencrypt/live/course.magicc.org/fullchain.pem'

# redirect http queries to https
c.ConfigurableHTTPProxy.command = ['configurable-http-proxy', '--redirect-port', '80']

from oauthenticator.gitlab import LocalGitLabOAuthenticator
c.JupyterHub.authenticator_class = LocalGitLabOAuthenticator
# make a user on the system if they don't already exist
c.LocalGitLabOAuthenticator.create_system_users = True
c.LocalGitLabOAuthenticator.delete_invalid_users = True

c.SystemdSpawner.extra_paths = [os.path.join(USER_ENV_PREFIX, 'bin')]
c.SystemdSpawner.default_shell = '/bin/bash'
# Drop the '-singleuser' suffix present in the default template
c.SystemdSpawner.unit_name_template = 'jupyter-{USERNAME}'

configurer.apply_yaml_config(os.path.join(INSTALL_PREFIX, 'config.yaml'), c)
