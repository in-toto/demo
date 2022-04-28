"""
<Program Name>
  run_demo_md.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  Jul 17, 2019

<Purpose>
  Provides a script that extracts the demo code snippets from README.md and
  runs them in a shell, raising `SystemExit`, if the output is not as expected.

  virtualenv setup and installation of in-toto, as described in the demo
  instructions, is not performed by this script and must be done before running
  it. Snippets are run in a temporary directory, which is removed afterwards.

  NOTE: Currently, the script runs all snippets marked as `shell` snippets (see
  `SNIPPET_PATTERN`). To exclude a snippet from execution it must be marked as
  something else (e.g. `bash` to get the same syntax highlighting).

"""
import os
import re
import shutil
import sys
import tempfile
import difflib
import subprocess

# The file pointed to by `INSTRUCTIONS_FN` contains `shell` code snippets that
# may be extracted using the regex defined in `SNIPPET_PATTERN`, and executed
# to generate a combined stdout/stderr equal to `EXPECTED_STDOUT`.
INSTRUCTIONS_FN = "README.md"
SNIPPET_PATTERN = r"```shell\n([\s\S]*?)\n```"

EXPECTED_STDOUT = \
"""+ cd owner_alice
+ python create_layout.py
Created demo in-toto layout as "root.layout".
+ cd ../functionary_bob
+ in-toto-run --step-name clone --products demo-project/foo.py --key bob -- git clone https://github.com/in-toto/demo-project.git
+ in-toto-record start --step-name update-version --key bob --materials demo-project/foo.py
+ sed -i.bak s/v0/v1/ demo-project/foo.py
+ rm demo-project/foo.py.bak
+ in-toto-record stop --step-name update-version --key bob --products demo-project/foo.py
+ cp -r demo-project ../functionary_carl/
+ cd ../functionary_carl
+ in-toto-run --step-name package --materials demo-project/foo.py --products demo-project.tar.gz --key carl -- tar --exclude .git -zcvf demo-project.tar.gz demo-project
+ cd ..
+ cp owner_alice/root.layout functionary_bob/clone.776a00e2.link functionary_bob/update-version.776a00e2.link functionary_carl/package.2f89b927.link functionary_carl/demo-project.tar.gz final_product/
+ cd final_product
+ cp ../owner_alice/alice.pub .
+ in-toto-verify --layout root.layout --layout-key alice.pub
+ echo 0
0
+ cd ../functionary_carl
+ echo something evil
+ in-toto-run --step-name package --materials demo-project/foo.py --products demo-project.tar.gz --key carl -- tar --exclude .git -zcvf demo-project.tar.gz demo-project
+ cd ..
+ cp owner_alice/root.layout functionary_bob/clone.776a00e2.link functionary_bob/update-version.776a00e2.link functionary_carl/package.2f89b927.link functionary_carl/demo-project.tar.gz final_product/
+ cd final_product
+ in-toto-verify --layout root.layout --layout-key alice.pub
(in-toto-verify) RuleVerificationError: 'DISALLOW *' matched the following artifacts: ['demo-project/foo.py']
Full trace for 'expected_materials' of item 'package':
Available materials (used for queue):
['demo-project/foo.py']
Available products:
['demo-project.tar.gz']
Queue after 'MATCH demo-project/* WITH PRODUCTS FROM update-version':
['demo-project/foo.py']

+ echo 1
1
"""

# Setup a test directory with all necessary demo files and change into it. This
# lets us easily clean up all the files created during the demo eventually.
demo_dir = os.path.dirname(os.path.realpath(__file__))
tmp_dir = os.path.realpath(tempfile.mkdtemp())
test_dir = os.path.join(tmp_dir, os.path.basename(demo_dir))
shutil.copytree(demo_dir, test_dir)
os.chdir(test_dir)

# Wrap test code in try/finally to always tear down test directory and files
try:
  # Extract all shell code snippets from demo instructions
  with open(INSTRUCTIONS_FN) as fp:
    readme = fp.read()
  snippets = re.findall(SNIPPET_PATTERN, readme)

  # Create script from all snippets, with shell xtrace mode (set -x) for
  # detailed output and make sure that it has the expected prefix (PS4='+ ')
  script = "PS4='+ '\nset -x\n{}".format("\n".join(snippets))

  # Execute script in one shell so we can run commands like `cd`
  # NOTE: Would be nice to use `in_toto.process.run_duplicate_streams` to show
  # output in real time, but the method does not support the required kwargs.
  proc = subprocess.Popen(
      ["/bin/sh", "-c", script],
      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
      universal_newlines=True)
  stdout, _ = proc.communicate()

  # Fail if the output is not what we expected
  if stdout != EXPECTED_STDOUT:
    difflist = list(difflib.Differ().compare(
        EXPECTED_STDOUT.splitlines(),
        stdout.splitlines()))
    raise SystemExit(
        "#### DIFFERENCE:\n\n{}\n\nDemo test failed due to unexpected output "
        "(see above). :(".format("\n".join(difflist)))

  print("{}\nDemo test ran as expected. :)".format(stdout))

finally:
  # Change back to where we were in the beginning and tear down test directory
  os.chdir(demo_dir)
  shutil.rmtree(test_dir)
