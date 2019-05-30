TARGET?=tests

test:
	PYTHONPATH="." python3 tests/ -v

compile:
	@echo Compiling python code
	python -m compileall .

compile_optimized:
	@echo Compiling python code optimized
	python -O -m compileall .

#coverage:
#	coverage erase
#	PYTHONPATH="." coverage run --source='.' --omit 'tests/*,setup.py' --branch tests/__main__.py
#	coverage xml -i
#	coverage report -m

clean:
	find -name "*.py?" -delete

install_deps:
	pip install --user -r requirements.txt
	pip install --user -r requirements_dev.txt

#test
jenkins: install_deps compile compile_optimized
