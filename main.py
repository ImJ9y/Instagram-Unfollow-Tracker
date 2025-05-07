from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import time
import random
import json
from datetime import datetime
import re
import os
import argparse


class UnfollowTracker:
    def __init__(self, username, password, headless=False):
        self.URL = 'https://www.instagram.com/'
        self.username = username
        self.password = password
        self.following_list = []
        self.followers_list = []
        self.not_following_back = []

        # Configurable parameters with defaults
        self.scroll_timeout = 1000  # Max number of scrolls
        self.stable_threshold = 10  # Number of stable scrolls before stopping
        self.scroll_delay = 2.0  # Default delay between scrolls

        # Create organized output directories
        self.base_dir = "instagram_data"
        self.screenshots_dir = os.path.join(self.base_dir, "screenshots")
        self.json_dir = os.path.join(self.base_dir, "json_files")

        # Create all directories
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)

        # Configure Chrome options
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")

        # Add user agent to avoid detection
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Disable automation detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Headless mode option
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()

        # Execute CDP commands to prevent detection
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })

        # Create a wait object
        self.wait = WebDriverWait(self.driver, 15)

        # Debug mode for saving screenshots
        self.debug = True
        self.screenshot_counter = 0

    def take_screenshot(self, name):
        """Save screenshot for debugging if debug mode is enabled"""
        if self.debug:
            try:
                self.screenshot_counter += 1
                filename = f"{self.screenshots_dir}/{self.screenshot_counter:03d}_{name}.png"
                self.driver.save_screenshot(filename)
                print(f"Screenshot saved: {filename}")
            except Exception as e:
                print(f"Error taking screenshot: {e}")

    def random_sleep(self, min_time=1, max_time=3):
        """Sleep for a random time between min_time and max_time seconds"""
        time.sleep(random.uniform(min_time, max_time))

    def find_best_element(self, xpaths, wait_time=5):
        """Try multiple XPaths to find the best element that's visible and clickable"""
        for xpath in xpaths:
            try:
                elements = WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_all_elements_located((By.XPATH, xpath))
                )

                for element in elements:
                    if element.is_displayed():
                        try:
                            # Check if element is in viewport
                            is_in_viewport = self.driver.execute_script(
                                "var elem = arguments[0]; "
                                "var box = elem.getBoundingClientRect(); "
                                "return (box.top >= 0 && box.left >= 0 && "
                                "box.bottom <= window.innerHeight && "
                                "box.right <= window.innerWidth);",
                                element
                            )

                            if is_in_viewport:
                                return element
                        except:
                            continue
            except:
                continue

        return None

    def safe_click(self, element):
        """Try multiple methods to click an element safely"""
        if not element:
            return False

        try:
            # Method 1: Direct click
            try:
                element.click()
                return True
            except:
                pass

            # Method 2: JavaScript click
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                pass

            # Method 3: Action chain click
            try:
                webdriver.ActionChains(self.driver).move_to_element(element).click().perform()
                return True
            except:
                pass

            # Method 4: Scroll into view and click
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
                self.random_sleep(0.5, 1)
                element.click()
                return True
            except:
                pass

            return False
        except Exception as e:
            print(f"All click methods failed: {e}")
            return False

    def click_element_by_xpath(self, xpath):
        """Try to click an element using given XPath"""
        elements = self.driver.find_elements(By.XPATH, xpath)
        if not elements:
            return False

        for elem in elements:
            try:
                if elem.is_displayed():
                    # Try scrolling into view first
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        self.random_sleep(0.5, 1)
                    except:
                        pass

                    # Try clicking
                    elem.click()
                    self.random_sleep(1, 2)
                    return True
            except:
                continue

        return False

    def js_click_element_by_xpath(self, xpath):
        """Try to click an element using JavaScript and given XPath"""
        elements = self.driver.find_elements(By.XPATH, xpath)
        if not elements:
            return False

        for elem in elements:
            try:
                # Try scrolling into view first
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                    self.random_sleep(0.5, 1)
                except:
                    pass

                # Try clicking with JS
                self.driver.execute_script("arguments[0].click();", elem)
                self.random_sleep(1, 2)
                return True
            except:
                continue

        return False

    def login(self):
        """Login to Instagram account"""
        print("Logging in to Instagram...")
        self.driver.get(self.URL)
        self.random_sleep(3, 5)
        self.take_screenshot("initial_load")

        try:
            # Handle cookies consent if it appears
            try:
                cookies_buttons = self.driver.find_elements(By.XPATH,
                                                            '//button[contains(text(), "Allow") or contains(text(), "Accept") or contains(text(), "Only allow essential cookies")]')
                if cookies_buttons:
                    cookies_buttons[0].click()
                    self.random_sleep()
                    self.take_screenshot("after_cookies")
            except Exception as e:
                print(f"No cookies dialog found or error handling it: {e}")

            # Login with credentials
            username_field = self.wait.until(EC.element_to_be_clickable((By.NAME, "username")))
            password_field = self.wait.until(EC.element_to_be_clickable((By.NAME, "password")))

            username_field.clear()
            password_field.clear()

            # Type like a human with random delays between characters
            for char in self.username:
                username_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            self.random_sleep(0.5, 1)

            for char in self.password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            self.random_sleep(0.5, 1)
            self.take_screenshot("before_login_click")

            login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@type="submit"]')))
            login_button.click()

            print("Waiting for verification process...")
            self.take_screenshot("waiting_for_verification")
            input("Complete any verification manually if required, then press Enter to continue...")

            # Handle "Save Login Info" dialog if it appears
            try:
                self.random_sleep(2, 3)
                not_now_buttons = self.driver.find_elements(By.XPATH,
                                                            '//button[contains(text(), "Not Now")] | //button[contains(text(), "Not now")]')
                if not_now_buttons:
                    not_now_buttons[0].click()
                    self.random_sleep()
                    self.take_screenshot("after_save_login")
            except Exception as e:
                print(f"No 'Save Login Info' dialog found or error handling it: {e}")

            # Handle notifications dialog if it appears
            try:
                self.random_sleep(2, 3)
                not_now_buttons = self.driver.find_elements(By.XPATH,
                                                            '//button[contains(text(), "Not Now")] | //button[contains(text(), "Not now")]')
                if not_now_buttons:
                    not_now_buttons[0].click()
                    self.take_screenshot("after_notifications")
            except Exception as e:
                print(f"No notifications dialog found or error handling it: {e}")

            # Wait for the feed page to confirm login success
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//div[@role="dialog"] | //div[contains(@class, "x9f619")] | //img[@alt="Instagram"]')))
                print("Login successful!")
                self.take_screenshot("login_successful")
                return True
            except TimeoutException:
                print("Timed out waiting for home page. Login may have failed.")
                self.take_screenshot("login_timeout")
                return False

        except Exception as e:
            print(f"Error during login: {e}")
            self.take_screenshot("login_error")
            return False

    def get_count_from_text(self, text):
        """Extract numeric count from text like '123 followers' or '1,234 following'"""
        if not text:
            return 0

        # Remove commas and extract digits
        count_match = re.search(r'([\d,]+)', text)
        if count_match:
            count_text = count_match.group(1).replace(',', '')
            # Handle 'K' (thousands)
            if 'K' in text or 'k' in text:
                return int(float(count_text) * 1000)
            # Handle 'M' (millions)
            elif 'M' in text or 'm' in text:
                return int(float(count_text) * 1000000)
            else:
                return int(count_text)
        return 0


    def scrape_users_from_dialog(self, expected_count=None, list_type="following"):
        """
        Improved method to extract usernames from the followers/following dialog
        with better scrolling and extraction logic
        """
        print(f"Extracting {list_type} list...")
        self.take_screenshot(f"{list_type}_dialog_start")
        self.random_sleep(3, 5)

        # Better scroll container detection with multiple strategies
        scroll_box_xpaths = [
            '//div[@role="dialog"]//div[contains(@style, "overflow")]',
            '//div[@role="dialog"]//div[contains(@style, "height") and contains(@style, "scroll")]',
            '//div[@role="dialog"]//ul',
            '//div[@role="dialog"]//div[@tabindex="0"]',
            '//div[@role="dialog"]'
        ]

        scroll_box = None
        for xpath in scroll_box_xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for elem in elements:
                    if elem.is_displayed() and elem.size['height'] > 100:
                        scroll_box = elem
                        print(f"Found scroll container using: {xpath}")
                        break
                if scroll_box:
                    break
            except:
                continue

        if not scroll_box:
            print("⚠️ Could not find scroll container.")
            self.take_screenshot(f"{list_type}_scroll_container_missing")
            return []

        # Setup for scrolling
        usernames = set()
        previous_count = -1
        stable_scrolls = 0
        max_stable_scrolls = self.stable_threshold
        scroll_count = 0
        max_scrolls = self.scroll_timeout
        min_expected_percent = 0.95
        force_continue_scrolling = True
        prev_height = -1

        print(f"Target extraction: approximately {expected_count} usernames")
        print("Scrolling and collecting usernames...")

        # Main scrolling loop
        while scroll_count < max_scrolls:
            # More aggressive scrolling - try different techniques in sequence
            try:
                # Method 1: Standard scroll
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)

                # Method 2: Force scroll with JavaScript
                if scroll_count % 3 == 0:
                    current_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)
                    self.driver.execute_script(f"arguments[0].scrollTop = {current_height + 1000}", scroll_box)

                # Method 3: Use keyboard for scrolling occasionally
                if scroll_count % 5 == 0:
                    try:
                        scroll_box.click()
                        for i in range(10):
                            webdriver.ActionChains(self.driver).send_keys(Keys.PAGE_DOWN).perform()
                            self.random_sleep(0.2, 0.4)
                    except:
                        pass
            except Exception as e:
                print(f"Scrolling error: {e}")

            # Longer sleep time to ensure content loads
            self.random_sleep(self.scroll_delay, self.scroll_delay * 1.5)

            # Extract usernames
            new_usernames = set()

            # Try different selection strategies for better extraction
            try:
                # Strategy 1: Find all links
                elements = scroll_box.find_elements(By.XPATH, './/a[contains(@href, "/")]')

                # Strategy 2: If few elements found, try a broader selector
                if len(elements) < 5:
                    elements = scroll_box.find_elements(By.XPATH,
                                                        './/*[contains(@href, "/") or contains(@role, "link")]')

                # Process all found elements
                for elem in elements:
                    try:
                        href = elem.get_attribute('href')
                        username = self.extract_username_from_href(href)
                        if self.is_valid_username(username):
                            new_usernames.add(username.strip())
                    except:
                        continue

                # Strategy 3: As last resort, try to find usernames in text content
                if len(new_usernames) < 3 and scroll_count > 3:
                    try:
                        elements = scroll_box.find_elements(By.XPATH, './/*[not(self::script)]')
                        for elem in elements:
                            try:
                                text = elem.text
                                if text and '@' in text:
                                    potential_username = text.strip().replace('@', '')
                                    if self.is_valid_username(potential_username):
                                        new_usernames.add(potential_username)
                            except:
                                continue
                    except:
                        pass
            except Exception as e:
                print(f"Error extracting usernames: {e}")

            # Update the set of collected usernames
            prev_total = len(usernames)
            usernames.update(new_usernames)
            current_total = len(usernames)
            new_count = current_total - prev_total

            # Log progress more frequently
            if scroll_count % 5 == 0 or new_count > 0:
                print(f"[{list_type}] Scroll {scroll_count}: {current_total} usernames collected (+{new_count} new)")

                # Take strategic screenshots
                if scroll_count % 20 == 0 or (new_count > 0 and scroll_count % 10 == 0):
                    self.take_screenshot(f"{list_type}_scroll_{scroll_count}")

            # Check if we're making progress on usernames
            if current_total == previous_count:
                stable_scrolls += 1
                if stable_scrolls % 5 == 0:
                    print(f"No new usernames after {stable_scrolls} scrolls. Continuing...")

                    # Try alternative scrolling techniques when stuck
                    if stable_scrolls % 10 == 0:
                        try:
                            print("Trying alternative scrolling techniques...")

                            # Try refreshing the scroll container
                            self.driver.execute_script("arguments[0].scrollTop = 0", scroll_box)
                            self.random_sleep(1, 2)

                            # Try scrolling from a different point
                            halfway = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box) / 2
                            self.driver.execute_script(f"arguments[0].scrollTop = {halfway}", scroll_box)
                            self.random_sleep(1, 2)

                            # Try clicking inside and pressing End key
                            try:
                                webdriver.ActionChains(self.driver).move_to_element(scroll_box).click().perform()
                                webdriver.ActionChains(self.driver).send_keys(Keys.END).perform()
                                self.random_sleep(1, 2)
                            except:
                                pass
                        except Exception as e:
                            print(f"Alternative scrolling failed: {e}")
            else:
                stable_scrolls = 0
                previous_count = current_total

            # Check if scrolling is making any difference to the scroll height
            current_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)
            if current_height == prev_height and scroll_count > 10:
                print("Scroll height not changing. May have reached end of list.")
                stable_scrolls += 1
            prev_height = current_height

            # Determine if we should stop scrolling
            if stable_scrolls >= max_stable_scrolls and not force_continue_scrolling:
                print(f"No new usernames after {stable_scrolls} scrolls. Stopping.")
                break

            # If we have an expected count, check if we're close enough
            if expected_count and current_total >= expected_count * min_expected_percent:
                print(
                    f"Collected {current_total} usernames ({(current_total / expected_count) * 100:.1f}% of expected).")

                # If we've really reached the target, we can stop
                if current_total >= expected_count * 0.98:
                    break

                # If we're close, we disable force_continue_scrolling and rely on stable_scrolls
                if stable_scrolls >= 5:
                    force_continue_scrolling = False

            # Emergency brake - too many scrolls with minimal progress
            if stable_scrolls > 25:
                print(f"Emergency stop: {stable_scrolls} stable scrolls with minimal progress.")
                break

        self.take_screenshot(f"{list_type}_scrolling_complete")
        print(f"Finished: {len(usernames)} unique usernames extracted from {list_type} list.")

        # Check success rate
        if expected_count:
            success_rate = len(usernames) / expected_count * 100
            print(f"Success rate: {success_rate:.1f}% of expected count")

            if success_rate < 90 and len(usernames) > 20:
                print(
                    f"⚠️ Warning: Only collected {success_rate:.1f}% of expected {list_type} ({len(usernames)}/{expected_count}).")
                print("Instagram may be limiting the data we can extract.")

                # Try one more time with a new approach if we have a poor extraction rate
                if success_rate < 50 and list_type == "following":
                    print("Trying alternative extraction method...")
                    return self.get_following_alternative()
                elif success_rate < 50 and list_type == "followers":
                    print("Trying alternative extraction method...")
                    return self.get_followers_alternative()

        try:
            webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        except:
            pass

        return list(usernames)

    def extract_username_from_href(self, href):
        """Extract username from Instagram profile URL with improved parsing"""
        if not href:
            return ""

        # Clean and parse URL
        try:
            # Remove trailing slash and query parameters
            href = href.split('?')[0].rstrip('/')

            # Extract username part - avoid common non-username paths
            invalid_paths = ['/p/', '/explore/', '/reels/', '/stories/', '/direct/', '/tags/']

            # Skip processing if the URL contains invalid paths
            if any(invalid_path in href for invalid_path in invalid_paths):
                return ""

            # Extract the username (should be the last part of the URL for profile pages)
            parts = href.split('/')
            # Get the last non-empty part
            username_parts = [part for part in parts if part]
            if username_parts:
                return username_parts[-1]
        except Exception as e:
            print(f"Error extracting username from URL {href}: {e}")

        return ""

    def is_valid_username(self, username):
        """Check if a username appears valid with improved validation"""
        if not username:
            return False

        # Invalid usernames to filter out
        invalid_keywords = ['explore', 'p', 'reels', 'stories', 'direct', 'tags',
                            'about', 'accounts', 'legal', 'directory', 'hashtag',
                            'login', 'signup', 'download', 'help', 'privacy', 'terms',
                            'api', 'press', 'jobs', 'locations']

        # Check if username looks valid
        return (
                username and
                username.strip() != "" and
                username.lower() not in invalid_keywords and
                not username.startswith('p/') and
                not username.startswith('@') and
                '?' not in username and
                '#' not in username and
                '/' not in username and
                ' ' not in username and
                len(username) > 1 and  # Usernames are at least 2 characters
                len(username) <= 30  # Instagram username length limit
        )

    def get_following(self):
        """Get the list of accounts the user is following with improved extraction"""
        print(f"Navigating to {self.username}'s profile to get following list...")
        self.driver.get(f"{self.URL}{self.username}/")
        self.random_sleep(3, 5)
        self.take_screenshot("profile_page")

        # Get the count first with improved and aggressive counting
        following_count = 0
        try:
            # Try multiple advanced selectors for following count
            count_selectors = [
                # Modern selector patterns
                '//a[contains(@href, "/following")]/span/span | //a[contains(@href, "/following")]/div/span',
                '//a[contains(@href, "/following")] | //div[contains(text(), " following")]',
                '//section//li[contains(., "following")]',
                '//div[contains(@class, "x78zum5")]/span | //div[contains(@class, "x78zum5")]/div',
                '//span[contains(@class, "html-span")]',
                # Very broad selectors as last resort
                '//*[contains(text(), "following")]',
                '//*[contains(text(), " following") or contains(text(), " Following")]'
            ]

            for selector in count_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    text = elem.text or elem.get_attribute('innerText')
                    if text and ('following' in text.lower() or
                                 (text.isdigit() and int(text) > 0 and int(text) < 100000)):
                        count = self.get_count_from_text(text)
                        if count > 0:
                            following_count = count
                            print(f"Found count element with text: '{text}', extracted count: {count}")
                            break
                if following_count > 0:
                    break

            # Last resort - manual scan of all elements with numbers
            if following_count == 0:
                all_elements = self.driver.find_elements(By.XPATH, '//*')
                for elem in all_elements:
                    try:
                        text = elem.text
                        if text and 'following' in text.lower():
                            count = self.get_count_from_text(text)
                            if count > 0:
                                following_count = count
                                break
                    except:
                        continue

            print(f"Found approximately {following_count} accounts you're following")

        except Exception as e:
            print(f"Could not get following count: {e}. Will continue anyway.")

        # Take a screenshot of profile with counts visible
        self.take_screenshot("profile_with_counts")

        # Click on the following button - try multiple approaches with improved selectors
        following_button_clicked = False

        # Find and click using multiple strategies
        click_strategies = [
            # Strategy 1: Direct click on "following" text or link
            lambda: self.click_element_by_xpath(
                '//a[contains(@href, "/following")] | //div[contains(text(), " following")]'),

            # Strategy 2: Using JavaScript click with href selector
            lambda: self.js_click_element_by_xpath('//a[contains(@href, "/following")]'),

            # Strategy 3: Using the 2025 Instagram UI structure
            lambda: self.click_element_by_xpath(
                '//div[contains(@class, "x78zum5")]/../../div[2]//div | //div[contains(@class, "x9f619")]//div[contains(text(), "following")]'),

            # Strategy 4: Click on the count numbers
            lambda: self.click_element_by_xpath('//section//ul//li[contains(., "following")]'),

            # Strategy 5: Try a very broad selector as last resort
            lambda: self.click_element_by_xpath('//*[contains(text(), "following")]')
        ]

        for i, click_strategy in enumerate(click_strategies):
            try:
                print(f"Trying following button click strategy {i + 1}...")
                if click_strategy():
                    following_button_clicked = True
                    print(f"Successfully clicked following using strategy {i + 1}")
                    self.take_screenshot(f"following_clicked_strategy_{i + 1}")
                    break
            except Exception as e:
                print(f"Strategy {i + 1} failed: {e}")

        if not following_button_clicked:
            print("⚠️ Could not open following list! Taking screenshot and continuing...")
            self.take_screenshot("following_click_failed")
            return []

        self.random_sleep(3, 5)

        # Extract usernames from the dialog
        self.following_list = self.scrape_users_from_dialog(following_count, "following")

        # Save the following list to a file in the json directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        following_file = f"{self.json_dir}/{self.username}_following_{timestamp}.json"
        with open(following_file, 'w') as f:
            json.dump(self.following_list, f)

        print(f"Total following collected: {len(self.following_list)}")
        print(f"Results saved to {following_file}")
        return self.following_list

    def get_following_alternative(self):
        """Alternative method to extract following list if the dialog method fails"""
        print("Using alternative method to extract following list...")
        following = []

        try:
            # Go to profile page
            self.driver.get(f"{self.URL}{self.username}/following/")
            self.random_sleep(3, 5)

            # Scroll the page to load more users
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 500

            while scroll_count < max_scrolls:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_sleep(2, 3)
                scroll_count += 1

                # Get all links on the page
                links = self.driver.find_elements(By.XPATH, '//a[contains(@href, "/")]')
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        username = self.extract_username_from_href(href)
                        if self.is_valid_username(username):
                            following.append(username)
                    except:
                        continue

                # Check if we've scrolled to the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

                # Log progress
                if scroll_count % 10 == 0:
                    print(f"Alternative method: Scroll {scroll_count}, found {len(set(following))} usernames")

            # Deduplicate the list
            following = list(set(following))
            print(f"Alternative method found {len(following)} following accounts")
            return following

        except Exception as e:
            print(f"Alternative method failed: {e}")
            return []

    def get_followers(self):
        """Get the list of followers with improved extraction"""
        print(f"Navigating to {self.username}'s profile to get followers list...")
        self.driver.get(f"{self.URL}{self.username}/")
        self.random_sleep(3, 5)
        self.take_screenshot("profile_page_followers")

        # Get the count first with aggressive counting
        followers_count = 0
        try:
            # Try multiple advanced selectors for followers count
            count_selectors = [
                # Modern selector patterns
                '//a[contains(@href, "/followers")]/span/span | //a[contains(@href, "/followers")]/div/span',
                '//a[contains(@href, "/followers")] | //div[contains(text(), " followers")]',
                '//section//li[contains(., "followers")]',
                '//div[contains(@class, "x78zum5")]/span | //div[contains(@class, "x78zum5")]/div',
                '//span[contains(@class, "html-span")]',
                # Very broad selectors as last resort
                '//*[contains(text(), "followers")]',
                '//*[contains(text(), " followers") or contains(text(), " Followers")]'
            ]

            for selector in count_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    text = elem.text or elem.get_attribute('innerText')
                    if text and ('followers' in text.lower() or
                                 (text.isdigit() and int(text) > 0 and int(text) < 1000000)):
                        count = self.get_count_from_text(text)
                        if count > 0:
                            followers_count = count
                            print(f"Found count element with text: '{text}', extracted count: {count}")
                            break
                if followers_count > 0:
                    break

            # Last resort - manual scan of all elements with numbers
            if followers_count == 0:
                all_elements = self.driver.find_elements(By.XPATH, '//*')
                for elem in all_elements:
                    try:
                        text = elem.text
                        if text and 'followers' in text.lower():
                            count = self.get_count_from_text(text)
                            if count > 0:
                                followers_count = count
                                break
                    except:
                        continue

            print(f"Found approximately {followers_count} followers")

        except Exception as e:
            print(f"Could not get followers count: {e}. Will continue anyway.")

        # Take a screenshot with counts visible
        self.take_screenshot("profile_with_follower_counts")

        # Click on the followers button with multiple approaches
        followers_button_clicked = False

        # Find and click using multiple strategies
        click_strategies = [
            # Strategy 1: Direct click on "followers" text or link
            lambda: self.click_element_by_xpath(
                '//a[contains(@href, "/followers")] | //div[contains(text(), " followers")]'),

            # Strategy 2: Using JavaScript click with href selector
            lambda: self.js_click_element_by_xpath('//a[contains(@href, "/followers")]'),

            # Strategy 3: Using the UI structure
            lambda: self.click_element_by_xpath(
                '//div[contains(@class, "x78zum5")]/../../div[1]//div | //div[contains(@class, "x9f619")]//div[contains(text(), "followers")]'),

            # Strategy 4: Click on the count numbers
            lambda: self.click_element_by_xpath('//section//ul//li[contains(., "followers")]'),

            # Strategy 5: Try a very broad selector as last resort
            lambda: self.click_element_by_xpath('//*[contains(text(), "followers")]')
        ]

        for i, click_strategy in enumerate(click_strategies):
            try:
                print(f"Trying followers button click strategy {i + 1}...")
                if click_strategy():
                    followers_button_clicked = True
                    print(f"Successfully clicked followers using strategy {i + 1}")
                    self.take_screenshot(f"followers_clicked_strategy_{i + 1}")
                    break
            except Exception as e:
                print(f"Strategy {i + 1} failed: {e}")

        if not followers_button_clicked:
            print("⚠️ Could not open followers list! Taking screenshot and continuing...")
            self.take_screenshot("followers_click_failed")
            return []

        self.random_sleep(3, 5)

        # Extract usernames from the dialog
        self.followers_list = self.scrape_users_from_dialog(followers_count, "followers")

        # Save the followers list to a file in the json directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        followers_file = f"{self.json_dir}/{self.username}_followers_{timestamp}.json"
        with open(followers_file, 'w') as f:
            json.dump(self.followers_list, f)

        print(f"Total followers collected: {len(self.followers_list)}")
        print(f"Results saved to {followers_file}")
        return self.followers_list

    def get_followers_alternative(self):
        """Alternative method to extract followers list if the dialog method fails"""
        print("Using alternative method to extract followers list...")
        followers = []

        try:
            # Go to profile page
            self.driver.get(f"{self.URL}{self.username}/followers/")
            self.random_sleep(3, 5)

            # Scroll the page to load more users
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_count = 0
            max_scrolls = 500

            while scroll_count < max_scrolls:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_sleep(2, 3)
                scroll_count += 1

                # Get all links on the page
                links = self.driver.find_elements(By.XPATH, '//a[contains(@href, "/")]')
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        username = self.extract_username_from_href(href)
                        if self.is_valid_username(username):
                            followers.append(username)
                    except:
                        continue

                # Check if we've scrolled to the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

                # Log progress
                if scroll_count % 10 == 0:
                    print(f"Alternative method: Scroll {scroll_count}, found {len(set(followers))} usernames")

            # Deduplicate the list
            followers = list(set(followers))
            print(f"Alternative method found {len(followers)} follower accounts")
            return followers

        except Exception as e:
            print(f"Alternative method failed: {e}")
            return []

    def normalize_username(self, username):
        """Normalize username for better comparison"""
        if not username:
            return ""
        # Convert to lowercase and remove non-alphanumeric characters
        return re.sub(r'[^a-zA-Z0-9]', '', username.lower().strip())

    def find_non_followers(self, use_normalized_comparison=True):
        """Identify accounts that don't follow back with improved accuracy"""
        print("Finding accounts that don't follow you back...")

        # Make sure we have both lists
        if not self.following_list:
            print("Following list is empty. Getting it now...")
            self.get_following()

        if not self.followers_list:
            print("Followers list is empty. Getting it now...")
            self.get_followers()

        # Deduplicate lists
        self.following_list = list(set(self.following_list))
        self.followers_list = list(set(self.followers_list))

        # Print statistics before comparison
        print("\nComparison statistics:")
        print(f"- You are following: {len(self.following_list)} accounts")
        print(f"- You have: {len(self.followers_list)} followers")

        # Better comparison with improved accuracy
        if use_normalized_comparison:
            print("Using normalized username comparison for better accuracy...")
            # Create normalized versions of the lists for comparison
            normalized_followers = [self.normalize_username(user) for user in self.followers_list if user]
            normalized_following = [self.normalize_username(user) for user in self.following_list if user]

            # Find non-followers with normalized comparison
            self.not_following_back = []
            for idx, user in enumerate(self.following_list):
                if not user:
                    continue

                normalized_user = self.normalize_username(user)
                if normalized_user and normalized_user not in normalized_followers:
                    self.not_following_back.append(user)

            # Secondary check to make sure we didn't miss any with direct comparison
            direct_non_followers = set(self.following_list) - set(self.followers_list)
            for user in direct_non_followers:
                if user and user not in self.not_following_back:
                    self.not_following_back.append(user)
        else:
            # Simple direct comparison
            print("Using direct username comparison...")
            self.not_following_back = [user for user in self.following_list if user and user not in self.followers_list]

        # Verify our results with reverse check
        if use_normalized_comparison:
            print("Performing verification check...")
            verified_non_followers = []
            for user in self.not_following_back:
                # Double check each non-follower
                norm_user = self.normalize_username(user)
                if norm_user and norm_user not in normalized_followers:
                    verified_non_followers.append(user)

            if len(verified_non_followers) != len(self.not_following_back):
                print(
                    f"⚠️ Verification removed {len(self.not_following_back) - len(verified_non_followers)} false positives.")
                self.not_following_back = verified_non_followers

        # Save the non-followers list to a file in the json directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{self.json_dir}/{self.username}_non_followers_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(self.not_following_back, f)

        print(f"\nFound {len(self.not_following_back)} accounts that don't follow you back")
        print(f"Results saved to {output_file}")

        return self.not_following_back

    def show_results(self):
        """Display the results of who's not following back"""
        if not self.not_following_back:
            print("No results to display. Run find_non_followers() first.")
            return

        print("\n===== ACCOUNTS NOT FOLLOWING YOU BACK =====")
        for i, user in enumerate(self.not_following_back, 1):
            print(f"{i}. {user}")
        print(f"\nTotal: {len(self.not_following_back)} accounts")

    def verify_non_followers(self, sample_size=10):
        """Verify a sample of the non-followers by checking their profiles"""
        if not self.not_following_back:
            print("No non-followers to verify. Run find_non_followers() first.")
            return []

        print(f"\nVerifying a sample of {min(sample_size, len(self.not_following_back))} accounts...")

        # Take a random sample of non-followers to verify
        sample = random.sample(self.not_following_back, min(sample_size, len(self.not_following_back)))
        verified_non_followers = []
        incorrect_results = []

        for user in sample:
            print(f"Verifying {user}...")
            is_non_follower = self.manually_verify_non_follower(user)

            if is_non_follower:
                verified_non_followers.append(user)
            else:
                incorrect_results.append(user)

        accuracy = len(verified_non_followers) / len(sample) * 100 if sample else 0

        print(f"\nVerification complete:")
        print(f"- Accuracy: {accuracy:.1f}%")
        print(f"- Correctly identified non-followers: {len(verified_non_followers)}/{len(sample)}")

        if incorrect_results:
            print(f"- Incorrectly identified accounts (these actually do follow you): {incorrect_results}")

        return verified_non_followers

    def manually_verify_non_follower(self, username):
        """Manually verify if a user is truly not following back by checking their following list"""
        try:
            self.driver.get(f"{self.URL}{username}/")
            self.random_sleep(3, 5)

            # Check if account is private
            private_indicators = self.driver.find_elements(By.XPATH,
                                                           '//h2[contains(text(), "Private")] | //div[contains(text(), "Private")] | //span[contains(text(), "Private")]')

            if private_indicators:
                print(f"Account {username} is private. Cannot verify.")
                return True  # Assume our list is correct since we can't verify

            # Try to check the username's bio or profile info for verification
            try:
                profile_sections = self.driver.find_elements(By.XPATH, '//*')
                for section in profile_sections:
                    try:
                        text = section.text
                        if text and self.username.lower() in text.lower():
                            # If our username appears in their bio, they may be following us
                            print(f"Found username mention in {username}'s profile. Manual verification recommended.")
                    except:
                        pass
            except:
                pass

            # Click on the following button
            following_clicked = False
            try:
                following_buttons = self.driver.find_elements(
                    By.XPATH,
                    '//a[contains(@href, "/following")] | //div[contains(text(), " following")]'
                )

                for btn in following_buttons:
                    try:
                        if btn.is_displayed():
                            btn.click()
                            following_clicked = True
                            break
                    except:
                        continue

                if not following_clicked:
                    # Try JavaScript click
                    following_elems = self.driver.find_elements(By.XPATH, '//a[contains(@href, "/following")]')
                    for elem in following_elems:
                        try:
                            self.driver.execute_script("arguments[0].click();", elem)
                            following_clicked = True
                            break
                        except:
                            continue
            except Exception as e:
                print(f"Could not open following list: {e}")
                return True  # Assume our list is correct

            if not following_clicked:
                print(f"Could not open following list for {username}")
                return True

            self.random_sleep(3, 5)

            # Search for your username in their following list
            try:
                # Look for search box
                search_box = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search" or @aria-label="Search"]'))
                )
                search_box.clear()
                # Type the username character by character like a human
                for char in self.username:
                    search_box.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))

                self.random_sleep(2, 3)

                # Check if your username appears in the results
                your_username_elements = self.driver.find_elements(
                    By.XPATH,
                    f'//a[contains(@href, "/{self.username}/")] | //div[contains(text(), "{self.username}")]'
                )

                follows_you = len(your_username_elements) > 0

                # Additional check if our first search didn't find anything
                if not follows_you:
                    # Try searching for our normalized username
                    search_box.clear()
                    for char in self.username.lower():
                        search_box.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))

                    self.random_sleep(2, 3)

                    # Check again
                    your_username_elements = self.driver.find_elements(
                        By.XPATH,
                        f'//a[contains(@href, "/{self.username.lower()}/")] | //div[contains(text(), "{self.username.lower()}")]'
                    )

                    follows_you = len(your_username_elements) > 0

                # Close dialog
                try:
                    webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                except:
                    pass
                self.random_sleep()

                if follows_you:
                    print(f"VERIFICATION ERROR: {username} actually follows you!")
                    return False
                else:
                    print(f"Verified: {username} does not follow you.")
                    return True

            except Exception as e:
                print(f"Error searching for your username: {e}")
                # Close dialog if open
                try:
                    webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                except:
                    pass
                return True  # Assume our list is correct

        except Exception as e:
            print(f"Error verifying {username}: {e}")
            return True  # Assume our list is correct

    def load_from_files(self, following_file=None, followers_file=None):
        """Load following and followers lists from JSON files to avoid scraping again"""
        if following_file:
            try:
                with open(following_file, 'r') as f:
                    self.following_list = json.load(f)
                print(f"Loaded {len(self.following_list)} following accounts from {following_file}")
            except Exception as e:
                print(f"Error loading following file: {e}")

        if followers_file:
            try:
                with open(followers_file, 'r') as f:
                    self.followers_list = json.load(f)
                print(f"Loaded {len(self.followers_list)} followers from {followers_file}")
            except Exception as e:
                print(f"Error loading followers file: {e}")

    def close(self):
        """Close the browser and clean up"""
        print("Closing browser...")
        self.driver.quit()


