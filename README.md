# Youtube-data-harvesting-and-warehousing-project

# Introduction

YouTube Data Harvesting and Warehousing is a project that aims to allow users to access and analyze data from multiple YouTube channels. The project utilizes SQL, MongoDB, and Streamlit to create a user-friendly application that allows users to retrieve, store, and query YouTube channel and video data.

Project Overview

The YouTube Data Harvesting and Warehousing project consists of the following components:

Streamlit Application: A user-friendly UI built using Streamlit library, allowing users to interact with the application and perform data retrieval and analysis tasks.
YouTube API Integration: Integration with the YouTube API to fetch channel and video data based on the provided channel ID.
MongoDB Data Lake: Storage of the retrieved data in a MongoDB database, providing a flexible and scalable solution for storing unstructured and semi-structured data.
SQL Data Warehouse: Migration of data from the data lake to a SQL database, allowing for efficient querying and analysis using SQL queries.
Data Visualization: Presentation of retrieved data using Streamlit's data visualization features, enabling users to analyze the data through charts and graphs.

# Installation and Setup

To run the YouTube Data Harvesting and Warehousing project, follow these steps:

1.Install Python: Install the Python programming language on your machine.
2.Install Required Libraries: Install the necessary Python libraries using pip or conda package manager. Required libraries include Streamlit, MongoDB driver, mysql connector, myslql, Pandas, and Matplotlib.
3.Set Up Google API: Set up a Google API project and obtain the necessary API credentials for accessing the YouTube API.
4.Configure Database: Set up a MongoDB database and SQL database (MySQL) for storing the data.
5.Configure Application: Update the configuration file or environment variables with the necessary API credentials and database connection details.
6.Run the Application: Launch the Streamlit application using the command-line interface.

# Usage

step1: Enter a YouTube channel ID to retrieve data for that channel.
step2: Store the retrieved data in the MongoDB data lake.
step3: Collect and store data for multiple YouTube channels in the data lake.
step4: Select a channel and migrate its data from the data lake to the SQL data warehouse.
step5: Search and retrieve data from the SQL database using various search options.
step6: Perform data analysis and visualization using the provided features.

# Conclusion

The YouTube Data Harvesting and Warehousing project provides a powerful tool for retrieving, storing, and analyzing YouTube channel and video data. By leveraging SQL, MongoDB, and Streamlit, users can easily access and manipulate YouTube data in a user-friendly interface. The project offers flexibility, scalability, and data visualization capabilities, empowering users to gain insights from the vast amount of YouTube data available.
