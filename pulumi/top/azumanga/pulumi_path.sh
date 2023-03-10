#! /bin/bash

MODULES_PATH="$(cd ../../ && pwd)"

if [[ "$VIRTUAL_ENV" == "" ]]; then
	echo "Activate the virtual env first" 1>&2
	exit 1
fi

SITE_PACKAGES="$(python -c 'import site; print([c for c in site.getsitepackages() if c.endswith("site-packages")][0])')"

echo "$MODULES_PATH" > "$SITE_PACKAGES/pulumi_modules.pth"
