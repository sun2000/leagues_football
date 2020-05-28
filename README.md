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
git clone https://github.com/sun2000/leagues_football.git
cd leagues_football
```

Data is stored in an SQLite database
```
/data/soccer-stats.db
```

Install python 3.6.10 with pyenv
```
pyenv install 3.6.10
```

Create a virtualenv with python version 3.6.10
```
pyenv virtualenv 3.6.10 apps3.6.10
eval "$(pyenv init -)"
pyenv activate apps3.6.10
pip install -r requirements.txt --force-reinstall
```


## Run Application
Let's run app.py to make sure everything works.

```
$ export DB_URI=sqlite:///data/soccer-stats.db && python app.py
* Running on http://0.0.0.0:8050/ (Press CTRL+C to quit)
* Restarting with stat
```


Update packages if you want to use jupyter notebook for dev
```
pip3 install --upgrade jupyter_core jupyter_client
jupyter notebook
```
