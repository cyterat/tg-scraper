from datetime import date
from datetime import datetime
import time
import random
from sys import exit

import snscrape.modules.telegram as tg

from pyarrow import Table 
from pyarrow.parquet import write_table


# Channel name variable
CHANNEL_NAME = str(input("\n🔸 Enter a channel name to scrape, use the XXXX part in 'https://web.telegram.org/k/#@XXXX': ").strip()) # use the XXXX part in 'https://web.telegram.org/k/#@XXXX'

# Check for input
if len(CHANNEL_NAME.strip()) == 0 :
        exit('\n🔴 A channel name was not provided. Exiting program.')

# Default date values
_default_start = f"{datetime.today().year}-01-01"
_default_finish = f"{datetime.today().year}-12-31"

# Lower date boundary variable. Posts before it are not included
START_DATE = str(input("🔸 Enter the first date to begin scraping from, in YYYY-MM-DD format (beginning of the current year by default): ").strip() or _default_start)  # year, month, day

# Upper date boundary variable. Posts after it are not included
FINISH_DATE = str(input("🔸 Enter the last date to scrape, in YYYY-MM-DD format (end of the current year by default): ").strip() or _default_finish)  # year, month, day

# Maximum delay between requests
MAX_SLEEP = 0.1 # seconds

# Include posts contents in the output file
VERBOSE = True # True by default
VERBOSE = str(input('🔸 Do you want to include posts contents in the output file? y / n: ').strip() or 'y')


def validate_choice():
    """
    This function validates user input to confirm their choice before proceeding with scraping posts.

    Returns: 
        None
    """
    
    print(f"\nYou are about to scrape all {CHANNEL_NAME} posts from {START_DATE} to {FINISH_DATE}.")
    choice = str(input('🔸 Are you sure you want to continue? y / n: ')).lower()
    
    if choice == 'n':
        exit('Exiting program')
    elif choice == 'y':
        pass
    else:
        exit('\n🔴 Received an invalid response. Exiting program.')


def scrape_channel(channel_name=CHANNEL_NAME, start_date=START_DATE, finish_date=FINISH_DATE, max_sleep=MAX_SLEEP, verbose=VERBOSE):
    """
    This function scrapes a specified Telegram channel for posts.

    Parameters:
    - channel_name (str): The name of the Telegram channel to scrape.
      The default value is None.

    - start_date (str): The date from which to start scraping posts. 
      The date should be in the format 'YYYY-MM-DD'.

    - finish_date (str): The date up to which (including it) the posts will be scraped. 
      The date should be in the format 'YYYY-MM-DD'.

    - max_sleep (int): The maximum number of seconds to wait between requests to avoid
      overloading the server or getting blocked. The function will wait for a random 
      number of seconds between 0 and max_sleep before making each request. 
      The default value is 0.2.

    - verbose (bool): If False, the function will substitute post content with '#####'.
      The default value is True.

    Returns:
    - This function returns a list of posts from the specified Telegram channel.
      Each message is represented as a dictionary with keys for different attributes 
      of the message (post_id, date, content).
    """
    # Display target channel name
    print(f"\n🧲 Target Telegram channel >>> '{channel_name}'\n")

    # Create a Telegram channel scraper
    channel = tg.TelegramChannelScraper(channel_name)
    
    # Empty list will be filled with dictionaries
    raw = []

    # Convert date string to datetime object
    start_datetime_object = datetime.strptime(start_date, '%Y-%m-%d')
    finish_datetime_object = datetime.strptime(finish_date, '%Y-%m-%d')


    # Start the timer
    start_time = time.time()  
    elapsed_time_list = []

    # Iterate over posts
    for i, post in enumerate(channel.get_items()):

        # Check the post against the dates thresholds
        if post.date.date() >= start_datetime_object.date() and post.date.date() <= finish_datetime_object.date():

            # Display contents of the first post
            if i == 0:
                print('🔸 Output sample:')
                print(f"◻️ Post #{post.url.split('/')[-1]}:")
                print(f"◻️ URL: {post.url}")
                print(f"◻️ Date: {post.date}")
                print(f"◻️ Content: {post.content[:50]}...")
                print(f"\n⏰ Scraping posts between {start_date} and {finish_date} with random delay up to {max_sleep} seconds...\n")

            # Mask post contents in the output file if False (True by default)
            if verbose == 'y':  
                content = post.content
            elif verbose == 'n':
                content = '#####'
            else:
                exit('\n🔴 Received an invalid response. Exiting program.')

            # Append posts to the list if they satisfy the conditions        
            raw.append({
                'post_id': post.url.split('/')[-1], # last string in a split url is basically a post number (id)
                'post_url': post.url,
                'date': post.date,
                'content': content
                })

            # Print elapsed time at each iteration
            check_time = time.time() - start_time
                
            # Writes the time when the post was stored relative to the start time of the loop
            elapsed_time_list.append(check_time)
            
            # Introduce a random delay
            time.sleep(random.uniform(0, max_sleep))  # Sleep for a random time between 0 and MAX_SLEEP seconds

        else:
            break

    # Total loop time
    elapsed_time_total = time.time() - start_time

    def post_download_speed():
        """
        This function returns the approximate number of 'appended' posts per minute.

        Returns: 
            int
        """
        # Calculate differences between consecutive time intervals
        differences = [(elapsed_time_list[i] - elapsed_time_list[i-1]) for i in range(1, len(elapsed_time_list))]

        # Calculate mean sleep time 
        mean_sleep = sum(differences) / len(differences)

        # Calculate approximate speed: 1min / mean_sleep = posts per minute
        speed = 60 / mean_sleep

        return int(speed)

    print(f"✔️ Successfully scraped {len(raw)} posts from '{channel_name}' Telegram channel.")
    print(f"🔹 Script took {elapsed_time_total:.0f} seconds to run.")
    print(f"🔹 The approximate scraping speed was {post_download_speed()} posts per minute.")
    return raw


def main():
    """
    This function converts raw list of dictionaries to a
    pyarrow table and then writes it to the compressed parquet file.
    Additionaly, it creates a custom output file name based on the input parameters.
    
    Returns:
        None
    """
    
    # Write scraped data into pyarrow table
    table = Table.from_pylist(scrape_channel())

    print(f"\n🔹 The dataset has {table.shape[0]} rows and {table.shape[1]} columns")
    
    # Create an output file name
    output_name = f"tg-posts-{CHANNEL_NAME}-{START_DATE}-{FINISH_DATE}.parquet.gzip"
    
    # Export pyarrow table as a compressed parquet file
    write_table(table, output_name)

    print(f"\n🔽 Saved locally as '{output_name}'")


if __name__ == '__main__':
    validate_choice()
    main()