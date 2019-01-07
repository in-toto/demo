run: _demo clean

_demo:
	python run_demo.py

confirm:
	@echo "This will install python dependencies with pip. Recommend using a virtualenv, check the Readme. Continue? [y/N] " && read ans && [ $${ans:-N} == y ]

install: confirm
	pip install -r requirements.txt

clean:
	@echo "Removing files created for demo."
	rm -f final_product/untar.link
	rm -f final_product/package.2f89b927.link
	rm -f final_product/clone.776a00e2.link
	rm -rf final_product/demo-project
	rm -f final_product/alice.pub
	rm -f final_product/demo-project.tar.gz
	rm -f final_product/root.layout
	rm -f final_product/update-version.776a00e2.link
	rm -f functionary_bob/clone.776a00e2.link
	rm -rf functionary_bob/demo-project/
	rm -f functionary_bob/update-version.776a00e2.link
	rm -rf functionary_carl/demo-project.tar.gz
	rm -rf functionary_carl/demo-project/
	rm -f functionary_carl/package.2f89b927.link
	rm -f owner_alice/root.layout
