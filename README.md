## Historical Match-up Dashboard
In this section, we will create a full-featured Dash application that can be used to view historical football leagues data.

### We will use the following process to create / modify Dash applications:

1. Create/Update Layout - Figure out where components will be placed
2. Map Interactions with Other Components - Specify interaction in callback decorators
3. Wire in Data Model - Data manipulation to link interaction and render

## Setting Up Environment and Installing Dependencies
There are installation instructions in the Dash Documentation. Alternatively, we can create a virtualenv and pip install the requirements file.


Clone the project leagues_football
```
git clone ....
cd leagues_football

```


```
virtualenv -p /Library/Frameworks/Python.framework/Versions/3.8/bin/python3 dash-app
source dash-app/bin/activate

pip install -r requirements.txt --force-reinstall
```

Data is stored in an SQLite database
```
/data/soccer-stats.db
```


## Run Application
Let's run app.py to make sure everything works.

```
$ export DB_URI=sqlite:///data/soccer-stats.db && python app.py
* Running on http://0.0.0.0:8050/ (Press CTRL+C to quit)
* Restarting with stat
```


pip3 install --upgrade jupyter_core jupyter_client
