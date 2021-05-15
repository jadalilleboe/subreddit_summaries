from flask import Blueprint, render_template, request, url_for, redirect, flash, session, jsonify
import praw
import os.path
import os
import psycopg2
from psycopg2.extensions import AsIs
import uuid

# connect to database
conn = psycopg2.connect(database="summary_db",
user="postgres",
password=os.environ.get('database_password'),
host="summary-db.chvnxb9rellm.us-east-2.rds.amazonaws.com",
port="5432")

bp = Blueprint('subrsum', __name__)

@bp.route('/')
def home():
    return render_template('home.html', summaries=session.items())

@bp.route('/about')
def about():
    return render_template('about.html')


@bp.route('/confirmation-page', methods=['GET', 'POST'])
def confirmation_page():
    
    if request.method == "POST":
        cursor = conn.cursor()
        email = request.form['user_email']
        subreddit_choice = request.form['subreddit']
        keywords = request.form['keywords']
        timeframe = request.form['timeframe']
        request_id = str(uuid.uuid4())

        # check if the email address and subreddit combination already exists in the database
        cursor.execute("SELECT EXISTS(SELECT relname FROM pg_class WHERE relname = %s and relkind='r');", (email,))
        if cursor.fetchone()[0]:
            cursor.execute('SELECT * FROM "%s";', (AsIs(email),))
            subreddits = cursor.fetchall()
            for subreddit in subreddits:
                if subreddit[0] == subreddit_choice:
                    flash("The e-mail address {} has already been used to sign up for a summary of the {} subreddit. Please sign up with a different e-mail address or a different subreddit.".format(email, subreddit_choice))
                    return redirect(url_for('subrsum.home'))

        # check if the subreddit choice of the user exists
        praw_connection = praw.Reddit(
        client_id=os.environ.get('reddit_api_id'),
        client_secret=os.environ.get('reddit_api_secret'),
        user_agent="scraper",
        username= os.environ.get('reddit_username'),
        password= os.environ.get('reddit_password'),
        )
        try:
            subreddit_check = praw_connection.subreddit(subreddit_choice).top('week')
            submissions = [i.selftext for i in subreddit_check]
        except:
            flash("{} is not a valid subreddit name. Please check your spelling and try again.".format(subreddit_choice))
            return redirect(url_for('subrsum.home'))
        
        # enter form information into database
        cursor.execute("INSERT INTO SummaryRequests VALUES (%s, %s, %s, %s, %s);", (request_id, email, subreddit_choice, keywords, timeframe))
        cursor.execute('''CREATE TABLE IF NOT EXISTS "%s"
        (Subreddit TEXT,
        RequestID TEXT,
        CONSTRAINT fk_requestid
            FOREIGN KEY(RequestID)
                REFERENCES SummaryRequests(RequestID)
                ON DELETE CASCADE);''', (AsIs(email),))
        cursor.execute('''INSERT INTO "%s" VALUES (%s, %s);''', (AsIs(email), subreddit_choice, request_id))


        conn.commit()
        session[subreddit_choice] = [keywords, email]

        return render_template('confirmation_page.html', subreddit=request.form['subreddit'])
    else:
        return redirect(url_for('subrsum.home'))

@bp.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if request.args:    
        cursor = conn.cursor()
        # The "Unsubscribe" link is at the bottom of all subreddit summaries. A query parameter "d" contains the RequestID of the subreddit summary the user is trying to unsubscribe from. This code gets the request id from the query parameter and uses it to delete that request from the database. 
        args = request.args
        request_id = args.get("d")
        cursor.execute('DELETE FROM SummaryRequests WHERE RequestId = %s', (request_id,))
        conn.commit()
        return render_template('unsubscribe.html')
    else:
        return redirect(url_for('subrsum.home'))

@bp.app_errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

@bp.route('/api')
def session_api():
    json_list = []
    for k,v in session.items():
        json_list.append({
            "email" : v[1],
            "subreddit" : k,
            "keywords" : v[0]
        })
    return jsonify(json_list)