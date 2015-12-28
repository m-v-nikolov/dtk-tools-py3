Install sphinx to build the docs:
```
pip install sphinx
```

Build the docs, which should result in a bunch of files in a temporary `_build/html` folder:
```
make html
```

Set up `deploy.sh` script as described in the [`git-directory-deploy`](https://github.com/X1011/git-directory-deploy) README:
- set permissions (`chmod +x deploy.sh`)
- ensure defaults are appropriate (deploy_directory, deploy_branch, default_username, default_email)

Deploy the generated html to the `gh-pages` branch:
```
./deploy.sh
```

The resulting documentation appears at http://edwenger.github.io/dtk-tools
