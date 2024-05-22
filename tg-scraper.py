from datetime import datetime
import time
import random
from sys import exit

import snscrape.modules.telegram as tg

from pyarrow import Table 
from pyarrow.parquet import write_table


# Channel name variable
CHANNEL_NAME = str(input("\n◽ Enter a channel name to scrape, use the XXXX part in 'https://web.telegram.org/k/#@XXXX': ").strip()) # use the XXXX part in 'https://web.telegram.org/k/#@XXXX'

# Check for input
if len(CHANNEL_NAME.strip()) == 0 :
        exit('\n🔴 A channel name was not provided. Exiting program.')

# Date variables 
START_YEAR = int(input("◽ Enter the year when the scraping should start, default '2024': ").strip() or str(datetime.today().year))
START_MONTH = int(input("◽ Enter the month when the scraping should start, default '01': ").strip() or "01")
START_DAY = int(input("◽ Enter the day when the scraping should start, default '01': ").strip() or "01")

# Lower date boundary variable. Posts before it are not included
START_DATE = f"{START_YEAR}-{START_MONTH}-{START_DAY}" # year, month, day

# Maximum delay between requests
MAX_SLEEP = 0.1 # seconds

# Print the elapsed time at each iteration
VERBOSE = False # False by default


def validate_choices():
    """
    This function validates user input to confirm their choice before proceeding with scraping posts.

    Returns: 
        None
    """
    
    print(f"\nYou are about to scrape all posts from {CHANNEL_NAME} starting from {START_DATE}.")
    choice = str(input('🔸 Are you sure you want to continue? y / n: ')).lower()
    
    if choice == 'n':
        exit('Exiting program')
    elif choice == 'y':
        pass
    else:
        exit('\n🔴 Received an invalid response. Exiting program.')


def scrape_channel(channel_name=CHANNEL_NAME, start_date=START_DATE, max_sleep=MAX_SLEEP, verbose=VERBOSE):
    """
    This function scrapes a specified Telegram channel for messages.

    Parameters:
    - channel_name (str): The name of the Telegram channel to scrape.
      The default value is None.

    - start_date (str): The date from which to start scraping messages. 
      The date should be in the format 'YYYY-MM-DD'. The default value is '2021-01-01'.

    - max_sleep (int): The maximum number of seconds to wait between requests to avoid
      overloading the server or getting blocked. The function will wait for a random 
      number of seconds between 0 and max_sleep before making each request. 
      The default value is 0.2.

    - verbose (bool): If True, the function will print out the elapsed time at each iteration.
      If False, the function will run silently. The default value is False.

    Returns:
    - This function returns a list of messages from the specified Telegram channel.
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
    datetime_object = datetime.strptime(start_date, '%Y-%m-%d')

    # Start the timer
    start_time = time.time()  
    elapsed_time_list = []

    # Iterate over posts
    for i, post in enumerate(channel.get_items()):

        # Check if post is not older than a date threshold
        if post.date.date() >= datetime_object.date():

            # Print out contents of the first post
            if i == 0:
                print('🔸 Example of a Telegram post:')
                print(f"◻️ Post #{post.url.split('/')[-1]}:")
                print(f"◻️ URL: {post.url}")
                print(f"◻️ Date: {post.date}")
                print(f"◻️ Content: {post.content}")
                print('...\n')
                print(f"⏰ Scraping posts after {start_date} with random delay up to {max_sleep} seconds...\n")

            # Append posts to the list if they satisfy the 'date' condition        
            raw.append({
                'post_id': post.url.split('/')[-1], # last string in a split url is basically a post number (id)
                'post_url': post.url,
                'date': post.date,
                'content': post.content
                })

            # Print elapsed time at each iteration
            check_time = time.time() - start_time
                
            # Writes the time when the post was stored relative to the start time of the loop
            elapsed_time_list.append(check_time)

            # False by default
            if verbose:
                print(f"Elapsed time: {check_time:.0f} seconds")
            
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
    Additionaly, it adds START_DATE year value to the output file name.
    
    Returns:
        None
    """
    
    # Write scraped data into pyarrow table
    table = Table.from_pylist(scrape_channel())

    print(f"\n🔸 The dataset has: {table.shape[0]} rows and {table.shape[1]} columns")

    # Extract the year from START_DATE
    filename_year = datetime.strptime(START_DATE, '%Y-%m-%d').year
    
    # Paste year into the output filename
    output_name = f"telegram-posts-{filename_year}-{datetime.now().year - filename_year}y.parquet.gzip"
    
    # Export pyarrow table as a compressed parquet file
    write_table(table, output_name)

    print(f"\n🔽 Saved locally as '{output_name}'")


if __name__ == '__main__':
    validate_choices()
    main()