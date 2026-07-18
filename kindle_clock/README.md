Link to extensions to disable/enable the screen going to sleep: https://www.mobileread.com/forums/showthread.php?t=293264


https://www.mobileread.com/forums/showthread.php?t=367713 for python bin


Where to find FBInk binary by itself: https://www.mobileread.com/forums/showthread.php?t=299620

there is an fbink file in /mnt/us/libkh/bin/fbink. idk if i put it there or if someone else did.

# Literary Quote Clock Scriptlet / KUAL Extension

Jailbroken software can change/become irrelevant very quickly, so parts of this documentation may become out of date. That said, the bottom line is that you need to accomplish two things for this to work:

## Installing the Extension

The setup instructions will be broken into two parts: generating the images for the clock and jailbreaking the kindle/installing the clock. Since this repository is set up to work as a clock for Kindles and other e-paper screens, there is a bit of configuration that will need to be done prior to generating the images.

### Image Generation.

1. Clone this repository to your local device with:

    ```sh
    git clone --recursive https://github.com/alextaschuk/Literary-Quote-Clock.git
    ```
    
    - _Note:_ Don’t include the `--recursive` flag! This is only necessary for IT8951 screens.

2. Configure a virtual environment within the cloned repo.

    First, `cd` into the cloned repo and initialize a venv:

    ```sh
    python3 -m venv venv
    ```
    
    Then, activate the venv:
    ```sh
    source venv/bin/activate
    ```
    
    Lastly, install the clock’s necessary packages:
    
    ```sh
    pip install -r requirements.txt
    ```

3. The `constants.py` file is set up for non-IT8951 screens by default, but there may be some modifications that will need to be made:

    1. Make sure `SCREEN_WIDTH` and `SCREEN_HEIGHT` match your Kindle’s display dimensions. You can check your model’s display size at the [Device specifications](https://en.wikipedia.org/wiki/Amazon_Kindle#Device_specifications) section of Wikipedia’s article on Kindles.
    2. Change the `IMAGE_FORMAT` to `'png'`.
    3. Depending on the screen’s resolution, you may need to increase `MAX_FONT_SIZE`.

4. In image_generator.py, Uncomment `quote_image = quote_image.transpose(method=Image.Transpose.ROTATE_270)` at the end of the `generate_img()` function. The images need to be physically rotated to display on the screen properly.

5. Generate the images by running:

    ```sh
    python image_generator.py
    ```

6. Move the images/ folder into /kindle_clock/literary_clock/.

***

Next, you need to jailbreak your Kindle If you have already done this and have KUAL installed, skip to step 5.

Since the type of jailbreak you need varies depending on the type of Kindle you have, follow the [Kindle Modding Wiki’s Guides](https://kindlemodding.org/jailbreaking/index.html). While following the guide, make sure that steps 1-4 are completed.

1. Install a jailbreak (e.g., WinterBreak or AdBreak)
2. Install a hotfix, if needed. This is dependent on your Kindle. 
3. Install (Kindle Unified Application Launcher) and MRPI (MobileRead Package Installer)
    - *(Optional)*: Instead of downloading KUAL and MRPI from the wiki, install [PEKI](https://kindlemodshelf.me/peki) for a cleaner look. “PEKI installs and launches KUAL without MRPI, delivers a polished icon, and keeps Kindle mod setups dependable.”
4. Disable OTA (Over-the-Air) updates. These can cause the jailbreak to be removed from your Kindle.
<!--5. Install the FBInk binary from NiLuJe’s [forum post](https://www.mobileread.com/forums/showthread.php?t=299620). Extract the folder from the zipped file and move -->
5. (Optional) Install USBNet(Lite) from notemarek’s [repository](https://github.com/notmarek/kindle-usbnetlite/tree/master). This will allow you to SSH into your kindle and easily transfer files to it.
    - Once it is installed, open KUAL and select `USBNetLite`
    - Select `* Toggle USBNetwork *` to enable SSH.
    - Exit out of KUAL and in the Kindle’s search bar, search for `;711`. On this page, you will be able to find your Kindle’s IP address. 
    - To SSH into the Kindle, enter `ssh root@[kindle’s IP addr]`. The password is `kindle`.
6. Next, install j.p.s’s [Sleep Disable/Enable KUAL+ extensions](https://www.mobileread.com/forums/showthread.php?t=293264) to prevent the screen from going to sleep. Download both the sleepDisable and sleepEnable files from the thread. When you extract each file, you will get an "extenstions" folder, which has a "sleep_disable"/"sleep_enable" folder. Move the sleep_disable and sleep_enable folders to the Kindle in /mnt/us/extensions.

7. To prevent the screen from going to sleep, open KUAL, select `Helper+`, and select sleep disable.

8. Move the /literary_clock/ folder from the local repository into /mnt/us/.

9. Move the literary_clock.sh file out of the /literary_clock/ folder and into /mnt/us/documents. Next time you turn on the Kindle, the clock should show up in your library. To start it, click on the book as if you were opening it!

## How to Turn the Clock Off

1. Swipe down on the screen to open to Quick Settings panel, then exit this panel. This will bring you back to the Home screen.
2. Select on the Literary Quote Clock thumbnail in your library. This will turn the clock off. To turn it back on, simply click on the Clock’s thumbnail in your library again.