# IMPORTING MODULES

from googleapiclient.discovery import build
import pandas as pd
import pymongo
import streamlit as st
from PIL import Image
from pymongo import MongoClient 
from pymongo.server_api import ServerApi
import mysql.connector
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# MAKING CONNECTION
def make_connection():
    api_key = 'AIzaSyAjIU6fTQfKcnSsUkJ3-W-dQS8JBAGAmrU'
    youtube = build('youtube', 'v3', developerKey=api_key)
    return youtube


youtube = make_connection()

# GATHERING CHANNEL INFORMATION
def retrieve_channel_info(channel_id):
    request = youtube.channels().list(
        part = 'snippet, ContentDetails, Statistics', 
        id = channel_id, 
        maxResults = 50
    )
    response = request.execute()
    
    for i in range(0, len(response['items'])):
        data = {
            'channel_name' : response['items'][i]['snippet']['title'], 
            'channel_id' : response['items'][i]['id'], 
            'subscription_count' : response['items'][i]['statistics']['subscriberCount'], 
            'views' : response['items'][i]['statistics']['viewCount'], 
            'videos_count' : response['items'][i]['statistics']['videoCount'], 
            'channel_description' : response['items'][i]['snippet']['description'], 
            'playlist_id' : response['items'][i]['contentDetails']['relatedPlaylists']['uploads']
        }
    
    return data

# GATHERING PLAYLIST INFORMATION
def retrieve_playlist_info(channel_id):
    playlist_data = []
    next_page_token = None

    while True:
        try:
            request = youtube.playlists().list(
                part='snippet, contentDetails',
                channelId=channel_id,
                pageToken=next_page_token,
                maxResults=50,
            )
            response = request.execute()
            
        except Exception as e:
            print(f"Error making API request: {e}")
            break

        for item in response['items']:
            data = {
                'playlist_id': item['id'],
                'title': item['snippet']['title'],
                'channel_id': item['snippet']['channelId'],
                'channel_name': item['snippet']['channelTitle'],
                'publication_timestamp': item['snippet']['publishedAt'],
                'video_count': item['contentDetails']['itemCount']
            }
            playlist_data.append(data)
        
        next_page_token = response.get('nextPageToken')

        if not next_page_token:
            break

    return playlist_data

