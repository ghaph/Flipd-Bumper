import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import os
import time
import threading
import json
import random

# login page
turnstileSelector = 'document.querySelector("#cf-stage > div.ctp-checkbox-container > label")?.click()'
usernameSelector = '#fullcontainment > div > form:nth-child(2) > div > div.container.mt-4 > div > div.col-md-6.bg-container.py-4.px-5.rounded-right.rounded-xs > div > span > div:nth-child(1) > span > label > input'
passwordSelector = '#fullcontainment > div > form:nth-child(2) > div > div.container.mt-4 > div > div.col-md-6.bg-container.py-4.px-5.rounded-right.rounded-xs > div > span > div:nth-child(3) > label > input'
mfaFieldSelector = '#fullcontainment > div > form:nth-child(2) > div > div.container.mt-4 > div > div.col-md-6.bg-container.py-4.px-5.rounded-right.rounded-xs > div > span > div:nth-child(5) > label > input'
loginButtonSelector = '#fullcontainment > div > form:nth-child(2) > div > div.container.mt-4 > div > div.col-md-6.bg-container.py-4.px-5.rounded-right.rounded-xs > div > span > button'

# logged in
vouchesSelector = '#fullcontainment > div.wraps > div.forum_sidebar > div.responsivehide.sidebarstats.drop-shadow-lg > div:nth-child(2) > div:nth-child(2) > strong > a'
repSelector = '#fullcontainment > div.wraps > div.forum_sidebar > div.responsivehide.sidebarstats.drop-shadow-lg > div:nth-child(2) > div:nth-child(1) > strong > a'
loggedInUsernameSelector = '#fullcontainment > div.wraps > div.forum_sidebar > div.responsivehide.sidebarstats.drop-shadow-lg > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > a'
likesSelector = '#fullcontainment > div.wraps > div.forum_sidebar > div.responsivehide.sidebarstats.drop-shadow-lg > div:nth-child(2) > div:nth-child(3) > strong'

# thread page
replyMessageSelector = '#message'
postReplySelector = '#quick_reply_submit'

with open('config.json') as f:
    config = json.load(f)

if len(config['threads']) == 0:
    print('No threads to bump')
    exit()

for x in range(3):
    print('DO NOT TOUCH THE BROWSER WINDOW!')

thread_ids = []
msg_index = 0

def get_message():
    global msg_index

    messages = config['messages']

    msg_index += 1
    if msg_index >= len(messages):
        msg_index = 0

    msg = messages[msg_index]

    msg += f' [{random.randint(1000, 9999)}]'

    return msg

def log(msg: str):
    t = time.strftime('%H:%M:%S', time.localtime())
    print(f'[{t}] {msg}')

