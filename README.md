<h1 align="center">Aboulomania Bot</h1>
<p align="center">When you just can't decide</p>
<p align="center">Built using python and sqlite</p>
<p align="center">
  <a href="https://discord.gg/mTBrXyWxAF"><img src="https://img.shields.io/discord/739934735387721768?logo=discord"></a>
  <a href="https://github.com/simifalaye/aboulomania-bot/commits/main"><img src="https://img.shields.io/github/last-commit/simifalaye/aboulomania-bot"></a>
  <a href="https://github.com/simifalaye/aboulomania-bot/blob/main/LICENSE"><img src="https://img.shields.io/github/license/simifalaye/aboulomania-bot"></a>
  <a href="https://github.com/simifalaye/aboulomania-bot"><img src="https://img.shields.io/github/languages/code-size/simifalaye/aboulomania-bot"></a>
</p>

**Google says...**
> Aboulomania (from Greek a– 'without', and boulē 'will') is a mental
> disorder in which the patient displays pathological indecisiveness. It
> is typically associated with anxiety, stress, depression, and mental
> anguish, severely affecting one's ability to function socially.

This bot helps multiple people decide between different options by
allowing users in the server to enter their picks into a draw and then
it will automatically select two winners from the picks provided each
week on a specified day and time. It also allows you to view the
historical stats to see who's the most lucky. Run `!help` to see
available commands.

**Basic Usage**:
All commands start with "!" (the default prefix)
* Run "*help*" to see the bot available commands
* An admin of the channel can add the bot to the server and then
  configure it by entering the commands into a text channel:
  * "*draw_listen*": Set current channel as the channel the bot will
    listen to for draw commands
  * "*draw_auto_enable*": Schedule when to run the auto-draw each week
* Each user can enter the next draw by running "*draw_enter* <pick1> <pick2>"
* The draw will be automatically run on the configured schedule (if it
  has been configured) or manually by running "*draw_now*"

**Draw Rules**:
* Each user gets two picks in the draw
* The first pick gets an additional entry in the draw
* Two winners are drawn from the entry list
* If someone gets one of their picks, all of their entries are removed from the next draw
* If a pick wins, that pick is removed from the next draw so it can't be selected again

## Pre-Install Requirements

* python3
* pip3

## Setup

* Clone the repository: `git clone <url>`
* Create your discord bot [here](https://discord.com/developers/applications)
  * See [here](https://www.freecodecamp.org/news/create-a-discord-bot-with-python/) for tutorial
* Retrieve your bot token and application ID from the applications UI
* Invite your bot to a server for testing using the following invite:
  `https://discord.com/oauth2/authorize?&client_id={application_id}&scope=bot+applications.commands&permissions={permissions}`
  * Change `{application_id}` to the application ID of your new application and change `{permissions}` to the required permissions integer (532576414784)
* Add a config.json file and enter in all the configuration options

### Configuration

Running the application requires a json configuration file what has the
following fields:
| Variable    | Type         | Description                                                 | Default               |
|-------------|--------------|-------------------------------------------------------------|-----------------------|
| prefix      | string       | The prefix to use when running commands                     | "!"                   |
| token       | string       | Your bot token from the discord UI                          | None, required        |
| permissions | string       | The permissions integer your bot needs when it gets invited | None, required        |
| owners      | list[string] | List of owner id's for extra privileges                     | []                    |
| timezone    | string       | The timezone to use for the bot (using python pytz strings) | "Canada/Saskatchewan" |

**Example**:
```json
{
  "prefix": "!",
  "token": "MY_BOT_TOKEN",
  "permissions": "532576414784",
  "application_id": "MY_APP_ID",
  "owners": [
    "MY_OWNER_ID"
  ],
  "timezone": "Canada/Saskatchewan"
}
```
**Note**:
- You can retrieve your discord user ID from discord by right-clicking
  on your name and selecting "Copy ID"

## Install & Run

Install:
```
python3 -m pip install -r requirements.txt
```
Run:
```
python3 main.py
```