# GATHERING VIDEOIDS
def retrieve_video_ids(channel_id):
    retrieve_playlistid = retrieve_channel_info(channel_id)
    
    playlist_id =  retrieve_playlistid['playlist_id']
        
    next_page_token = None
    video_ids = []
    
    while True:
        request = youtube.playlistItems().list(
            part = 'snippet', 
            playlistId = playlist_id, 
            pageToken = next_page_token, 
            maxResults = 50
        )
        
        response = request.execute()
        
        for i in range(len(response['items'])):
            video_ids.append(response['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = response.get('nextPageToken')
        
        if not next_page_token:
            break
            
    return video_ids

# GATHERING VIDEO INFORMATION
def retrieve_video_info(video_ids):
    video_data = []
    
    for video_id in video_ids:

        request = youtube.videos().list(
            part = 'snippet, contentDetails, statistics', 
            id = video_id
        )
        response = request.execute()

        for item in response['items']:
            data = {
                'channel_name' : item['snippet']['channelTitle'], 
                'channel_id' : item['snippet']['channelId'], 
                'video_id' : item['id'], 
                'title' : item['snippet']['title'], 
                'tags' : item['snippet'].get('tags', []), 
                'thumbnail' : item['snippet']['thumbnails']['default']['url'], 
                'description' : item['snippet']['description'], 
                'publication_timestamp' : item['snippet']['publishedAt'], 
                'duration' : item['contentDetails']['duration'], 
                'views' : item['statistics']['viewCount'], 
                'likes' : item['statistics'].get('likeCount'), 
                'comments' : item['statistics'].get('commentCount'), 
                'favorite_count' : item['statistics']['favoriteCount'], 
                'definition' : item['contentDetails']['definition'], 
                'caption_status' : item['contentDetails']['caption']
            }
            video_data.append(data)


    return video_data

# GATHERING COMMENT INFORMATION
def retrieve_comment_info(video_ids):
    comment_data = []
    
    try:
        for video_id in video_ids:
            request = youtube.commentThreads().list(
                part = 'snippet', 
                videoId = video_id, 
                maxResults = 50
            )
            response = request.execute()
            
            for item in response['items']:
                data = {
                    'comment_id' : item['snippet']['topLevelComment']['id'], 
                    'video_id' : item['snippet']['videoId'], 
                    'comment_text' : item['snippet']['topLevelComment']['snippet']['textOriginal'], 
                    'comment_author' : item['snippet']['topLevelComment']['snippet']['authorDisplayName'], 
                    'comment_timestamp' : item['snippet']['topLevelComment']['snippet']['publishedAt']
                }
                
                comment_data.append(data)
                
    except:
        pass
    
    return comment_data

# CONNECTING MONGODB ATLAS
client = MongoClient('mongodb+srv://wolfx:wolfxkills@cluster0.xv8pe5i.mongodb.net/?retryWrites=true&w=majority')

db = client['Youtube_data']

# STORING DATA IN MONGODB
def channel_details(channel_id):
    chl_details = retrieve_channel_info(channel_id)
    plylst_details = retrieve_playlist_info(channel_id)
    vdo_ids = retrieve_video_ids(channel_id)
    vdo_details = retrieve_video_info(vdo_ids)
    comnt_details = retrieve_comment_info(vdo_ids)
    
    coll1 = db['channel_details']
    coll1.insert_one({
        'channel_information' : chl_details, 'playlist_information' : plylst_details, 'video_information' : vdo_details, 
        'comment_information' : comnt_details
    })
    
    return 'upload completed successfully'

# MIGRATING DATA FROM MONGODB TO SQL
def date_formatter(published_time_yt):
    parsed_timestamp = datetime.strptime(published_time_yt, '%Y-%m-%dT%H:%M:%SZ')
    formatted_timestamp = parsed_timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return formatted_timestamp

def duration_formatter(duration):
    duration = duration[2:]
    parsed_duration = timedelta()
    time_part = ''
    
    for char in duration:
        if char.isdigit():
            time_part += char
            
        else:
            if char == 'H':
                parsed_duration += timedelta(hours = int(time_part))
            elif char == 'M':
                parsed_duration += timedelta(minutes = int(time_part))
            elif char == 'S':
                parsed_duration += timedelta(seconds = int(time_part))
            time_part = ''
            
    return parsed_duration

# CHANNEL TABLE
def channels_table(cursor):
    drop_query = 'DROP TABLE IF EXISTS channels'
    cursor.execute(drop_query)
    mydb.commit()

    try:
        create_query = '''
        CREATE TABLE IF NOT EXISTS channels(
        channel_name VARCHAR(100), 
        channel_id VARCHAR(80) PRIMARY KEY, 
        subscription_count BIGINT, 
        views BIGINT, 
        videos_count INT, 
        channel_description TEXT, 
        playlist_id VARCHAR(50)
        )
        '''

        cursor.execute(create_query)
        mydb.commit()

    except mysql.connector.Error as err:
        if err.errno == 1062:
            print('channels tables already created')

        else:
            print(f'Error: {err}')

    db = client['Youtube_data']
    coll1 = db['channel_details']
    ch_list = []

    for ch_data in coll1.find({}, {'_id': 0, 'channel_information': 1}):
        ch_list.append(ch_data['channel_information'])
        
    df = pd.DataFrame(ch_list)
    
    for index, row in df.iterrows():
        insert_query = '''
        INSERT INTO channels(
        channel_name, 
        channel_id, 
        subscription_count, 
        views, 
        videos_count, 
        channel_description, 
        playlist_id
        )
        VALUES(%s, %s, %s, %s, %s, %s, %s)
        '''
        
        values = (
            row['channel_name'], 
            row['channel_id'], 
            row['subscription_count'], 
            row['views'], 
            row['videos_count'], 
            row['channel_description'], 
            row['playlist_id']
        )
        
        try: 
            cursor.execute(insert_query, values)
            mydb.commit()
            
        except mysql.connector.Error as err:
            if err.errno == 1062:  # MySQL duplicate entry code
                print('Channels values already inserted')
            
            else :
                print(f'Error: {err}')
                
# PLAYLIST TABLE
def playlists_table(cursor):
    drop_query = 'DROP TABLE IF EXISTS playlists'
    cursor.execute(drop_query)
    mydb.commit()
    
    
    try:
        create_query = '''
        CREATE TABLE IF NOT EXISTS playlists(
        playlist_id VARCHAR(100) PRIMARY KEY, 
        title VARCHAR(80), 
        channelid VARCHAR(100), 
        channelname VARCHAR(100), 
        publication_timestamp TIMESTAMP, 
        video_count INT
        )
        '''
        cursor.execute(create_query)
        mydb.commit()
        
    except mysql.connector.Error as err:
        if err.errno == 1062:
            print('Playlists values already inserted')
            
        else :
            print(f'Error: {err}')
        
    db = client['Youtube_data']
    coll1 = db['channel_details']
    ply_lists = []
    for ply_list in coll1.find({}, {'_id': 0, 'playlist_information': 1}):
        ply_list_data = ply_list['playlist_information']
        for i in range(len(ply_list_data)):
            ply_lists.append(ply_list_data[i])
            
    df = pd.DataFrame(ply_lists)
    for index, row in df.iterrows():
        publication_timestamp = date_formatter(row['publication_timestamp'])
        
        insert_query = '''
        INSERT INTO playlists(
        playlist_id, 
        title, 
        channelid, 
        channelname, 
        publication_timestamp, 
        video_count
        )
        VALUES(%s, %s, %s, %s, %s, %s)
        '''
        
        values = (
            row['playlist_id'], 
            row['title'], 
            row['channel_id'], 
            row['channel_name'], 
            publication_timestamp, 
            row['video_count']
        )
        try:
            cursor.execute(insert_query, values)
            mydb.commit()
        
        except mysql.connector.Error as err:
            if err.errno == 1062:
                print('playlists values already inserted')
            else:
                print(f'Error: {err}')
                
# VIDEO TABLE
def videos_table(cursor):
    drop_query = 'DROP TABLE IF EXISTS videos'
    cursor.execute(drop_query)
    mydb.commit()
    
    try:
        create_query = '''
        CREATE TABLE IF NOT EXISTS videos(
        channel_name VARCHAR(100), 
        channel_id VARCHAR(80), 
        video_id VARCHAR(80) PRIMARY KEY, 
        title VARCHAR(150), 
        tags TEXT, 
        thumbnail VARCHAR(225), 
        description TEXT, 
        publication_timestamp TIMESTAMP, 
        duration TIME, 
        views BIGINT, 
        likes BIGINT, 
        comments INT, 
        favorite_count INT, 
        definition VARCHAR(20), 
        caption_status VARCHAR(50)
        )
        '''
        
        cursor.execute(create_query)
        mydb.commit()
        
    except mysql.connector.Error as err:
        if err.errno == 1062:
            print('Videos table already created')
            
        else:
            print(f'Error: {err}')
            
    db  = client['Youtube_data']
    coll1 = db['channel_details']
    vdo_lists = []
    for vdo_list in coll1.find({}, {'_id': 0, 'video_information': 1}):
        vdo_list_data = vdo_list['video_information']
        for _ in range(len(vdo_list_data)):
            vdo_lists.append(vdo_list_data[_])
    
    df = pd.DataFrame(vdo_lists)
    
    for index, row in df.iterrows():
        publication_timestamp = date_formatter(row['publication_timestamp'])
        duration = duration_formatter(row['duration'])
        tags = ', '.join(map(str, row['tags'])) if row['tags'] else None
        
        insert_query = '''
        INSERT INTO videos(
        channel_name, 
        channel_id, 
        video_id, 
        title, 
        tags, 
        thumbnail, 
        description, 
        publication_timestamp, 
        duration, 
        views, 
        likes, 
        comments, 
        favorite_count, 
        definition, 
        caption_status
        )
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        values = (
            row['channel_name'], 
            row['channel_id'], 
            row['video_id'], 
            row['title'], 
            tags, 
            row['thumbnail'], 
            row['description'], 
            publication_timestamp, 
            duration, 
            row['views'], 
            row['likes'], 
            row['comments'], 
            row['favorite_count'], 
            row['definition'], 
            row['caption_status']
        )
        
        try:
            cursor.execute(insert_query, values)
            mydb.commit()
            
        except mysql.connector.Error as err:
            if err.errno == 1062:
                print('Video values already inserted')
            
            else:
                print(f'Error: {err}')
                
# COMMENT TABLE
def comments_table(cursor):
    drop_query = 'DROP TABLE IF EXISTS comments'
    cursor.execute(drop_query)
    mydb.commit()
    
    try:
        create_query = '''
        CREATE TABLE IF NOT EXISTS comments(
        comment_id VARCHAR(100) PRIMARY KEY, 
        video_id VARCHAR(80), 
        comment_text TEXT, 
        comment_author VARCHAR(150), 
        comment_timestamp TIMESTAMP
        )
        '''
        cursor.execute(create_query)
        mydb.commit()
        
    except mysql.connector.Error as err:
        if err.errno == 1062:
            print('Comments table already created')
            
        else:
            print(f'Error: {err}')
            
    db = client['Youtube_data']
    coll1 = db['channel_details']
    cmnt_lists = []
    for cmnt_list in coll1.find({}, {'_id': 0, 'comment_information': 1}):
        cmnt_list_data = cmnt_list['comment_information']
        for _ in range(len(cmnt_list_data)):
            cmnt_lists.append(cmnt_list_data[_])
            
    df = pd.DataFrame(cmnt_lists)
    
    for index, row in df.iterrows():
        comment_timestamp = date_formatter(row['comment_timestamp'])
        insert_query = '''
        INSERT INTO comments(
        comment_id, 
        video_id, 
        comment_text, 
        comment_author, 
        comment_timestamp
        )
        VALUES(%s, %s, %s, %s, %s)
        '''
        
        values = ( 
            row['comment_id'], 
            row['video_id'], 
            row['comment_text'], 
            row['comment_author'], 
            comment_timestamp
        )
        try:
            cursor.execute(insert_query, values)
            mydb.commit()
            
        except mysql.connector.Error as err:
            if err.errno == 1062:
                print('Comment values already inserted')
                
            else:
                print(f'Error: {err}')
                

# RETRIEVING INFORMATION FROM MONGODB
mydb = mysql.connector.connect(
            host = 'localhost', 
            user = 'root', 
            password = 'Abu#@7899#', 
            database = 'youtube_data', 
            port = '3306'
        )

cursor = mydb.cursor()
    
def channels_table_mdb():
    db = client['Youtube_data']
    coll1 = db['channel_details']
    ch_list = []

    for ch_data in coll1.find({}, {'_id': 0, 'channel_information': 1}):
        ch_list.append(ch_data['channel_information'])
        
    df = st.dataframe(ch_list)
    return df

def playlists_table_mdb():
    db = client['Youtube_data']
    coll1 = db['channel_details']
    ply_lists = []
    for ply_list in coll1.find({}, {'_id': 0, 'playlist_information': 1}):
        ply_list_data = ply_list['playlist_information']
        for i in range(len(ply_list_data)):
            ply_lists.append(ply_list_data[i])
            
    df = st.dataframe(ply_lists)
    return df

def videos_table_mdb():
    db  = client['Youtube_data']
    coll1 = db['channel_details']
    vdo_lists = []
    for vdo_list in coll1.find({}, {'_id': 0, 'video_information': 1}):
        vdo_list_data = vdo_list['video_information']
        for _ in range(len(vdo_list_data)):
            vdo_lists.append(vdo_list_data[_])
    
    df = st.dataframe(vdo_lists)
    return df

def comments_table_mdb():
    db = client['Youtube_data']
    coll1 = db['channel_details']
    cmnt_lists = []
    for cmnt_list in coll1.find({}, {'_id': 0, 'comment_information': 1}):
        cmnt_list_data = cmnt_list['comment_information']
        for _ in range(len(cmnt_list_data)):
            cmnt_lists.append(cmnt_list_data[_])
            
    df = st.dataframe(cmnt_lists)
    return df

                
# CALLING ALLTABLES                
def tables(cursor):
    channels_table(cursor)
    playlists_table(cursor)
    videos_table(cursor)
    comments_table(cursor)
    return 'All tables created successfully!'


#STREAMLIT
img1 = Image.open('Image\\yt_page.png')
st.set_page_config(page_title = 'Youtube Project', page_icon = img1, layout = 'wide')
st.title(':red[Youtube Data Harvesting and Warehousing]')

#NAVIGATION
home, search, data_insights = st.tabs(
    ['Home', 'Gathering Data', 'Data Insights']
)

with home:
    img2 = Image.open('Image\\yt.png')
    st.image(img2, width = 200)
    st.write('''YouTube is an American online video sharing and social media platform
    owned by Google. Accessible worldwide,[7] it was launched on February 14, 2005, 
    by Steve Chen, Chad Hurley, and Jawed Karim, three former employees of PayPal. 
    Headquartered in San Bruno, California, United States, it is the second most 
    visited website in the world, after Google Search. 
    '''
    )
    st.header('About Project')
    st.write('''
    This project aims to develop a user-friendly Streamlit application that utilizes the
    Google API to extract information from a YouTube channel using channelid, stores it in a 
    MongoDB database, migrates it to a SQL data warehouse, and enables users to find useful 
    insights from the data collected.
    '''
    )
    
with search:
    channel_id = st.text_input('Enter Channel Id')
    channels = channel_id.split(',')
    channels = [ch.strip() for ch in channels if ch]
    
    if st.button('Gather data', type = 'primary'):
        for channel in channels:
            ch_ids = []
            db = client['Youtube_data']
            coll1 = db['channel_details']
            for ch_lst in coll1.find({}, {'_id': 0, 'channel_information': 1}):
                ch_ids.append(ch_lst['channel_information']['channel_id'])
            if channel in ch_ids:
                st.success(f'Given Channel id {channel} already exists! please proceed further')
            
            else:
                output = channel_details(channel)
                st.success(output)
            
    if st.button(':red[Migrate data to sql]'):
        display = tables(cursor)
        st.success(display)
        
    show_table = st.selectbox(':black[Select tables]', 
                              ('Select an option', 'channels', 'playlists', 'videos', 'comments')
    )
    
    if show_table == 'channels':
        channels_table_mdb()
    
    elif show_table == 'playlists':
        playlists_table_mdb()
    
    elif show_table == 'videos':
        videos_table_mdb()
        
    elif show_table == 'comments':
        comments_table_mdb()
    
with data_insights:
    st.markdown(':red[Youtube Data]')    

    question = st.selectbox(
    ':red[How would you prefer to view the gathered information?]', (
        '1.All videos and their corresponding channels', 
        '2.Channels with most number of videos', 
        '3.Top 10 videos', 
        '4.Comments made on each video', 
        '5.Highly liked videos', 
        '6.Likes made on each video', 
        '7.Total views of each channels',
        '8.Channels published videos on 2022', 
        '9.Average video duration of each channel', 
        '10.Highly commented videos'
    ), 
        index = None, 
        placeholder = 'Select your question',
    )

    if question == '1.All videos and their corresponding channels':
        query = '''SELECT channel_name, title FROM videos'''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Channel Name', 'Video Title'])
        fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='red',
                    font = dict(color = 'white', size=15),
                    align=['left', 'center']),
        cells=dict(values=[df['Channel Name'], df['Video Title']],
                   fill_color='white',
                   font = dict(color = 'black', size=13),
                   align=['left', 'center']))
                             ]
                       )
        fig.update_layout(width=1225, height=700)
        st.write(fig)

    elif question == '2.Channels with most number of videos':
        query = '''SELECT channel_name, videos_count FROM channels ORDER BY videos_count DESC''' #DESC-descending
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Channel Name', 'Videos Count'])
        fig = px.bar(df, x = 'Channel Name', y = 'Videos Count',
                     hover_data = ['Channel Name', 'Videos Count'],
                     color = 'Videos Count',
                     color_continuous_scale = 'reds',
                     width = 1200,
                     height = 700,
                     title = 'High Videos Channel',
                     text_auto = True
                    )
        st.plotly_chart(fig)

    elif question == '3.Top 10 videos':
        query = '''SELECT channel_name, title, views FROM videos 
        WHERE views IS NOT NULL ORDER BY views DESC LIMIT 10
        '''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Channel Name', 'Video Name', 'View Count'])
        fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='red',
                    font = dict(color = 'white', size=15),
                    align=['left', 'center']),
        cells=dict(values=[df['Channel Name'], df['Video Name'], df['View Count']],
                   fill_color='white',
                   font = dict(color = 'black', size=13),
                   align=['left', 'center']))
                             ]
                       )
        fig.update_layout(width=1225, height=700)
        st.write(fig)

    elif question == '4.Comments made on each video':
        query = '''SELECT title, comments FROM videos WHERE comments IS NOT NULL'''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Video Name', 'Comments Count'])
        fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='red',
                    font = dict(color = 'white', size=15),
                    align=['left', 'center']),
        cells=dict(values=[df['Video Name'], df['Comments Count']],
                   fill_color='white',
                   font = dict(color = 'black', size=13),
                   align=['left', 'center']))
                             ]
                       )
        fig.update_layout(width=1225, height=700)
        st.write(fig)

    elif question == '5.Highly liked videos':
        query = '''SELECT channel_name, title, likes FROM videos 
        WHERE likes IS NOT NULL ORDER BY likes DESC
        '''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Channel Name', 'Video Name', 'Likes Count'])
        fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='red',
                    font = dict(color = 'white', size=15),
                    align=['left', 'center']),
        cells=dict(values=[df['Channel Name'], df['Video Name'], df['Likes Count']],
                   fill_color='white',
                   font = dict(color = 'black', size=13),
                   align=['left', 'center']))
                             ]
                       )
        fig.update_layout(width=1225, height=700)
        st.write(fig)

    elif question == '6.Likes made on each video':
        query = '''SELECT title, likes FROM videos'''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Video Name', 'Likes Count'])
        fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='red',
                    font = dict(color = 'white', size=15),
                    align=['left', 'center']),
        cells=dict(values=[df['Video Name'], df['Likes Count']],
                   fill_color='white',
                   font = dict(color = 'black', size=13),
                   align=['left', 'center']))
                             ]
                       )
        fig.update_layout(width=1225, height=700)
        st.write(fig)

    elif question == '7.Total views of each channels':
        query = '''SELECT channel_name, views FROM channels'''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Channel Name', 'Views Count'])
        fig = px.bar(df, x = 'Channel Name', y = 'Views Count',
                     hover_data = ['Channel Name', 'Views Count'],
                     color = 'Views Count',
                     color_continuous_scale = 'reds',
                     width = 1200,
                     height = 700,
                     title = 'Total Views of Channels',
                     text_auto = True, 
                    )
        st.plotly_chart(fig)

    elif question == '8.Channels published videos on 2022':
        query = '''SELECT channel_name, title, publication_timestamp FROM videos 
        WHERE EXTRACT(YEAR FROM publication_timestamp) = 2022
        '''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Channel Name', 'Video Name', 'Publication Timestamp'])
        fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='red',
                    font = dict(color = 'white', size=15),
                    align=['left', 'center']),
        cells=dict(values=[df['Channel Name'], df['Video Name'], df['Publication Timestamp']],
                   fill_color='white',
                   font = dict(color = 'black', size=13),
                   align=['left', 'center']))
                             ],
                       )
        fig.update_layout(width=1225, height=700)
        st.write(fig)

    elif question == '9.Average video duration of each channel':
        query = '''SELECT channel_name, AVG(TIME_TO_SEC(duration))/60 FROM videos GROUP BY channel_name'''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Channel Name', 'Average Duration'])
        df['Average Duration'] = pd.to_numeric(df['Average Duration'])
        fig = px.bar(df, x = 'Channel Name', y = 'Average Duration',
                     hover_data = ['Channel Name', 'Average Duration'],
                     color = 'Average Duration',
                     color_continuous_scale = 'reds',
                     width = 1200,
                     height = 700,
                     title = 'Average Duration of Channels (in Minutes)',
                     text_auto = True, 
                    )
        st.plotly_chart(fig)

    elif question == '10.Highly commented videos':
        query = '''SELECT channel_name, title, comments FROM videos 
        WHERE comments IS NOT NULL ORDER BY comments DESC
        '''
        cursor.execute(query)
        tuples = cursor.fetchall()
        df = pd.DataFrame(tuples, columns = ['Channel Name', 'Video Name', 'Comments Count'])
        fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color='red',
                    font = dict(color = 'white', size=15),
                    align=['left', 'center']),
        cells=dict(values=[df['Channel Name'], df['Video Name'], df['Comments Count']],
                   fill_color='white',
                   font = dict(color = 'black', size=13),
                   align=['left', 'center']))
                             ],
                       )
        fig.update_layout(width=1225, height=700)
        st.write(fig)