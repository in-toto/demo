import os
import sys
import shlex
import subprocess
import argparse
import time
from shutil import copyfile, copytree, rmtree

NO_PROMPT = False

def prompt_key(prompt):
  if NO_PROMPT:
    print("\n" + prompt)
    return
  inp = False
  while inp != "":
    try:
      inp = input("\n{} -- press any key to continue".format(prompt))
    except Exception:
      pass

def supply_chain():

  prompt_key("Define supply chain layout (Alice)")
  os.chdir("owner_alice")
  create_layout_cmd = "python create_layout.py"
  print(create_layout_cmd)
  subprocess.call(shlex.split(create_layout_cmd))

  prompt_key("Clone source code (Bob)")
  os.chdir("../functionary_bob")
  clone_cmd = ("in-toto-run"
                    " --verbose"
                    " --use-dsse"
                    " --step-name clone --products demo-project/foo.py"
                    " --signing-key bob -- git clone https://github.com/in-toto/demo-project.git")
  print(clone_cmd)
  subprocess.call(shlex.split(clone_cmd))

  prompt_key("Update version number (Bob)")
  update_version_start_cmd = ("in-toto-record"
                    " start"
                    " --verbose"
                    " --use-dsse"
                    " --step-name update-version"
                    " --signing-key bob"
                    " --materials demo-project/foo.py")

  print(update_version_start_cmd)
  subprocess.call(shlex.split(update_version_start_cmd))

  update_version = "echo 'VERSION = \"foo-v1\"\n\nprint(\"Hello in-toto\")\n' > demo-project/foo.py"
  print(update_version)
  subprocess.call(update_version, shell=True)

  update_version_stop_cmd = ("in-toto-record"
                    " stop"
                    " --verbose"
                    " --use-dsse"
                    " --step-name update-version"
                    " --signing-key bob"
                    " --products demo-project/foo.py")

  print(update_version_stop_cmd)
  subprocess.call(shlex.split(update_version_stop_cmd))

  copytree("demo-project", "../functionary_carl/demo-project")

  prompt_key("Package (Carl)")
  os.chdir("../functionary_carl")
  package_cmd = ("in-toto-run"
                 " --verbose"
                 " --use-dsse"
                 " --step-name package --materials demo-project/foo.py"
                 " --products demo-project.tar.gz"
                 " --signing-key carl --record-streams"
                 " -- tar --exclude '.git' -zcvf demo-project.tar.gz demo-project")
  print(package_cmd)
  subprocess.call(shlex.split(package_cmd))


  prompt_key("Create final product")
  os.chdir("..")
  copyfile("owner_alice/root.layout", "final_product/root.layout")
  copyfile("functionary_bob/clone.776a00e2.link", "final_product/clone.776a00e2.link")
  copyfile("functionary_bob/update-version.776a00e2.link", "final_product/update-version.776a00e2.link")
  copyfile("functionary_carl/package.2f89b927.link", "final_product/package.2f89b927.link")
  copyfile("functionary_carl/demo-project.tar.gz", "final_product/demo-project.tar.gz")


  prompt_key("Verify final product (client)")
  os.chdir("final_product")
  copyfile("../owner_alice/alice.pub", "alice.pub")
  verify_cmd = ("in-toto-verify"
                " --verbose"
                " --layout root.layout"
                " --layout-key alice.pub")
  print(verify_cmd)
  retval = subprocess.call(shlex.split(verify_cmd))
  print("Return value: " + str(retval))




  prompt_key("Tampering with the supply chain")
  os.chdir("../functionary_carl")
  tamper_cmd = "echo 'something evil' >> demo-project/foo.py"
  print(tamper_cmd)
  subprocess.call(tamper_cmd, shell=True)


  prompt_key("Package (Carl)")
  package_cmd = ("in-toto-run"
                 " --verbose"
                 " --use-dsse"
                 " --step-name package --materials demo-project/foo.py"
                 " --products demo-project.tar.gz"
                 " --signing-key carl --record-streams"
                 " -- tar --exclude '.git' -zcvf demo-project.tar.gz demo-project")
  print(package_cmd)
  subprocess.call(shlex.split(package_cmd))


  prompt_key("Create final product")
  os.chdir("..")
  copyfile("owner_alice/root.layout", "final_product/root.layout")
  copyfile("functionary_bob/clone.776a00e2.link", "final_product/clone.776a00e2.link")
  copyfile("functionary_bob/update-version.776a00e2.link", "final_product/update-version.776a00e2.link")
  copyfile("functionary_carl/package.2f89b927.link", "final_product/package.2f89b927.link")
  copyfile("functionary_carl/demo-project.tar.gz", "final_product/demo-project.tar.gz")


  prompt_key("Verify final product (client)")
  os.chdir("final_product")
  copyfile("../owner_alice/alice.pub", "alice.pub")
  verify_cmd = ("in-toto-verify"
                " --verbose"
                " --layout root.layout"
                " --layout-key alice.pub")

  print(verify_cmd)
  retval = subprocess.call(shlex.split(verify_cmd))
  print("Return value: " + str(retval))


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-n", "--no-prompt", help="No prompt.",
      action="store_true")
  parser.add_argument("-c", "--clean", help="Remove files created during demo.",
      action="store_true")
  args = parser.parse_args()

  if args.clean:
    files_to_delete = [
      "owner_alice/root.layout",
      "functionary_bob/clone.776a00e2.link",
      "functionary_bob/update-version.776a00e2.link",
      "functionary_bob/demo-project",
      "functionary_carl/package.2f89b927.link",
      "functionary_carl/demo-project.tar.gz",
      "functionary_carl/demo-project",
      "final_product/alice.pub",
      "final_product/demo-project.tar.gz",
      "final_product/package.2f89b927.link",
      "final_product/clone.776a00e2.link",
      "final_product/update-version.776a00e2.link",
      "final_product/untar.link",
      "final_product/root.layout",
      "final_product/demo-project",
    ]

    for path in files_to_delete:
      if os.path.isfile(path):
        os.remove(path)
      elif os.path.isdir(path):
        rmtree(path)

    sys.exit(0)
  if args.no_prompt:
    global NO_PROMPT
    NO_PROMPT = True


  supply_chain()

if __name__ == '__main__':
  main()
