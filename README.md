<h1 align="center">Literary Quote Clock</h1>

I made a clock that displays the time using quotes from various books using a [Raspberry Pi Zero 2WH](https://www.raspberryPi.com/products/raspberry-Pi-zero-2-w/) and Waveshare's [7.5 inch E-ink display](https://www.waveshare.com/7.5inch-e-paper-hat.htm). All 1,440 minutes of the day have at least one corresponding quote, but many have multiple possible quotes that may be used (one is chosen at random).

<p align="center">
    <img src="misc/demo/demo.jpg" alt="the clock in its frame with a quote that reads There's a train a seventeen minutes to two, said Didier. He blessed himself and got to his feet. He hesitated. 'What's the matter?' 'Shouldn't we say goodbye to Grandpa? He usually has a cheque for me.' —The Public Prosecutor, Jef Geeraerts" width="600"/>
</p>

<h2 align="center">Materials</h2>

- [Waveshare 7.5 inch E-ink Display & HAT](https://www.waveshare.com/7.5inch-e-paper-hat.htm)
- [Raspberry Pi Zero 2WH](https://www.raspberryPi.com/products/raspberry-Pi-zero-2-w/)
  - _Note:_ Waveshare sells a [pre-soldered Pi](https://www.waveshare.com/product/raspberry-Pi/boards-kits/raspberry-Pi-zero-2-w-cat/raspberry-Pi-zero-2-w.htm?sku=21039), which is what I used.
- The frame was handmade using walnut wood.

<h2 align="center">How to Setup the Clock</h2>

The Pi running the clock uses a headless version of the Raspberry Pi OS.

- _Note:_ Any Unix-like OS should work, but I haven't tried anything else personally. You may need to place the startup script in a different location, and the process of making a crontab may be a bit different.

Prior to following the instructions below, make sure you have completed a basic setup of your Pi (at a minimum, make sure you've configured your timezone, have connected the Pi to a WiFi network, and have some version of Python3 installed).

1. Waveshare has provided a handy guide for configuring a Pi to use their screen. The guide can be accessed [here](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_Manual). The [Working With Raspberry Pi](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_Manual#Working_With_Raspberry_Pi) section pertains to this specific project.

2. After you have verified that the screen is working via Waveshare's demo, clone this repository to the Pi with:

    ```sh
    git clone https://github.com/alextaschuk/Literary-Quote-Clock.git
    ```

3. Configure a virtual environment within the cloned repo.

    First, `cd` into the cloned repo and initialize a venv:

    ```sh
    python3 -m venv venv
    ```
    
    Then, activate the venv:
    ```sh
    source venv/bin/activate
    ```
    
    Lastly, install the clock's necessary packages:
    
    ```sh
    pip install -r requirements.txt
    ```

4. In the [clock.service](/scripts/clock.service) script, modify the `WorkingDirectory` variable to store the path to the cloned repo and the `ExecStart` variable to store the path to `clock.py` in the cloned repo. Then, move [clock.service](/scripts/clock.service) into `/etc/systemd/system`.

    - For example, if the repo was cloned into the `Desktop/` directory, change the `WorkingDirectory` variable to `WorkingDirectory=/home/[username]/Desktop/Literary-Quote-Clock`. Similarly, change `ExecStart` to `ExecStart=/home/[username]/Desktop/Literary-Quote-Clock/clock.py`.

5. To run the clock's startup script, run:

    ```sh
    sudo systemctl restart clock.service
    ```

    The script will now automatically start the clock when the Pi is powered on.

6. (Optional) I've come across a problem where the clock becomes desync'd with the actual time due to   an unstable WiFi connection, meaning quotes don't change at the correct moment. A workaround to the issue is to add a crontab that reboots the Pi every day at 4 AM. This doesn't always fix the problem, and sometimes the Pi has to be unplugged from its power source, which usually does the trick for some reason. You can add this cron job by running:

   ```sh
   sudo crontab -e
   ```

   Then, add the following in the file that opens:

   ```sh
   0 4 * * * bash /path/to/Literary-Quote-Clock/scripts/update_clock.sh
   ```
   
   - _Note_: the script will pull changes from the clock's remote repository first, so any updates I make (e.g., adding new quotes) will be automatically downloaded.

<h3>Other Commands</h3>

- To generate the quote images and save them to a `/images` directory:

    ```bash
    python3 image_generator.py
    ```

- To view the top (start) of the clock's logs:
    ```bash
    journalctl -u clock.service
    ```

- To view the clock's most recent logs: 
    ```bash
    journalctl -e -u clock.service
    ```

<h2 align="center">How the Clock Works</h2>

<p align="center">
<img src="./misc/demo/startup-img.bmp" alt="The clock's startup image" width="400"/>
</p>

This project was a gift, so I wanted it to be as plug-and-play as possible. To achieve this, I created a simple systemd unit configuration file ([clock.service](/clock.service)) that starts the clock by running the [clock.py](/clock.py) file after the Pi connects to a WiFi network. It still takes about half a minute for the Pi's internal clock to be updated from this point, so the clock performs a full initialization on the screen to remove any ghosted Pixels and displays a startup image in the meantime, then goes to sleep for 30 seconds.

All of the clock's logic lies in [clock.py](./clock.py), and all of the quotes are stored in [quotes.csv](./quotes.csv). The clock runs in a continuous loop that calls the `main()` function once every minute. The clock maintains a buffer that contains three images, each a succeeding minute past the current minute of the hour. At the top of a minute—technically, the 59th second of the previous minute; you'll see what I mean—`display_quote()` is called, and the image at the front of the buffer is displayed to the screen. Then, `refresh_buffer()` is called, which removes the quote that was just displayed from the buffer, and appends a new image for the time that is three minutes ahead of the next image to be displayed.

Here's an example: Suppose that the clock's program is started at 13:31:15. After sleeping for 30 seconds (it is now 13:31:45), the first image to be displayed is generated outside of the `main()` function and is appened to the buffer (this is necessary because of how the buffer works). Then, the `main()` function is called. Inside of `main()`, `display_quote()` is called, to display the image for 13:31. Then, `refresh_buffer()` is called. Inside of this function, the image for 13:31 is removed from the buffer, and the buffer is populated with images for 13:32, 13:33, and 13:34. Assuming this whole process took 1 second, the time is now 13:31:46, so the program goes to sleep for 13 seconds.

- If you're wondering why it slept for 13 seconds instead of 14 (since 60-46 = 14), this is because it takes ~1 second for the image shown on the screen to change, so the program wakes up at the 59th second of the minute instead of the 0th second of the next minute. This makes it look like the change is actually occuring at the 0th second of the next minute instead of the 1st second.

The program wakes up at 13:31:59, and calls `display_quote()` to show the quote for 13:32 on the screen. Then, `refresh_buffer()` is called, which removes the image for 13:32 from the buffer and appends an image for 13:35. The program then sleeps until 13:32:59.

<h2 align="center">Credits</h2>

I used [JohannesNE's CSV file](https://github.com/JohannesNE/literature-clock/blob/master/litclock_annotated.csv) as a starting point for gathering quotes, and have since made several modifications to the quotes in the file (see the section titled *Adding, Editing, and Finding Quotes*).

Images are generated by parsing the CSV file and writing each row to a .bmp file. I originally used a self-modified version of elegantalchemist's [quote_to_image.py](https://github.com/elegantalchemist/literaryclock/blob/main/quote%20to%20image/quote_to_image.py) program to generate images of the quotes. The biggest modification I made to the image generation files is that it could handle italic and bold characters. However, I wasn't very happy with how readable or maintainable the code turned out to be and I felt that there was a lot of refactoring to be done to the program. I opted to rewrite the entire thing, allowing for any future formatting additions or modifications to be easily added later down the line. The logic for converting a row from the CSV file into an image now exists in [image_generator.py](/image_generator.py) and [writer.py](/writer.py).


<h2 align="center">Formatting Text</h2>

### Character Formatting

JohannesNE's CSV file contains a few quotes that have italic characters, and their project is a website, so the formatting of text in a quote could easily be changed using the CSS `font-style` property to specify if the text should be normal or _italic_, and the `font-weight` property to specify how thick the text should be to make it **bold** (you can even combine them for text that is _**italicized and bolded**_).

In my case, each style of a font needs its own font file. Since each quote is parsed and drawn on a .bmp image character-by-character, my solution to formatting text is similar to how it is done in markdown where a substring of text can be wrapped with custom character delimiters to specify when different font styles should be applied.

#### Italic '`◻`' (White Medium Square, `U+25FB`) 

Wrap a substring with this character to *italicize* it.

For example, the CSV stores:

> Henry held out his hand for the note, which Victoria gave over in exchange for a Sweet Caporal. There were only four words: ◻Tomorrow morning. 2 o’clock◻.

Which will be formatted as:

<p align="center">
    <img src="misc/demo/italic-example.bmp" width="600"/>
</p>

#### Bold: '`◯`' (Large Circle, `U+25EF`)

Wrap a substring with this character to **bold it**.

There aren't any quotes yet where the bold delimiter has been needed, but I have added it as an option just in case.

---

### Word Formatting

There are some instances where preserving a quote's original formatting can help to improve the readability of the quote. They're rarely useful as there is limited screen space to work with, but I have added them anyway.

#### Newline: '`␤`' (Symbol For Newline, `U+2424`)

Add this character to put the succeeding word(s) on a new line (equivalent to `\r\n`). Though this option makes very little difference, I've decided to keep it just in case.

For example, the CSV stores:

> He smiled to himself and went to his office and waited for the telephone call that he knew would come. ␤It came at two o’clock that afternoon.

<p align="center">
    <img src="misc/demo/newline-comparison.png" width="900"/>
</p>

---

#### Double Newline '`⇇`' (Leftwards Paired Arrows, `U+21C7`)

Add this character to put a blank line between wrapped text and the next word (equivalent to `\r\n\r\n`).

For example, the CSV stores:

> A full one hundred meters down the slope, Kazuo Kiriyama didn't look back. Instead, he glanced down at his watch. ⇇The second hand had just made its seventh click past five.

<p align="center">
    <img src="misc/demo/double-newline-comparison.png" width="900"/>
</p>


<h2 align="center">Adding, Editing, and Finding Quotes</h2>

I have manually read through all ~3500 quotes in the original CSV and am in the process of modifying ~700 of them. I have a somewhat strict list of qualities that the quotes can and cannot have, and specific types of changes that I make depending on what I think is "wrong" about the quote's context, formatting, etc. This section covers some of the things that I look for when evaluating if a quote needs to be modified or removed, my own quotes that I have found and added, and a list of minutes that are missing quotes/are in need of better quotes.

---

**Can the quote be used for both the A.M. and P.M. times of the day (e.g., 07:00 and 19:00)?**
    
- If the answer is "yes", check if the quote has already been used twice. If not, add it to the other time.

- If the answer is "no", check that the quote wasn't mistakenly added to both times of the day. If it was, remove it from the second time.

Example 1:
> At **8 o’clock** on Thursday morning Arthur didn't feel very good. —_The Hitchhiker’s Guide to the Galaxy_, Douglas Adams
  
Clearly, this quote should only be used for 08:00. Check if there is also a row for the quote at 20:00. If there is, remove it.

Example 2:
> The front doorbell rang at **one minute to ten**, and Karl answered it. —_Best Kept Secret_, Jeffrey Archer

This quote is vague enough that it is not clear whether "__one minute to ten__" is referring to 9:59 or 21:59 (unless you have read the book, which I haven't). Check if there is a row for the quote at 21:59. If there isn't, add it.

---

**Does the quote mention more than one time of the day?**

If it does, check if the additional time(s) also have this quote. Otherwise, add them as new rows.
  
Example:

> My watch lay on the dressing-table close by; glancing at it, I saw that the time was **twenty-five minutes to seven**. I had been told that the family breakfasted at nine, so I had nearly two-and-a-half hours of leisure. Of course, I would go out, and enjoy the freshness of the morning. —_Ravensdene Court_, J.S. Fletcher

This quote was used for 06:35, but it can also be used for 09:00. However,it didn't have a row for 09:00 (it can technically be used for 07:00 too, though I chose not to add it for this time because "**seven**" is being used to refer to a number of minutes before 07:00). Furthermore, it is clear from the context of the quote that the time of day is morning, so the quote should only be added for 9:00 and not 21:00 too. Using the quote for 09:00, it would look like this:

> My watch lay on the dressing-table close by; glancing at it, I saw that the time was twenty-five minutes to seven. I had been told that the family breakfasted at **nine**, so I had nearly two-and-a-half hours of leisure. Of course, I would go out, and enjoy the freshness of the morning. —_Ravensdene Court_, J.S. Fletcher

---
  
**Does the quote require more or less context (i.e., a preceding and/or succeeding sentence)? Could the quote be enhanced by adding more context?**

If more context is required or could possibly enhance the quote,  add it as needed.

Example 1:
> There were only four words: _Tomorrow morning. 2 o’clock_. —_Full Dark, No Stars_, Stephen King

The context of this sentence is not clear to the reader by itself. The four words could be words that someone spoke, wrote, or read. However, when we add the preceding sentence, the context becomes significantly more obvious: 

> Henry held out his hand for the note, which Victoria gave over in exchange for a Sweet Caporal. There were only four words: _Tomorrow morning. 2 o’clock_.

Now, it is clear to the reader that the four words were written on a note that a character named Victoria traded to someone named Henry for a pack of Sweet Caporals.

Example 2:

> It was nine o’clock when we finished breakfast and went out on the porch. —_The Great Gatsby_, F. Scott Fitzgerald

By itself, this quote is perfectly fine and makes sense. However, we can include the sentence that follows to provide a bit more information to the reader:

> It was nine o’clock when we finished breakfast and went out on the porch. The night had made a sharp difference in the weather, and there was an autumn flavor in the air. —The Great Gatsby, F. Scott Fitzgerald

---

**Does the quote specify an exact hour and minute?**

The strictness of this rule is dependent on a quote-to-quote basis and the wording that is used. If the mention of time in a quote is worded with "just past [**time**]," "just before [**time**]," or similar language, I will usually use the quote the 1st minute or the 59th minute of an hour.

Example 1:

> Raymond came back with Masson around one-thirty. His arm was bandaged up and he had an adhesive plaster on the corner of his mouth. The doctor had told him it was nothing, but Raymond looked pretty grim. Masson tried to make him laugh. But he still wouldn't say anything. —_The Stranger_, Albert Camus

Prior to modification, this quote was being used for 13:31, with the time quote being "Raymond came back with Masson **around one-thirty**." My issue with this is that "around" leaves too much room for interpretation and doesn't tell the reader what time it actually is. I moved it to be displayed at 13:30 and change the time quote to instead be "Raymond came back with Masson around **one-thirty**."

Example 2:

> Shuya held his watch up to the moonlight. The finely crafted old model K. Hattori diver’s watch (a gift, like most of his possessions, with him living in an orphanage) read **just past 2:40**. Whatever had happened to Yoshio Akamatsu, nearly all of the students would have left the school by now, save for two or three. —_Battle Royale_, Koushun Takami

- I would use this quote for 02:41, but it would be perfectly fine to use it for 02:40 instead (though, I wouldn't use it for both since that could cause the same quote to be displayed back-to-back).

---

There are also general formatting changes that I look for and apply as needed. This includes things such as fixes when a certain part of the quote that should/shouldn't be highlighted is or isn't:

> A man driving a tractor saw her, four hundred yards from her house, **six minutes past two** in the afternoon. —_A Change of Climate_, Hilary Mantel

This sentence should have "in the afternoon" as a part of the time quote because it specifies that the time is 14:06 and not 02:06.

> A man driving a tractor saw her, four hundred yards from her house, **six minutes past two in the afternoon**. —_A Change of Climate_, Hilary Mantel

Minor changes to character formatting, including:
- Replacing instances of three full stops (`...`) with a proper horizontal ellipsis character (`…`, `U+2026`)
- Replacing instances of two hyphens (`--`) with an em dash (`—`)
- Replacing all instances of double quotation marks (`"`) with a left double quotation mark (`“`, `U+201C`) or a right double quotation mark (`”`, `U+201D`) for the opening and closing of quotes.

---

<h3>Adding My Own Quotes</h3>

As I find quotes in the books I read in my free time, I add them to the CSV file (see [my-quotes.csv](./misc/my-quotes.csv) for only the quotes I have found). Here are the books I have found quotes in while reading:

| Title                          | Author               | Number of Quotes      |
| ------------------------------ | -------------------- | ----------------      |
| Battle Royale                  | Koshun Takami        | 59                    |
| Stoner                         | John Williams        | 21                    |
| All Quiet on the Western Front | Erich Maria Remarque | 20                    |
| In Cold Blood                  | Truman Capote        | 84                    |
| The Road                       | Cormac McCarthy      | 8                     |
| Butcher’s Crossing             | John Williams        | 16                    |
| The Great Gatsby               | F. Scott Fitzgerald  | 51                    |
| 2001: A Space Odyssey          | Arthur C. Clarke     | 10                    |
| Before the Coffee Gets Cold    | Toshikazu Kawaguchi  | 3                     |
| Dungeon Crawler Carl           | Matt Dinniman        | 5                     |
| Carl’s Doomsday Scenario       | Matt Dinniman        | 2                     |
| Dune                           | Frank Herbert        | 12                    |
| Dune Messiah                   | Frank Herbert        | 3                     |
| Children of Dune               | Frank Herbert        | 16                    |
| God Emperor of Dune            | Frank Herbert        | 1 (Currently Reading) |

- *Note*: A few of these quotes are used for AM and PM, so the third column is for total quotes found in each book, not unique quotes.

---

<h3>Times Without a Quote / In Need of a Better One</h3>

There are a few times that are still without any quote at all (an error message is currently displayed in lieu of the missing images).

There are also some times that I am looking for better quotes for. This is because they have only one quote option, and that quote is one that I would like to remove/replace, but can't since it's the only option for that minute.

Looking for Better Option |
------------------------- |
00:51                     |
00:57                     |
05:26                     |
06:02                     |
07:36                     |
08:01                     |
08:02                     |
09:08                     |
10:16                     |
11:47                     |
12:31                     |
18:04                     |


<h2 align="center">Other Notes</h2>

<h3>Troubleshooting the Pi</h3>

The Raspberry Pi Zero 2W cannot connect to a 5 Ghz WiFi channel; it only works with 2.4 GHz. If you have issues connecting try the following to troubleshoot:

  1. Log into your modem and temporarily disable the 5 GHz channel, allowing the Pi to connect only to the 2.4 GHz channel. After it connects, you can re-enable the 5 GHz channel.
     - _Note: You shouldn't have to do this every time you turn the Pi on. Once it connects to your WiFi on the 2.4 GHz channel for the first time, it should do so automatically every time moving forward._
  2. Rename the 2.4 GHz channel to have a different SSID.
     - E.g. `SSID-Name-2_4GHz`

If the you take the clock into a new timezone, the Pi's localization settings need to be changed manually. Otherwise the clock won't display the correct time.

<h3>Miscellaneous</h3>

Waveshare has some additional helpful [documentation](https://www.waveshare.com/wiki/E-Paper_APi_Analysis#Python) on other functions and things that can be done on the screen (separate from their config guide).

*Note*: No AI (e.g., Claude, Gemini, etc.) has been used to any extent for this project.
