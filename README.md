[![python](https://img.shields.io/badge/Python-3.10.0-FFD43B)](https://www.python.org/downloads/release/python-3100/)   ![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?logo=openai&logoColor=white)

# Telegram Posts Scraper

## Overview

Telegram Posts Scraper is a standalone application and script designed to scrape posts from a specified Telegram channel. The output is saved in a compressed `.parquet.gzip` format.

### Features

- Standalone application with a graphical user interface (GUI)
- Script-based operation for command-line users
- Outputs data in `.parquet.gzip` format
- Optional content masking for post data

__Important:__ most of the GUI code has been generated using Chat GPT

---

## 1. Application

The standalone application provides an easy-to-use GUI for scraping posts from a Telegram channel. It was build on top of [this](#2-script) script, and converted into an executable file using `auto-py-to-exe`.

### How to Use

1. __Download__: [Telegram Posts Scraper.exe](https://github.com/cyterat/tg-scraper/blob/main/Telegram%20Posts%20Scraper.exe)
2. __Run the Application__: Double-click the downloaded executable file.
3. __Wait:__ It might take a few seconds to start up.
3. __Input Details__: Enter the channel details and date range as prompted.
4. __Scrape__: Click the "Start Scraping" button to begin.

### Screenshots

![Application Window](assets/app-window.png)

---

## 2. Script

The `tg-scraper.py` script is designed for users who prefer the command-line interface. It scrapes posts from a specified Telegram channel and writes the output into a compressed parquet file using the `snscrape` module.

### How to Use

1. __Run the Script__:

    ```sh
    python tg-scraper.py
    ```

2. __Provide Inputs__: When prompted, enter:
    - The `XXXX` part of the Telegram channel URL `https://web.telegram.org/k/#@XXXX`
    - The start and end dates to define the scraping period

3. __Optional Content Masking__: Choose whether to mask post contents in the output file with `#####`.

### Script Example

```sh
python tg-scraper.py
# Example prompts
Enter channel name (XXXX): example_channel
Enter start date (YYYY-MM-DD): 2023-01-01
Enter finish date (YYYY-MM-DD): 2023-12-31
Include post contents? (y/n): y
```

![](assets/script-run-example.png)

#### Script Output Example

The output file name is automatically generated: `tg-posts` + `[channel name]` + `[start date]` + `[end date]` + `.parquet.gzip`.

It will be saved in the `data` folder (in a current directory)  as a compressed parquet file with the following structure:

| post_id |      post_url      |         date        |    content    |
| ------- | ------------------ | ------------------- | ------------- |
| 12345   | <https://t.me/12345> | 2023-01-01 12:00:00 | Lorem Ipsum  |

The excluded (masked) post contents, if a respective option is chosen, will be replaced with `#####`:

| post_id |      post_url      |         date        |    content    |
| ------- | ------------------ | ------------------- | ------------- |
| 12345   | <https://t.me/12345> | 2023-01-01 12:00:00 | #####  |

#### Script Requirements

- Python 3.10
- Required Python libraries: `snscrape`, `pyarrow`, `PyQt5`

Install dependencies using:

`pip install -r requirements.txt`

***

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License. To view a copy of this license, visit [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
