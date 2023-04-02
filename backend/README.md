# Translation Plugin

Google Chrome extension that utilizes the LSFB corpus of unamur to automatically provide translations for text highlighted in the browser page. It currently supports French to Francophone Belgium sign language translations.

### Install extension
  1. Download and unzip this repository.
  2. Go to [chrome://extensions](chrome://extensions) in your Chrome browser.
  3. Check the **Developer mode** box on the top right-hand corner of the page.
  4. Click the **Load unpacked extension** button and select your downloaded repository from the file-selection pop-up window.

*Note: After making edits to the code, make sure to reload the extensions page to see the new changes.*

### start flask serveur
Go to the folder that containts "app.py"
#### windows
create a virtual env : py -m venv env
1. Activate the virtual env : env\Scripts\activate 
2. install requirements : pip install - r requirements.txt
3. set FLASK_APP=app.py  
3. run : flask run
#### linux

### start docker
download docker on your machine
1. Go to LSFB/Translate/backend/app
2. run : docker build -t givemeasign:latest .
3. run : docker run -p 5000:5000 givemeasign:latest