import praw
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import psycopg2

# connect to database
conn = psycopg2.connect(database="summary_db",
user="postgres",
password=os.environ.get('database_password'),
host="summary-db.chvnxb9rellm.us-east-2.rds.amazonaws.com",
port="5432")

class Scrape:
    '''
    Purpose:
        Represents an object of the desired subreddit to scrape and the desired keywords to search for
    Instance Variables: 
        a reddit object, a subreddit object, a list of keywords, and an applicable submissions list
    Methods:
        __init__: 
            takes in the subreddit of choice and a list of desired keyword, creates instance variables of those
        find_submissions: 
            finds top weekly 
    '''

    def __init__(self,subreddit_choice,keyword_list,keyword_string,request_id,timeframe):
        # connect to reddit API
        self.reddit = praw.Reddit(
        client_id=os.environ.get('reddit_api_id'),
        client_secret=os.environ.get('reddit_api_secret'),
        user_agent="scraper",
        username= os.environ.get('reddit_username'),
        password= os.environ.get('reddit_password'),
        )
        self.subreddit = self.reddit.subreddit(subreddit_choice)
        self.keywords = keyword_list
        self.keyword_string = keyword_string
        self.request_id = request_id
        self.timeframe = timeframe
        self.applicable_submissions = []
        self.plain_text = ''''''
        self.html = ''''''
    
    def find_submissions(self):
        # find all applicable submissions that contain desired keywords
        if self.keywords == []:
            # if the user doesn't have any keywords, just get the top ten posts from that subreddit
            for submission in self.subreddit.top(self.timeframe, limit=10):
                self.applicable_submissions.append(submission)
        else:
            for submission in self.subreddit.top(self.timeframe, limit=300):
                if any((keyword in submission.title.casefold() for keyword in self.keywords) or (keyword in submission.selftext.casefold() for keyword in self.keywords)):
                    self.applicable_submissions.append(submission)
                    if len(self.applicable_submissions) == 10:
                        break
        # what to do if there's no posts with selected keywords: just give them the top ten posts from that subreddit
        if self.applicable_submissions == []:
            for submission in self.subreddit.top(self.timeframe, limit=10):
                self.applicable_submissions.append(submission)
            self.html += '''
            <p>We couldn't find any posts with your keywords, so here's the top ten posts from {}!</p>
            '''.format(self.subreddit._path)
    
    def print_submissions(self):
        for submission in self.applicable_submissions:
            print("Title: ", submission.title)
            print("Contents: ", submission.selftext)
            print("URL: ", submission.url) 
            print()
    
    def create_plain_text(self): 
        for submission in self.applicable_submissions:
            if len(submission.selftext) > 300:
                submission_text = submission.selftext[:300] + '...'
            else:
                submission_text = submission.selftext
            submission_string = '''\'{}\': {}\n\n{}
            
            
            '''.format(submission.title, submission.url, submission_text)
            self.plain_text += submission_string

    def create_html(self): 
        for submission in self.applicable_submissions:
            if len(submission.selftext) > 300:
                submission_text = submission.selftext[:300] + '...'
            else:
                submission_text = submission.selftext
            if len(submission.comments) > 0:
                if len(submission.comments[0].body) > 300:
                    top_comment = submission.comments[0].body[:300] + '...'
                else:
                    top_comment = submission.comments[0].body
                submission_html = '''
                <div class="submission">
                <h2><a href={}>{}</a> ({} upvotes)</h2>
                <p>{}</p>
                <h3>Top comment:</h3>
                <p>{}</p><br>
                </div>
                '''.format(submission.url, submission.title, submission.score, submission_text, top_comment)
                self.html += submission_html
            else:
                submission_html = '''
                <div class="submission">
                <h2><a href={}>{}</a> ({} upvotes)</h2>
                <p>{}</p>
                </div>
                '''.format(submission.url, submission.title, submission.score, submission_text)
                self.html += submission_html

    def send_email(self,receiver_email):
        sender_email = os.environ.get('bot_gmail')
        password = os.environ.get('bot_password')

        if self.timeframe == 'day':
            time = 'Daily'
        elif self.timeframe == 'week':
            time = 'Weekly'
        else: 
            time = 'Monthly'

        message = MIMEMultipart("alternative")
        message["Subject"] = "{} Summary Report of {}".format(time, self.subreddit._path)
        message["From"] = sender_email
        message["To"] = receiver_email

        text = self.plain_text

        if self.keywords == []:
            with open("subrsum\\email_templates\\no_keywords.html", 'r') as html_file:
                html = html_file.read().format(time.lower(), self.subreddit._path, self.html, self.request_id)
        else:
            with open("subrsum\\email_templates\\keywords.html", 'r') as html_file:
                html = html_file.read().format(time.lower(), self.subreddit._path, self.keyword_string, self.html, self.request_id)

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)

        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string()
            )
    
    def email_process(self, email):
        self.find_submissions()
        self.create_plain_text()
        self.create_html()
        self.send_email(email)
