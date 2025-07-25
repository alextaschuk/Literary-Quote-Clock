# Literary Quote Clock

I made a clock that displays the time using quotes from various books using a [Raspberry PI Zero 2WH](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) and Waveshare's [7.5 inch E-ink display](https://www.waveshare.com/7.5inch-e-paper-hat.htm). (Almost) every minute of the day has at least one corresponding quote, but many have multiple possible quotes that may be used (one is chosen at random).

<p align="center">
<img src="demo/demo.jpg" alt="picture of clock in its frame" width="600"/>
</p>

## Materials:
 
- [Waveshare 7.5 inch E-ink Display & HAT](https://www.waveshare.com/7.5inch-e-paper-hat.htm)

-  [Raspberry PI Zero 2WH](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)
    - *Note:* Waveshare sells a [pre-soldered PI](https://www.waveshare.com/product/raspberry-pi/boards-kits/raspberry-pi-zero-2-w-cat/raspberry-pi-zero-2-w.htm?sku=21039), which is what I used



## Setting the PI Up

1. Waveshare has provided a handy guide for configuring a PI to use their screen. The guide can be accessed [here](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_Manual). The [Working With Raspberry PI](https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT_Manual#Working_With_Raspberry_Pi) section pertians to this specific project.

2. After you have verified that the screen is working via Waveshare's demo, clone this repository to the PI.

3. Initialize a venv with `python3 -m venv venv`, activate it with `source venv/bin/activate`, then install necessary packages with `pip install -r requirements.txt`.

3. Run [`make_images.py`](make_images.py) to generate all of the `.bmp` images that will be used to display the time. The images will be located in the [`/images`](/images) folder.

4. In the [`clock.service`](\clock.service) script, modify the `WorkingDirectory` variable to store the path to the cloned repo and the `ExecStart` variable to store the path to `clock.py` in the cloned repo. Then, move the file to `/etc/systemd/system`.

5. Run `sudo systemctl restart clock.service` to start the clock. The script will now automatically start the clock any time that the PI is turned on.

6. (Optional) I've noticed that sometimes the clock seems get out of sync with the actual time, meaning quotes don't change at the correct moment. It's pretty gradual and also seems to fix itself so I'm not sure if this is an issue with my code or the PI's internal clock. A workaround to the issue is to add a crontab that reboots the PI everyday at 4AM. You can add this cronjob by running:

    `sudo crontab -e`

    Then 

    `0 4 * * * /usr/sbin/reboot`

### Other

- To view the top (start) of the clock's logs: `journalctl -u clock.service`

- To view the clock's most recent logs: `journalctl -e -u clock.service`

## How the Clock Works

All of the clock's logic lies in `clock.py`. There are three stages that the clock runs in- the initialization stage, the display & update stage, and the "in-between" stage.

### The Intialization Stage

This stage only occurs once when the clock is plugged in. This project was actually a gift to my girlfriend for her birthday, and I wanted it to be as plug-and-place as possible. During this stage [`clock.service`](\clock.service), a systemd unit configuration file that runs once the PI has an internet connection, starts the clock by running [`clock.py`](/clock.py). When [`clock.py`](/clock.py) is first ran, it will clear the screen and perform a full initialization to remove any ghosted pixels. 
Though the PI has an internet connection at this point, it still takes about 30 seconds to update its internal clock. In the meantime, [`startup.bmp`](startup.bmp) is displayed.

After 30 seconds has passed, the clock's quote buffer is initialized. Because it may take a second or two for the program to read, process, and display the image file a buffer is used to store the current and next two quotes to display. It is a list that contains three elements- the first is the Image obj for the current time's quote, the second is the Image obj for the next minute's quote, and the third is the Img obj of the quote two minutes ahead of the current quote. 

### The Display & Update Stage
This stage occurs once every minute; most of the magic happens here. Two events make up this stage- The first is displaying a quote and the second is updating the quote buffer. At the 59th second of a minute (it takes ~1 second for the screen to update) [`display_quote()`](/clock.py#L178) is called, which displays the Image obj at index 0 of the quote buffer. Then, [`update_buffer()`](/clock.py#L121) is called, which appends the Image obj for the quote that is two minutes ahead of the Image at index 1 of the buffer.

- Example: The current time is 13:31. The buffer looks like this: `[13_32_Img, 13_33_Img, 13_34_Img]` At 13:31:59, call [`display_quote()`](/clock.py#L178) to display the quote for 13:32. Then, `13_35_Img` is appended to the buffer and `13_32_Img` is removed, resulting in the buffer looking like this: `[13_33_Img, 13_34_Img, 13_35_Img]`.

### The "In-Between" Stage

This stage involved everything that happens in the time between a quote being displayed and waiting for the end of the current minute. First, the screen is put to sleep to reduce its power consumption, then we calculate how long until the next minute so that we know when to wake screen and reenter the Display & Update Stage. The cycle between the Display & Update Stage and the "In-between" Stage continues as long as the clock runs.


## Other Notes

- The Raspberry Pi Zero 2W cannot connect to a 5 Ghz WiF channel; it only works with 2.4 GHz. If you have issues connecting try the following to troubleshoot:
    1. Log into your modem and temporarily disable the 5 GHz channel, allowing the PI to connect only to the 2.4 GHz channel. After it connects, you can re-enable the 5 GHz channel.
        - *Note: You shouldn't have to do this every time you turn the PI on. Once it connects to your WiFi on the 2.4 GHz channel for the first time, it should do so automatically every time moving forward.*
    2. Rename the 2.4 GHz channel to have a different SSID.
        - E.g. `SSID-Name-2_4GHz`

- Waveshare has some additional helpful [documentation](https://www.waveshare.com/wiki/E-Paper_API_Analysis#Python) on other functions and things that can be done on the screen (separate from their config guide above).

- If the you take the clock into a new timezone, the PI's localization settings need to be changed manually. Otherwise the clock won't display the correct time.
    - Maybe there's a way to read PI's IP address when it connects to WiFi and update the setting if its timezone is different?

## Credits

[`make_images.py`](/make_images.py) is a modified version of [elegantalchemist's `quote_to_image.py`](https://github.com/elegantalchemist/literaryclock/blob/main/quote%20to%20image/quote_to_image.py) program.

The program parses a CSV file and converts each line into a .bmp file. I decided to use [JohannesNE's CSV file](https://github.com/JohannesNE/literature-clock/blob/master/litclock_annotated.csv) instead of [elegantalchemist's](https://github.com/elegantalchemist/literaryclock/blob/main/quote%20to%20image/litclock_annotated_br2.csv); both files contain many of the same quotes, but  JohannesNE's seems more refined and has more quotes overall. I manually went through all ~3500 quotes in the file and am in the process of modifying the CSV for the following reasons:

- I have found that some quotes can be used for both A.M and P.M. but currently aren't.
- I'd like to add more context to some quotes (i.e., a preceding and/or succeeding sentance)
- I am modifying some because I feel that they are too vauge (e.g., "Raymond came back with Masson around one-thirty." with "around one-thirty" highlighted for 13:31 will be used for 13:30 with "one-thirty" being highlighted)
- A certain part of the quote is or isn't highlighted (e.g., for the quote "A man driving a tractor saw her, four hundred yards from her house, six minutes past two in the afternoon." only "six minutes past two" is highlighted when "six minutes past two in the afternoon" should be). 

I also read in my free time, and will be adding quotes that I find in books as I read.
 
The biggest modification I made is to handle italic characters. JohannesNE's CSV file contains a few quotes that have italic characters (their project is a literary quote clock website that uses HTML which makes it a lot easier to handle italic text), and elegantalchemist's code doesn't have a way to detect and handle these characters. With CSS, you can easily change the `font-style` between normal, *italic*, and **bold**, but in my case a different font file is needed for italicized characters because font files can only contain one font style. My solution is to wrap italicized words in a '◻' character (White medium square, U+25FB) since each quote is written to the .bmp file word-by-word. Quotes that have the time part italicized are wrapped with a '◯' character (Large circle, U+25EF) since they'll need a font file that has bolded and italicized characters. For example, a quote might have looked like this in the CSV file: "There were only four words: *Tomorrow morning. 2 o'clock*." With my changes, it looks like this: "There were only four words: ◻Tomorrow◻ ◻morning◻. ◯2◯ ◯o'clock◯."




****
personal todo notes and other stuff ignore plz

Quick-access characters for copy & pasting

`◻`     `◯`     `—` (em dash)   ⭐    `…` (ellipsis)

- dont forget to pull changes then modify clock.service from app.py to clock.py

## PI and SSH Info

- From Mac, `ping raspberrypi.local` should return success.

- The Pi's IP address is 10.0.0.94

### To SSH

1. Run `ssh alex@raspberrypi.local`
2. Enter the Pi's password: password


### To Run Waveshare's Screen Test

1. CD to `/Desktop/WaveshareTest/e-paper/RaspberryPi-JetsonNano/python/examples`
2. Run `python3 epd_7in5_V2_test.py`

### TODO

**Documentation**
- pictures of the clock

**TODO**

- Dark mode
- Remote login
- Why does # of quote images not match # of csv rows?
- Improve quote formatting
- Handle quotes that are on multiple lines

Example:
``` Text
9:43 P.M.

"We'll be working together, kid," Dore Peretz was saying. "We're a team"...
```

shouldn't be too hard since new line is calculated based on quote length.
just need to call it prematurely somehow(?)



- Go through CSVs, fix/improve quotes, and combine them
- Special Messages

Tech issues
- At 12AM every even minute will cause a full init
- Maybe update journalctl config to clear once a week if it will cause storage issues
- Implement a check for if the author and book title are longer than threshold, it changes the coordinates the start at


- Pi's every time timezone is changed. Maybe automate this using IP?

How to add a crontab that reboots the PI everyday at 4AM as a workaround for desync issues:

    1. `sudo crontab -e`
    2. `0 4 * * * /usr/sbin/reboot


Look into issue: If timestring is italicized and has 3+ words (example: ◯Eight◯ ◯oh◯ ◯two◯), the middle word(s) aren't identified as word to write with italicized & bolded font, so the '◯' character
isnt removed from the substring.
    - Currently, the quotes for 8:02AM & 8:02AM are broken b/c of this... possibly more tho
    - use '⭐' as newline delimiter... for fun

`13:32|one ... thirty-two|“At the third stroke it will be one ... thirty-two ... and twenty seconds.” ⭐“Beep ... beep ... beep.” ⭐Ford Prefect suppressed a little giggle of evil satisfaction, realized that he had no reason to suppress it, and laughed out loud, a wicked laugh.|So Long, and Thanks for All the Fish|Douglas Adams|unknown`

should print as:
``` txt
“At the third stroke it will be one ... thirty-two ... and twenty seconds.”

⭐“Beep ... beep ... beep.”

⭐Ford Prefect suppressed a little giggle of evil satisfaction, realized that he had no reason to suppress it, and laughed out loud, a wicked laugh.
```
Possible unicode characters to use for delimiting things:
⭐  ╱   ♜  ♞  ⚡  ⛏  ⭕  𝌉   🂱   🅱   🆒   🐄  📖  🙼   🟨  🟧  🤍

Maybe also look into indenting quotes as well. For example:

`13:59|One ... fifty-nine|For twenty minutes he sat and watched as the gap between the ship and Epun closed, as the ship's computer teased and kneaded the numbers that would bring it into a loop around the little moon, and close the loop and keep it there, orbiting in perpetual obscurity. ⭐"One ... fifty-nine ..."|So Long, and Thanks for All the Fish|Douglas Adams|unknown`

should print as:

``` txt
‎ ‎ ‎ ‎For twenty minutes he sat and watched as the gap between the ship and Epun closed, as the ship's computer teased and kneaded the numbers that would bring it into a loop around the little moon, and close the loop and keep it there, orbiting in perpetual obscurity. 

⭐"One ... fifty-nine ..."
```

New edge case for italics-- part of the word should be italicized, but not all of it. I think it'd only be an issue in possessive cases. 

For example, the direct quote is : "Each morning, over eggs and kippers, he peruses the *Times*'s personal notices."

With the current implementation, *Times*'s would be ◻Times◻'s, but this doesnt work, so the quote would be skipped. 
    - One solution is ◻Times's◻ but I dont like it.
    - Find proper solution.

