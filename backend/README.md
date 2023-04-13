# Translation Plugin

Google Chrome extension that utilizes the LSFB corpus of unamur to automatically provide translations for text highlighted in the browser page. It currently supports French to Francophone Belgium sign language translations.

### Install extension via Chrome - webstore
  1. Install the extension [https://chrome.google.com/webstore/search/lsfbtranslate?hl=]
  2. Or search "LSFBtranslate" on [https://chrome.google.com/webstore/category/extensions]

### Install extension on local
  1. Download and unzip this repository.
  2. Go to [chrome://extensions](chrome://extensions) in your Chrome browser.
  3. Check the **Developer mode** box on the top right-hand corner of the page.
  4. Click the **Load unpacked extension** button and select your downloaded repository from the file-selection pop-up window.

*Note: After making edits to the code, make sure to reload the extensions page to see the new changes.*

### start docker
download docker on your machine
1. Go to LSFB/Translate/backend/app
2. run : docker build -t givemeasign:latest .
3. run : docker run -p 5000:5000 givemeasign:latest

### start flask serveur
#### windows
Go to the folder that containts "app.py"
create a virtual env : py -m venv env
1. Activate the virtual env : env\Scripts\activate 
2. install requirements : pip install - r requirements.txt
3. set FLASK_APP=app.py  
3. run : flask run

### How to use 
#### Translate a word

#### C