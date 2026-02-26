# projectdatabases
Programming Project Databases UAntwerpen


# Run for now:
python3 -m pip install -r requirements.txt
# To run the project, use:
See the folders backend and frontend and open 2 terminals, one for each. In the backend terminal, run:


# Terminal 1 (backend):

cd backend \
python3 -m venv venv \
source venv/bin/activate \
python main.py 

# Terminal 2 (frontend):

cd frontend \
npm install \
npm run dev 

# Testsing with Pytest

Alle tests runnen

cd backend\
pytest -q\
For pycharm check to see if working directory is set to projectdatabases/backend
# Results:
you should see that if you open http://localhost:5173/ in your browser, you will see the frontend of the project.\
You can do f12 and navigate to the console to see the logs of the backend and frontend. You can also navigate to http://localhost:5000/ to see the backend logs.