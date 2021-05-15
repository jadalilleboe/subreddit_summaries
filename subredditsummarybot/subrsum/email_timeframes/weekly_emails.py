import sys
import os
import psycopg2

sys.path.append('C:\\Users\\16512\\OneDrive\\Desktop\\subredditsummarybot\\subrsum')
import subreddit_scraper

# connect to database
conn = psycopg2.connect(database="summary_db",
user="postgres",
password=os.environ.get('database_password'),
host="summary-db.chvnxb9rellm.us-east-2.rds.amazonaws.com",
port="5432")

cursor = conn.cursor()
def send_weekly_emails():
    cursor.execute("SELECT * FROM SummaryRequests WHERE Timeframe='week'")
    results = cursor.fetchall()
    
    for i in results:
        id = i[0]
        email = i[1]
        subreddit = i[2]
        keyword_string = i[3]
        timeframe = i[4]
        if keyword_string == '':
            keyword_list = []
        else:
            keyword_list = i[3].split(',')
            for i in range(len(keyword_list)):
                keyword_list[i] = keyword_list[i].strip()
                keyword_list[i] = keyword_list[i].casefold()

        scrape = subreddit_scraper.Scrape(subreddit, keyword_list, keyword_string, id, timeframe)
        scrape.email_process(email)

send_weekly_emails()