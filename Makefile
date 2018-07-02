.PHONY: force-reinstall
force-reinstall:
	curl -H 'Cache-Control: no-cache' https://raw.githubusercontent.com/znicholls/the-littlest-jupyterhub/master/installer/install.bash | sudo bash -
