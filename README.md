# subreddit_summaries

Subreddit Summary Signup

Tools/Technologies used: Flask, Python, Reddit API(praw), HTML/CSS, Bootstrap, PostgreSQL, Amazon Web Services

This is a full-stack web application that allows users to sign up for a customized email of a subreddit summary. Users can choose a subreddit and a list of keywords that they would like to see posts about. They can choose to receive this email on a daily, weekly, or monthly basis. Users can unsubscribe from these emails by following the "unsubscribe" link at the bottom of each subreddit summary e-mail. The data of the requests is stored in a PostgreSQL database, and AWS Lambda is used to automate the sending of the emails. The emails have been styled with HTML and CSS to provide a cleaner look.
