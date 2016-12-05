.PHONY: install clean test run watch-css css test pt cc mi raw production deploy

PYTHON = venv/bin/python
PIP-INSTALL = build/pip-install
SSL = server.key server.crt
ENV = .env
PROD = dist

${PIP-INSTALL}: ${PYTHON} requirements.txt
	mkdir -p build
	venv/bin/pip install -r requirements.txt
	touch ${PIP-INSTALL}

${PYTHON}:
	virtualenv venv

${SSL}:
	./dummy_ssl.sh

${ENV}:
	cp .env.default .env

run:
	${PYTHON} ./src/app.py

watch-css:
	scss --watch src/assets/scss/main.scss:src/static/css/main.css

css:
	./generate_css.sh

test:
	nosetests src/tests --with-coverage --cover-package=app,cadapter,mail_integration

pt:
	nosetests src/tests --with-coverage --cover-package=app,cadapter,mail_integration --nocapture

cc:
	radon cc src -a -s --ignore "tests"

mi:
	radon mi src -s --ignore "tests"

raw:
	radon raw src -s --ignore "tests"

install: ${PIP-INSTALL} ${SSL}

production: install css
	rm -rf ${PROD}
	rsync -a src ${PROD} --exclude src/assets --exclude src/tests
	mv css_suffix.txt ${PROD}
	cp ${SSL} ${PROD}
	cp passenger_wsgi.py ${PROD}

deploy:
	scp -r ${PROD}/* kompisby@kompisbyran.hemsida.eu:cms-kompisbyran-se

clean:
	rm -rf venv
	rm -rf node_modules
