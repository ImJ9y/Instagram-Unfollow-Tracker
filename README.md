# Instagram-Unfollow-Tracker
A powerful tool to track who doesn't follow you back on Instagram.

Show Image

****Features****
- 🔍 **Complete Follower Analysis:** Extract your entire following and followers lists
- 🔄 **Accurate Comparison:** Identify accounts that don't follow you back with normalized username comparison
- ✅ **Verification System:** Double-check results to ensure accuracy
- 📊 **Detailed Statistics:** Get information about your Instagram relationships
- 📱 **Clean UI:** Easy-to-use command line interface with customizable parameters
- 🔐 **Privacy-Focused:** All data remains on your device - no external servers

****Installation****
**Prerequisites**
- Python 3.6 or newer
- Chrome browser
- ChromeDriver that matches your Chrome version

**Setup**
1. Clone the repository:
   - bash
     git clone https://github.com/ImJ9y/instagram-unfollow-tracker.git
     cd instagram-unfollow-tracker
2. Install required packages:
   - bash
     pip install -r requirements.txt
3. Download ChromeDriver:
   - Visit ChromeDriver website
   - Download the version that matches your Chrome browser
   - Place the executable in your PATH or in the project directory

**Usage**

**Basic Usage**
<pre lang="bash">
python instagram_bot_cli.py --username YOUR_INSTAGRAM_USERNAME --password YOUR_INSTAGRAM_PASSWORD
</pre>

**Advanced Options**
<pre lang="bash">
python instagram_bot_cli.py --username YOUR_USERNAME --password YOUR_PASSWORD --scroll-timeout 2000 --stable-threshold 15 --scroll-delay 1.5 --verify
</pre>


**Command-line Arguments**
| Argument            | Description                                      | Default |
|---------------------|--------------------------------------------------|---------|
| `--username`        | Your Instagram username                          | Required |
| `--password`        | Your Instagram password                          | Required |
| `--headless`        | Run in headless mode (no visible browser)        | False |
| `--debug`           | Enable debug mode with screenshots               | True |
| `--scroll-timeout`  | Maximum number of scrolls to attempt             | 1000 |
| `--stable-threshold`| Number of stable scrolls before stopping         | 10 |
| `--scroll-delay`    | Delay between scrolls (seconds)                  | 2.0 |
| `--verify`          | Verify a sample of non-followers                 | False |
| `--verify-count`    | Number of accounts to verify                     | 5 |


**Operation Modes**
| Mode            | Description                        | Command |
|------------------|------------------------------------|---------|
| Full Scan        | Complete analysis (default)        | `--full-scan` |
| Following Only   | Only extract following list        | `--following-only` |
| Followers Only   | Only extract followers list        | `--followers-only` |
| Load Files       | Use previously saved data          | `--load-files --following-file FILE1 --followers-file FILE2` |


****Output****

The tool creates an organized directory structure for results:
<pre lang="bash">
instagram_data/
├── screenshots/                             # Debug screenshots (if --debug is enabled)
└── json_files/
    ├── username_following_TIMESTAMP.json     # People you follow
    ├── username_followers_TIMESTAMP.json     # People who follow you
    └── username_non_followers_TIMESTAMP.json # People who don't follow you back
</pre>

**How It Works**
1. The bot logs into your Instagram account
2. It navigates to your profile and extracts your following and followers lists
3. It compares the lists to identify accounts that don't follow you back
4. Results are saved as JSON files in the output directory

****Advanced Features****

**Normalized Username Comparison**
The tool uses a sophisticated username normalization technique to ensure accurate matching. This catches cases where the same account might appear with slight variations in capitalization or formatting.


**Verification System**
The --verify option performs an additional check on a sample of identified non-followers by directly checking their following list, providing an accuracy percentage.


**Privacy & Security**
- Your credentials are only used locally to log in to Instagram
- No data is sent to any external servers
- All results are stored locally on your device
- The tool respects Instagram's terms of service and implements rate limiting


**Limitations**
- Instagram may temporarily limit your account if you run the tool too frequently
- Some accounts may be inaccessible if they are private or have blocked you
- The tool may require manual interaction for verification or CAPTCHA challenges


**Contributing**
Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the repository
2. Create your feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add some amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request


**License**
This project is licensed under the MIT License - see the [LICENSE](/LICENSE) file for details.


**Disclaimer**
This tool is for personal use only. Please respect Instagram's terms of service and use this tool responsibly. The developers are not responsible for any account limitations or bans resulting from the use of this tool.


**Contact**
Jay Im - jayim1996@outlook.com
Project Link: https://github.com/ImJ9y/Instagram-Unfollow-Tracker
