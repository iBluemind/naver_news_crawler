from pymongo import MongoClient
from config import DATABASE_HOST, DATABASE_NAME, DATABASE_PORT, DATABASE_PASSWORD, DATABASE_USERNAME


connection = MongoClient('mongodb://{}:{}@{}:{}'.format(DATABASE_USERNAME, DATABASE_PASSWORD,
                                                        DATABASE_HOST, DATABASE_PORT))
database = connection.get_database(DATABASE_NAME)

articles = database.get_collection('articles')
comments_count_history = database.get_collection('comments_count_histories')
comments = database.get_collection('comments')