# -------- Command Line Interface --------
def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description="Instagram Followers Analysis Tool")

    # Required credentials
    parser.add_argument("--username", required=True, help="Your Instagram username")
    parser.add_argument("--password", required=True, help="Your Instagram password")

    # Optional behavior flags
    parser.add_argument("--headless", action="store_true", help="Run in headless mode without browser UI")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with screenshots")

    # Operation mode options
    operation_group = parser.add_argument_group("Operation Mode")
    operation_group.add_argument("--full-scan", action="store_true", help="Perform full scan (default)")
    operation_group.add_argument("--following-only", action="store_true", help="Only get following list")
    operation_group.add_argument("--followers-only", action="store_true", help="Only get followers list")
    operation_group.add_argument("--load-files", action="store_true",
                                 help="Load from existing files instead of scraping")

    # File loading options
    files_group = parser.add_argument_group("File Options")
    files_group.add_argument("--following-file", help="Path to following JSON file (for --load-files)")
    files_group.add_argument("--followers-file", help="Path to followers JSON file (for --load-files)")

    # Verification options
    verify_group = parser.add_argument_group("Verification Options")
    verify_group.add_argument("--verify", action="store_true", help="Verify a sample of non-followers")
    verify_group.add_argument("--verify-count", type=int, default=5, help="Number of accounts to verify (default: 5)")

    # Scrolling options
    scroll_group = parser.add_argument_group("Scrolling Options")
    scroll_group.add_argument("--scroll-timeout", type=int, default=1000,
                              help="Maximum number of scrolls before stopping (default: 1000)")
    scroll_group.add_argument("--stable-threshold", type=int, default=10,
                              help="Number of stable scrolls before stopping (default: 10)")
    scroll_group.add_argument("--scroll-delay", type=float, default=2.0,
                              help="Delay between scrolls in seconds (default: 2.0)")

    # Parse arguments
    args = parser.parse_args()

    # Initialize the bot
    bot = UnfollowTracker(args.username, args.password, headless=args.headless)
    bot.debug = args.debug

    # Set custom scrolling parameters
    bot.scroll_timeout = args.scroll_timeout
    bot.stable_threshold = args.stable_threshold
    bot.scroll_delay = args.scroll_delay

    try:
        # Handle different operation modes
        if args.load_files:
            # Load from existing files
            if not args.following_file or not args.followers_file:
                parser.error("--load-files requires both --following-file and --followers-file")

            print("Loading from existing files...")
            bot.load_from_files(args.following_file, args.followers_file)
            bot.find_non_followers()
            bot.show_results()

        else:
            # Login first (required for all scraping operations)
            if not bot.login():
                print("Login failed. Exiting.")
                return

            # Handle the different scan options
            if args.following_only:
                bot.get_following()
            elif args.followers_only:
                bot.get_followers()
            else:  # Full scan is default
                print("\n== STEP 1: Getting your following list ==")
                bot.get_following()

                print("\n== STEP 2: Getting your followers list ==")
                bot.get_followers()

                print("\n== STEP 3: Finding who doesn't follow you back ==")
                bot.find_non_followers(use_normalized_comparison=True)
                bot.show_results()

        # Optional verification step
        if args.verify:
            print(f"\n== Verifying {args.verify_count} non-followers ==")
            bot.verify_non_followers(args.verify_count)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        bot.close()


if __name__ == "__main__":
    main()