<p align="center">
    <img alt="rubika logo." src="./img/r1.png" style="width:200px;">
</p>


# RUBIKA GROUP MANAGER BOT
This bot is designed to manage groups on Rubika messenger platform with various capabilities and features.

The capabilities of the bot include:

1. Removing media files such as GIFs, images, videos, etc.
2. Deleting sent posts and stories.
3. Searching for music.
4. Complete group or chat locking.
5. Welcoming users.


<br>
</br>

## Installation

To install the bot, you need to clone the repository:
```bash
git clone https://github.com/Hossein-YB/rubika-bot-group-manager
```
Create a database in mysql

```sql
CREATE DATABASE irpytho1_rubika_v_2;
CREATE USER 'irpytho1_rubika_v2'@'%' IDENTIFIED WITH mysql_native_password BY "rubika@v2";
GRANT ALL ON irpytho1_rubika_v_2.* TO 'irpytho1_rubika_v2'@'%'; 
flush privileges;
```

Then install the required packages:
```bash
pip install -r requirements.txt
```
Now, run the bot using the following command:
```bash
python main.py
```
The bot will prompt for two account numbers, the first one for Rubika and the second one for Telegram. Enter them to activate the bot

<br>
</br>

# Usage

Once the bot is running, send the following command in the bot's private chat: ```!setsudo``` After sending this command, the bot will recognize you as the main administrator.
You can now add your bot to groups. If you want the bot to manage a group, make the bot an admin and use the command:
```!setgroup```Now the bot is an admin in the group and checks all group messages, applying necessary locks and management actions. For further commands and instructions, send the command ```!راهنما``` within the group chat.
