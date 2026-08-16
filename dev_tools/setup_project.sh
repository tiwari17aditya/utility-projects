#!/bin/bash

# 1. Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    touch requirements.txt
fi

# 2. Create a valid, empty Jupyter Notebook if it doesn't exist
if [ ! -f main.ipynb ]; then
    echo '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":2}' > main.ipynb
fi

# 3. Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# 4 & 5. Activate, install ipykernel, and register kernel
echo "Installing ipykernel and linking to VS Code..."

if [ -d "venv/Scripts" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip
pip install ipykernel
python -m ipykernel install --user --name=venv --display-name "Python (venv)"

echo -e "\033[0;32mSetup Complete! Select 'Python (venv)' kernel when running main.ipynb.\033[0m"
