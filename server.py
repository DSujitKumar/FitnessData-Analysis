from io import BytesIO
import logging
import flask
import json
import httplib2
import time
import webbrowser
import requests
import urllib.request
import pandas as pd
from datetime import datetime
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow
from datetime import timedelta

#Initializing the Flask and error log fiel
app = flask.Flask(__name__)
# file_handler = logging.FileHandler('server.log')
# app.logger.addHandler(file_handler)
# app.logger.setLevel(logging.INFO)

# Copy your credentials from the Google Developers Console
CLIENT_ID = '404865027459-jndn7t7a6mo94cd8sfb85pk21utgo3n8.apps.googleusercontent.com'
CLIENT_SECRET = 'ESmECqbbLh1mpaFCHU_IgxYA'
Sdate = str((datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d"))
# Check https://developers.google.com/fit/rest/v1/reference/users/dataSources/datasets/get
# for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/fitness.activity.read https://www.googleapis.com/auth/fitness.blood_glucose.read https://www.googleapis.com/auth/fitness.blood_pressure.read https://www.googleapis.com/auth/fitness.body_temperature.read https://www.googleapis.com/auth/fitness.location.read https://www.googleapis.com/auth/fitness.nutrition.read https://www.googleapis.com/auth/fitness.oxygen_saturation.read https://www.googleapis.com/auth/fitness.body.read https://www.googleapis.com/auth/fitness.reproductive_health.read'
#OAUTH_SCOPE ='https://www.googleapis.com/auth/fitness.activity.read'
# DATA SOURCE
DATA_SOURCE = "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"

# The ID is formatted like: "startTime-endTime" where startTime and endTime are
# 64 bit integers (epoch time with nanoseconds).

#++++++++++++++++++++ Exploring Time Data Start ++++++++++++++++++++++++
now = datetime.now()-timedelta(days=1)
to_day=(datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
last_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
T_y_mid= int(time.mktime(last_day.timetuple())) * 1000000000
T_T_mid= int(time.mktime(to_day.timetuple())) * 1000000000
T_now= int(time.mktime(datetime.now().timetuple())) * 1000000000
DATA_SET = str(T_y_mid)+"-"+str(T_T_mid)
#DATA_SET = "1522371700792119516-"+str(T_now)
#DATA_SET = "1560865682774454593-"+str(T_now)

#++++++++++++++++++++ Exploring Time Data Stop ++++++++++++++++++++++++

# Redirect URI for installed apps
REDIRECT_URI = 'http://127.0.0.1:3210/oauth2callback'

@app.route("/",methods=["GET"])
def auth1():
	flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, redirect_uri=REDIRECT_URI)
	authorize_url = flow.step1_get_authorize_url()
	webbrowser.open_new(authorize_url)
	#return "This is Only The user"
@app.route("/oauth2callback",methods=["GET"])
def assign():
	flow = OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE, redirect_uri=REDIRECT_URI)
	c = flask.request.args.get("code")
	print("This is the code which we get from thr server    ",c)
	code=c.strip()
	credentials = flow.step2_exchange(code)
	http = httplib2.Http()
	http = credentials.authorize(http)
	fitness_service = build('fitness', 'v1', http=http)
	weightData=fetchData("derived:com.google.weight:com.google.android.gms:merge_weight",fitness_service)
	saveSpeed(weightData,'Weight')#saveData(weightData,'weight.txt')
	calories=fetchData('derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended',fitness_service)
	saveSpeed(calories,'Calories')#saveData(calories,'calories.txt')
	dist=fetchData('derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta',fitness_service)
	saveSpeed(dist,'Distance')#saveData(dist,'distance.txt')
	heightData=fetchData("derived:com.google.height:com.google.android.gms:merge_height",fitness_service)
	saveSpeed(heightData,'Heart')#saveData(heightData,'height.txt')
	heartData=fetchData('derived:com.google.heart_minutes:com.google.android.gms:merge_heart_minutes',fitness_service)
	saveSpeed(heartData,'Heart')#saveData(heartData,'heart.txt')
	locationData=fetchData('derived:com.google.location.sample:com.google.android.gms:merge_location_samples',fitness_service)
	saveData(locationData,'Location.txt')
	#++++++++++Derriving the Location++++++++++++++++++++++++++
	speedData=fetchData("derived:com.google.speed:com.google.android.gms:merge_speed",fitness_service)
	
	saveSpeed(speedData,'Speed')#saveData(speedData,'speed.txt')
	#activity=fetchData("derived:com.google.active_minutes:com.google.android.gms:merge_active_minutes",fitness_service)
	#activity=fetchData("derived:com.google.activity.segment:com.google.android.apps.fitness:session_activity_segment",fitness_service) # Not a single value is present
	activityData=fetchData("derived:com.google.activity.segment:com.google.android.gms:merge_activity_segments",fitness_service)
	
	saveActivity(activityData,'Activity')#saveData(activityData,'activity.txt')
	steps=fetchData(DATA_SOURCE,fitness_service)
	saveActivity(steps,'Steps')
	stps="Data Cleared..."
	return (stps)
def nanoseconds(nanotime):
    """
    Convert epoch time with nanoseconds to human-readable.
    """
    dt = datetime.fromtimestamp(nanotime // 1000000000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')
##===============Saving all data into files==================
def saveData(data,path):
	with open('./data/'+path, 'w') as inputfile:
		json.dump(data, inputfile)
	pass
def fetchData(dataStreamId,fitness_service):
	dist=fitness_service.users().dataSources().datasets().get(userId='me', dataSourceId=dataStreamId, datasetId=DATA_SET).execute()
	return dist
## ==================Saving Data into CSV file ==================
def saveActivity(activityData,path):
	S_time,E_time,Type=[],[],[]
	stps={}
	for i in range(len(activityData["point"])):
		last_point = activityData["point"][i]
		S_time.append(nanoseconds(int(last_point.get("startTimeNanos", 0))))
		E_time.append(nanoseconds(int(last_point.get("endTimeNanos", 0))))
		Type.append(last_point["value"][0].get("intVal", None))
		stps.update({last_point["value"][0].get("intVal", None):[nanoseconds(int(last_point.get("startTimeNanos", 0))),nanoseconds(int(last_point.get("endTimeNanos", 0)))]})
	#print(S_time)
	adf = pd.DataFrame({'Start Time':S_time,'End Time':E_time,path:Type})
	#print(heartdf.head())
	adf.to_csv('./data/'+path+' '+Sdate+'.csv', columns=['Start Time','End Time',path], header=True,index = False)
	with open('./data/json/'+path+" "+Sdate+'.json', 'w') as outfile:
		json.dump(stps,outfile)

def saveSpeed(speedData,path):
  S_time,E_time,Speed=[],[],[]
  stps={}
  for i in range(len(speedData["point"])):
    last_point = speedData["point"][i]
    S_time.append(nanoseconds(int(last_point.get("startTimeNanos", 0))))
    E_time.append(nanoseconds(int(last_point.get("endTimeNanos", 0))))
    Speed.append(last_point["value"][0].get("fpVal", None))
    stps.update({last_point["value"][0].get("fpVal", None):[nanoseconds(int(last_point.get("startTimeNanos", 0))),nanoseconds(int(last_point.get("endTimeNanos", 0)))]})
  #print(S_time)
  adf = pd.DataFrame({'Start Time':S_time,'End Time':E_time,path:Speed})
  #print(heartdf.head())
  adf.to_csv('./data/'+path+' '+Sdate+'.csv', columns=['Start Time','End Time',path], header=True,index = False)
  with open('./data/json/'+path+" "+Sdate+'.json', 'w') as outfile:
  	json.dump(stps,outfile)
## =================== End of Saving Data =======================
if __name__ == "__main__":
	app.debug=True
	app.run(port=3210)
	# Point of entry in execution mode:
	
	
	print("Starting API services")

