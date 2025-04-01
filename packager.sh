#!/bin/bash

# Define the package directories
GET_MEMES_PACKAGE_DIR="./get-memes/package"
SCRAPE_MEMES_PACKAGE_DIR="./scrape-memes/package"
GATHERER_BOT_PACKAGE_DIR="./gatherer-bot/package"

# Define the zip files
GET_MEMES_ZIP_FILE="get-memes-deployment-package.zip"
SCRAPE_MEMES_ZIP_FILE="scrape-memes-deployment-package.zip"
GATHERER_BOT_ZIP_FILE="gatherer-bot-deployment-package.zip"

# Create a fresh get-memes package directory
rm -rf $GET_MEMES_PACKAGE_DIR
mkdir -p $GET_MEMES_PACKAGE_DIR

# Install Python dependencies into the get-memes package directory
pip install --no-cache-dir -r ./get-memes/requirements.txt --target $GET_MEMES_PACKAGE_DIR

# Package the get-memes code
cd $GET_MEMES_PACKAGE_DIR
rm $GET_MEMES_ZIP_FILE 
zip -r ../$GET_MEMES_ZIP_FILE .
cd ..
zip $GET_MEMES_ZIP_FILE lambda_function.py

cd ..


# Create a fresh scrape-memes package directory
rm -rf $SCRAPE_MEMES_PACKAGE_DIR
mkdir -p $SCRAPE_MEMES_PACKAGE_DIR

# Install Python dependencies into the scrape-memes package directory
pip install --no-cache-dir -r ./scrape-memes/requirements.txt --target $SCRAPE_MEMES_PACKAGE_DIR

# Package the scrape-memes code
cd $SCRAPE_MEMES_PACKAGE_DIR
rm $SCRAPE_MEMES_ZIP_FILE
zip -r ../$SCRAPE_MEMES_ZIP_FILE .
cd ..
zip $SCRAPE_MEMES_ZIP_FILE lambda_function.py

cd ..

# Create a fresh gatherer-bot package directory
rm -rf $GATHERER_BOT_PACKAGE_DIR
mkdir -p $GATHERER_BOT_PACKAGE_DIR

# Install Python dependencies into the gatherer-bot package directory
pip install --no-cache-dir -r ./gatherer-bot/requirements.txt --target $GATHERER_BOT_PACKAGE_DIR

# Package the gatherer-bot code
cd $GATHERER_BOT_PACKAGE_DIR
rm $GATHERER_BOT_ZIP_FILE
zip -r ../$GATHERER_BOT_ZIP_FILE .
cd ..
zip $GATHERER_BOT_ZIP_FILE lambda_function.py

echo "- Created $GATHERER_BOT_ZIP_FILE, $GET_MEMES_ZIP_FILE and $SCRAPE_MEMES_ZIP_FILE successfully! -"
