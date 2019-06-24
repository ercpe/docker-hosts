TARGET?=tests

test:
	PYTHONPATH="." python3 tests/ -v

compile:
	@echo Compiling python code
	python3 -m compileall .

compile_optimized:
	@echo Compiling python code optimized
	python3 -O -m compileall .

clean:
	find -name "*.py?" -delete
	rm -rf MANIFEST *.egg-info dist deb_dist *.tar.gz

install_deps:
	pip3 install --user -r requirements.txt
	pip3 install --user -r requirements_dev.txt

deb:
	python3 setup.py --command-packages=stdeb.command bdist_deb

#test
jenkins: clean install_deps compile compile_optimized
