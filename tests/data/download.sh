#!/bin/bash

# Create directory if it doesn't exist
mkdir -p "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Downloading sample notebooks for testing...${NC}"

# Download actor_critic.ipynb from TensorFlow docs repository
echo -e "Downloading actor_critic.ipynb..."
curl -s -L "https://raw.githubusercontent.com/tensorflow/docs/master/site/en/tutorials/reinforcement_learning/actor_critic.ipynb" -o "$(dirname "$0")/actor_critic.ipynb"

# Download a data science notebook
echo -e "Downloading pandas_tutorial.ipynb..."
curl -s -L "https://raw.githubusercontent.com/jakevdp/PythonDataScienceHandbook/master/notebooks/03.01-Introducing-Pandas-Objects.ipynb" -o "$(dirname "$0")/pandas_tutorial.ipynb"

# Download a deep learning notebook
echo -e "Downloading deep_learning_tutorial.ipynb..."
curl -s -L "https://raw.githubusercontent.com/pytorch/tutorials/gh-pages/_downloads/tensor_tutorial.ipynb" -o "$(dirname "$0")/tensor_tutorial.ipynb"

# Check if files were downloaded successfully
if [ -f "$(dirname "$0")/actor_critic.ipynb" ] && [ -f "$(dirname "$0")/pandas_tutorial.ipynb" ] && [ -f "$(dirname "$0")/tensor_tutorial.ipynb" ]; then
    echo -e "${GREEN}All notebooks downloaded successfully!${NC}"
    echo -e "Downloaded files:"
    ls -lh "$(dirname "$0")"/*.ipynb
else
    echo -e "Error: Failed to download one or more notebooks."
    exit 1
fi

echo -e "\n${YELLOW}To test the notebook distiller with these files, run:${NC}"
echo -e "nbdistill $(dirname "$0")/actor_critic.ipynb -o actor_critic_distilled.md"
echo -e "nbdistill $(dirname "$0")/pandas_tutorial.ipynb --chunk-size 4000 --estimate-tokens"
echo -e "nbdistill $(dirname "$0")/tensor_tutorial.ipynb --format json -o tensor_tutorial.json"