def login():
    global thread_ids

    # check if custom chrome driver exists
    path = None
    if os.path.exists('chromedriver.exe'):
        path = 'chromedriver.exe'
    elif os.path.exists('chromedriver'):
        path = 'chromedriver'
    elif os.path.exists('/usr/bin/chromedriver'):
        path = '/usr/bin/chromedriver'

    options = uc.ChromeOptions()

    if 'user_agent' in config:
        options.add_argument(f'user-agent={config["user_agent"]}')

    # set window to 1920x1080
    options.add_argument('--window-size=1920,1080')

    binary_locations = [
        '/snap/bin/brave',
        '/usr/bin/chromium-browser',
        'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
    ]

    for loc in binary_locations:
        if os.path.exists(loc):
            options.binary_location = loc
            break

    driver = uc.Chrome(driver_executable_path=path, options=options)
    log('Driver started')

    # i was jsut testing. i dont think setting this does anything meaningful
    if 'clearance' in config:
        # get flipd to apply the clearance cookie
        driver.get('https://flipd.gg')

        driver.add_cookie({
            'domain': '.flipd.gg',
            'hostOnly': False,
            'httpOnly': True,
            'name': 'cf_clearance',
            'path': '/',
            'sameSite': 'None',
            'secure': True,
            'value': config['clearance'],
        })
        log('Applied clearance cookie')

    # very hit or miss. doesnt seem to bypass turnstile always
    def check_turnstile():
        try:
            # get all frames
            frames = driver.find_elements(By.TAG_NAME, 'iframe')
            if len(frames) == 0:
                return
            
            for frame in frames:
                src = frame.get_attribute('src')
                log(f'Found iframe: {src}')

                # make sure its a turnstile iframe
                if not 'challenges.cloudflare.com' in src:
                    continue

                log('Found turnstile iframe')

                # switch to frame
                driver.switch_to.frame(frame)

                # click checkbox
                driver.execute_script(turnstileSelector)
                log('Clicked turnstile checkbox')

                time.sleep(0.5)

                # save screenshot for debug
                driver.save_screenshot('turnstile.png')

                driver.switch_to.default_content()
                return
        except:
            pass

        driver.switch_to.default_content()

    driver.get('https://flipd.gg/member.php?action=login')
    log('Opened login page')

    def restart():
        driver.quit()
        time.sleep(2)
        threading.Thread(target=login).start()

    start = time.time()
    found = False
    while time.time() - start < 60:
        try:
            driver.find_element(By.CSS_SELECTOR, usernameSelector).send_keys(config['username'])
            found = True
            break
        except:
            # take screenshot
            driver.save_screenshot('error.png')

            check_turnstile()

            time.sleep(1)
    
    if not found:
        log('Could not find username field')
        restart()
        return
    
    log('Found username field')
    
    # if username field exists password field should also exist
    try:
        driver.find_element(By.CSS_SELECTOR, passwordSelector).send_keys(config['password'])
    except:
        log('Could not find password field')
        restart()
        return
    
    if config['2fa']:
        code = input('Enter 2FA code: ')
        try:
            driver.find_element(By.CSS_SELECTOR, mfaFieldSelector).send_keys(code)
        except:
            log('Could not find 2FA field')
            restart()
            return
        
    log('Logging in...')

    try:
        driver.find_element(By.CSS_SELECTOR, loginButtonSelector).click()
    except:
        log('Could not find login button')
        restart()
        return
    
    log('Logged in')
    
    try:
        username = driver.find_element(By.CSS_SELECTOR, loggedInUsernameSelector).text
        rep = driver.find_element(By.CSS_SELECTOR, repSelector).text
        vouches = driver.find_element(By.CSS_SELECTOR, vouchesSelector).text
        likes = driver.find_element(By.CSS_SELECTOR, likesSelector).text

        print(f'[{username}] Rep: {rep} | Vouches: {vouches} | Likes: {likes}')
    except:
        log('Could not find username, vouches or rep. Most likely an invalid login')
        restart()
        return
    
    try:
        # find all thread ids
        if len(thread_ids) < len(config['threads']):
            for thread in config['threads']:

                # allow for inputting thread ids straight into config
                if type(thread) == int:
                    thread_ids.append(thread)
                    continue

                raw_thread = thread.lower().replace('https://flipd.gg/thread-', '')
                thread = 'https://flipd.gg/thread-' + raw_thread

                driver.get(thread)
                source = driver.page_source
                if not 'https://flipd.gg/showthread.php?tid=' in source:
                    log(f'Invalid thread: {thread}')
                    continue

                id = source.split('https://flipd.gg/showthread.php?tid=')[1].split('"')[0]
                thread_ids.append(id)

                log(f'[{raw_thread}] Thread ID: {id}')
        
        log('Starting bumper...')

        total_errors = 0 
        while True:
            for id in thread_ids:
                # ogu rate limit
                if id != thread_ids[0]:
                    time.sleep(15)

                try:
                    driver.get('https://flipd.gg/showthread.php?tid=' + str(id))

                    msg = get_message()

                    driver.find_element(By.CSS_SELECTOR, replyMessageSelector).send_keys(msg)
                    driver.find_element(By.CSS_SELECTOR, postReplySelector).click()
                    total_errors = 0

                    log(f'[{id}] Bumped thread: {msg}')
                except Exception as e:
                    print(e)

                    check_turnstile()

                    total_errors += 1
                    if total_errors >= 10:
                        print('Too many errors, restarting')
                        restart()
                        return

            time.sleep(int(config['interval']) * 60)
    except Exception as e:
        log(e)
        restart()
        return

if __name__ == '__main__':
    login()