"""
JupyterHub config for the littlest jupyterhub.
"""
import os
from os import makedirs, chown, chmod, listdir, walk
from os.path import isdir, isfile, expanduser, isfile, join
import stat
from shutil import copyfile
import pwd
import grp

from systemdspawner import SystemdSpawner
from tljh import user, configurer
from git import Repo
from git.cmd import Git

INSTALL_PREFIX = os.environ.get('TLJH_INSTALL_PREFIX', '/opt/tljh')
USER_ENV_PREFIX = os.path.join(INSTALL_PREFIX, 'user')

class CustomSpawner(SystemdSpawner):
    def start(self):
        """
        Perform system user activities before starting server
        """
        # FIXME: Move this elsewhere? Into the Authenticator?
        user.ensure_user(self.user.name)
        user.ensure_user_group(self.user.name, 'jupyterhub-users')
        if self.user.admin:
            user.ensure_user_group(self.user.name, 'jupyterhub-admins')
        else:
            user.remove_user_group(self.user.name, 'jupyterhub-admins')

        NOTEBOOKS_REPO_URL = 'git@gitlab.com:climate-modelling-climate-change-erth90026/notebooks.git'
        NOTEBOOKS_REPO_DIR = '/data/notebooks-repo'
        NOTEBOOKS_SRC_DIR = join(NOTEBOOKS_REPO_DIR, 'notebooks')
        NOTEBOOKS_SRC_SUBDIRS_TO_COPY = [
            'tutorials',
            'assignments',
        ]
        NOTEBOOKS_SRC_SUBDIRS_TO_LOCK = [
            'assignments-solutions',
        ]
        USER_ROOT = join('/home', self.user.name)
        # NOTEBOOKS_USER_DIR = join(USER_ROOT, 'notebooks', 'tutorials')
        NOTEBOOKS_USER_DIR = join(USER_ROOT, 'notebooks')

        if not isdir(NOTEBOOKS_REPO_DIR):
            Repo.clone_from(NOTEBOOKS_REPO_URL, NOTEBOOKS_REPO_DIR)

        notebooks_repo = Git(NOTEBOOKS_REPO_DIR)
        notebooks_repo.pull()

        root_uid = pwd.getpwnam("root").pw_uid
        root_gid = grp.getgrnam("root").gr_gid
        for src_subdir_to_lock in NOTEBOOKS_SRC_SUBDIRS_TO_LOCK:
            dir_to_lock = join(NOTEBOOKS_REPO_DIR, src_subdir_to_lock)
            nrdmode = os.stat(dir_to_lock)
            if (nrdmode.st_mode & stat.S_IRWXO != 0) or (nrdmode.st_mode & stat.S_IRWXG != 0):
                chown(dir_to_lock, root_uid, root_gid)
                chmod(dir_to_lock, 0o700)

        if not isdir(NOTEBOOKS_USER_DIR):
            makedirs(NOTEBOOKS_USER_DIR)

        for src_subdir in NOTEBOOKS_SRC_SUBDIRS_TO_COPY:
            src_dir = join(NOTEBOOKS_SRC_DIR, src_subdir)

            usr_dir = join(NOTEBOOKS_USER_DIR, src_subdir)
            if not isdir(usr_dir):
                makedirs(usr_dir)

            notebook_files = [
                f for f in listdir(src_dir)
                if f.endswith('.ipynb')
            ]
            for file_notebook in notebook_files:
                source_notebook = join(src_dir, file_notebook)
                user_notebook = join(usr_dir, file_notebook)
                if not isfile(user_notebook):
                    copyfile(source_notebook, user_notebook)

            user_uid = pwd.getpwnam(self.user.name).pw_uid
            user_gid = grp.getgrnam(self.user.name).gr_gid
            for root, dirs, files in walk(USER_ROOT):
                for momo in dirs:
                    chown(join(root, momo), user_uid, user_gid)
                for momo in files:
                    chown(join(root, momo), user_uid, user_gid)

        return super().start()

c.JupyterHub.spawner_class = CustomSpawner

# use SSL port
c.JupyterHub.port = 443
letsencrypt_folder = '/etc/letsencrypt/live'
domain_folder = listdir(letsencrypt_folder)[0]
c.JupyterHub.ssl_key = join(letsencrypt_folder, domain_folder, 'privkey.pem')
c.JupyterHub.ssl_cert = join(letsencrypt_folder, domain_folder, 'fullchain.pem')

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

# limit memory usage for each user
c.SystemdSpawner.mem_limit = '0.5G'

configurer.apply_yaml_config(os.path.join(INSTALL_PREFIX, 'config.yaml'), c)
