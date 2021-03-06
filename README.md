# Lambda function to solve sudoku puzzles :1234:

The solver in `lambda_function.py` combines a constraint-model-based algorithm with backtracking

## Run locally

To run on your local machine, first prepare the environment

```bash
# build a virutal environment
python3.8 -m venv v-env
. ./v-env/bin/activate
pip install -r requirements.txt
pip install numpy
```

Then run one of the sudoku grid available in the `data/` folder

```bash
python lambda_function_local.py data/sudoku_04.txt
```

## Build the deployment package

A lot of issues have been reported when using numpy or pandas libraries in a lambda function.
To avoid running into conflicts and relying on which OS it is build, let's use docker.

1. Download the amazonlinux image from dockerhub and jump inside the container

```bash
docker pull amazonlinux
docker run -ti -v $PWD:/app amazonlinux
```

2. Install the relevant python (3.8) and pip version

```bash
yum -y install wget zip unzip tar gzip gcc openssl-devel bzip2-devel libffi-devel make
wget https://www.python.org/ftp/python/3.8.2/Python-3.8.2.tgz
tar xzf Python-3.8.2.tgz
cd Python-3.8.2
./configure --enable-optimizations
make altinstall
rm Python-3.8.2.tgz

curl -O https://bootstrap.pypa.io/get-pip.py
python3.8 get-pip.py --user
```

3. Build the deployment package

```bash
# Move where the repo has been mounted
cd ../app

# Create and activate a virtual environment
python3.8 -m venv v-env
. ./v-env/bin/activate

# Install the libraries (make sure there is no numpy here)
pip3.8 install -r requirements.txt

# Manually add Numpy to the site-packages
cd v-env/lib/python3.8/site-packages
wget https://files.pythonhosted.org/packages/cf/5d/e8198f11dd73a91f7bde15ca88a2b78913fa2b416ae2dc2a6aeafcf4c63d/numpy-1.18.4-cp38-cp38-manylinux1_x86_64.whl
unzip numpy-1.18.4-cp38-cp38-manylinux1_x86_64.whl
rm numpy-1.18.4-cp38-cp38-manylinux1_x86_64.whl

# Exit the virtual env
deactivate

# Package the function
zip -r9 ${OLDPWD}/function.zip .
cd ${OLDPWD}
zip -g -r function.zip lambda_function.py
```

4. Finally, copy your package function.zip from the container into your local machine

*In new terminal tab without closing the tab running the container*

```bash
# Check the id of you running container
docker ps
# Copy the package to local
docker cp <CONTAINER ID>:/app/function.zip .
```

## Upload the package to aws

If `function.zip` is smaller than 50M, the easiest would be to use the aws console, create a new Lambda function with a python 3.7 runtime and upload the zip file. If the file is larger then place it in a S3 bucket.

* To check the size of the file

```bash
du -hs function.zip
```

* To create a function with the CLI

```bash
aws lambda create-function --function-name SolveSudoku \
--zip-file fileb://function.zip --handler lambda_function.lambda_handler --runtime python3.7 \
--timeout 60 \
--role arn:aws:iam::XXXXXXXXXX:role/lambda-s3-role
```

* To update the function with the CLI

```bash
aws lambda update-function-code \
    --function-name  SolveSudoku \
    --zip-file fileb://function.zip 
```
