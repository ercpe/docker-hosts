clean:
	find -name "*.py?" -delete
	rm -rf MANIFEST *.egg-info dist build deb_dist *.tar.gz

install_deps:
	pip3 install --user -r requirements.txt
	pip3 install --user -r requirements_dev.txt

deb:
	python3 setup.py --command-packages=stdeb.command bdist_deb
