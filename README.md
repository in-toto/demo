# in-toto demo [![CI](https://github.com/in-toto/demo/actions/workflows/ci.yml/badge.svg)](https://github.com/in-toto/demo/actions/workflows/ci.yml)

In this demo, we will use in-toto to secure a software supply chain with a very
simple workflow.  Bob is a developer for a project, Carl packages the software, and
Alice oversees the project.  So, using in-toto's names for the parties, 
Alice is the project owner - she creates and signs the software supply chain
layout with her private key - and Bob and Carl are project functionaries -
they carry out the steps of the software supply chain as defined in the layout.

For the sake of demonstrating in-toto, we will have you run all parts of the
software supply chain.
This is, you will perform the commands on behalf of Alice, Bob and Carl as well
as the client who verifies the final product.


## Download and setup in-toto on \*NIX (Linux, OS X, ..)
__Virtual Environments (optional)__

We highly recommend installing `in-toto` and its dependencies in a
[`venv`](https://docs.python.org/3/library/venv.html) Python virtual
environment. Just copy-paste the following snippet to create a virtual
environment:

```bash
# Create the virtual environment
python -m venv in-toto-demo

# Activate the virtual environment
# This will add the prefix "(in-toto-demo)" to your shell prompt
source in-toto-demo/bin/activate
```

__Get demo files and install in-toto__
```bash
# Fetch the demo repo using git
git clone https://github.com/in-toto/demo.git

# Change into the demo directory
cd demo

# Install a compatible version of in-toto
pip install -r requirements.txt
```
*Note: If you are having troubles installing in-toto, make sure you have all
the system dependencies. See the [installation guide on
in-toto.readthedocs.io](https://in-toto.readthedocs.io/en/latest/installing.html)
for details.*

Inside the demo directory you will find four directories: `owner_alice`,
`functionary_bob`, `functionary_carl` and `final_product`. Alice, Bob and Carl
already have RSA keys in each of their directories. This is what you see:
```bash
tree  # If you don't have tree, try 'find .' instead
# the tree command gives you the following output
# .
# ├── README.md
# ├── final_product
# ├── functionary_bob
# │   ├── bob
# │   └── bob.pub
# ├── functionary_carl
# │   ├── carl
# │   └── carl.pub
# ├── owner_alice
# │   ├── alice
# │   ├── alice.pub
# │   └── create_layout.py
# ├── requirements.txt
# ├── run_demo.py
# └── run_demo_md.py
```

## Run the demo commands
Note: if you don't want to type or copy & paste commands and would rather watch
a script run through the commands, jump to [the last section of this document](#tired-of-copy-pasting-commands)

### Define software supply chain layout (Alice)
First, we will need to define the software supply chain layout. To simplify this
process, we provide a script that generates a simple layout for the purpose of
the demo.

In this software supply chain layout, we have Alice, who is the project
owner that creates the layout, Bob, who clones the project's repo and
performs some pre-packaging editing (update version number), and Carl, who uses
`tar` to package the project sources into a tarball, which
together with the in-toto metadata composes the final product that will
eventually be installed and verified by the end user.

```shell
# Create and sign the software supply chain layout on behalf of Alice
cd owner_alice
python create_layout.py
```
The script will create a layout, add Bob's and Carl's public keys (fetched from
their directories), sign it with Alice's private key and dump it to `root.layout`.
In `root.layout`, you will find that (besides the signature and other information)
there are three steps, `clone`, `update-version` and `package`, that
the functionaries Bob and Carl, identified by their public keys, are authorized
to perform.

### Clone project source code (Bob)
Now, we will take the role of the functionary Bob and perform the step
`clone` on his behalf, that is we use in-toto to clone the project repo from GitHub and
record metadata for what we do. Execute the following commands to change to Bob's
directory and perform the step.

```shell
cd ../functionary_bob
in-toto-run --step-name clone --use-dsse --products demo-project/foo.py --signing-key bob -- git clone https://github.com/in-toto/demo-project.git
```

Here is what happens behind the scenes:
 1. In-toto wraps the command `git clone https://github.com/in-toto/demo-project.git`,
 1. hashes the contents of the source code, i.e. `demo-project/foo.py`,
 1. adds the hash together with other information to a metadata file,
 1. signs the metadata with Bob's private key, and
 1. stores everything to `clone.[Bob's keyid].link`.

### Update version number (Bob)
Before Carl packages the source code, Bob will update
a version number hard-coded into `foo.py`. He does this using the `in-toto-record` command,
which produces the same link metadata file as above but does not require Bob to wrap his action in a single command.
So first Bob records the state of the files he will modify:

```shell
# In functionary_bob directory
in-toto-record start --step-name update-version --use-dsse --signing-key bob --materials demo-project/foo.py
```

Then Bob uses an editor of his choice to update the version number in `demo-project/foo.py`, e.g.:

```shell
sed -i.bak 's/v0/v1/' demo-project/foo.py && rm demo-project/foo.py.bak
```

And finally he records the state of files after the modification and produces
a link metadata file called `update-version.[Bob's keyid].link`.
```shell
# In functionary_bob directory
in-toto-record stop --step-name update-version --use-dsse --signing-key bob --products demo-project/foo.py
```

Bob has done his work and can send over the sources to Carl, who will create
the package for the user.

```shell
# Bob has to send the update sources to Carl so that he can package them
cp -r demo-project ../functionary_carl/
```

### Package (Carl)
Now, we will perform Carl’s `package` step by executing the following commands
to change to Carl's directory and create a package of the software project

```shell
cd ../functionary_carl
in-toto-run --step-name package --use-dsse --materials demo-project/foo.py --products demo-project.tar.gz --signing-key carl -- tar --exclude ".git" -zcvf demo-project.tar.gz demo-project
```

This will create another step link metadata file, called `package.[Carl's keyid].link`.
It's time to release our software now.


### Verify final product (client)
Let's first copy all relevant files into the `final_product` that is
our software package `demo-project.tar.gz` and the related metadata files `root.layout`,
`clone.[Bob's keyid].link`, `update-version.[Bob's keyid].link` and `package.[Carl's keyid].link`:
```shell
cd ..
cp owner_alice/root.layout functionary_bob/clone.776a00e2.link functionary_bob/update-version.776a00e2.link functionary_carl/package.2f89b927.link functionary_carl/demo-project.tar.gz final_product/
```
And now run verification on behalf of the client:
```shell
cd final_product
# Fetch Alice's public key from a trusted source to verify the layout signature
# Note: The functionary public keys are fetched from the layout
cp ../owner_alice/alice.pub .
in-toto-verify --layout root.layout --layout-key alice.pub
```
This command will verify that
 1. the layout has not expired,
 2. was signed with Alice’s private key,
<br>and that according to the definitions in the layout
 3. each step was performed and signed by the authorized functionary
 4. the recorded materials and products follow the artifact rules and
 5. the inspection `untar` finds what it expects.


From it, you will see the meaningful output `PASSING` and a return value
of `0`, that indicates verification worked out well:
```shell
echo $?
# should output 0
```

### Tampering with the software supply chain
Now, let’s try to tamper with the software supply chain.
Imagine that someone got a hold of the source code before Carl could package it.
We will simulate this by changing `demo-project/foo.py` on Carl's machine
(in `functionary_carl` directory) and then let Carl package and ship the
malicious code.

```shell
cd ../functionary_carl
echo something evil >> demo-project/foo.py
```
Carl thought that this is the genuine code he got from Bob and
unwittingly packages the tampered version of foo.py

```shell
in-toto-run --step-name package --use-dsse --materials demo-project/foo.py --products demo-project.tar.gz --key carl -- tar --exclude ".git" -zcvf demo-project.tar.gz demo-project
```
and ships everything out as final product to the client:
```shell
cd ..
cp owner_alice/root.layout functionary_bob/clone.776a00e2.link functionary_bob/update-version.776a00e2.link functionary_carl/package.2f89b927.link functionary_carl/demo-project.tar.gz final_product/
```

### Verifying the malicious product

```shell
cd final_product
in-toto-verify --layout root.layout --layout-key alice.pub
```
This time, in-toto will detect that the product `foo.py` from Bob's `update-version`
step was not used as material in Carl's `package` step (the verified hashes
won't match) and therefore will fail verification an return a non-zero value:
```shell
echo $?
# should output 1
```


### Wrapping up
Congratulations! You have completed the in-toto demo! This exercise shows a very
simple case in how in-toto can protect the different steps within the software
supply chain. More complex software supply chains that contain more steps can be
created in a similar way. You can read more about what in-toto protects against
and how to use it on [in-toto's Github page](https://in-toto.github.io/).

## Cleaning up and automated run through
### Clean slate
If you want to run the demo again, you can use the following script to remove all the files you created above.

```bash
cd .. # You have to be the demo directory
python run_demo.py -c
```

### Tired of copy-pasting commands?
The same script can be used to sequentially execute all commands listed above. Just change into the `demo` directory, run `python run_demo.py` without flags and observe the output.

```bash
# In the demo directory
python run_demo.py
```
