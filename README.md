<h1 align="center">Aboulomania Bot</h1>
<p align="center">When you just can't decide</p>
<p align="center">Built using python and sqlite</p>

**Google says...**
> Aboulomania (from Greek a– 'without', and boulē 'will') is a mental
> disorder in which the patient displays pathological indecisiveness. It
> is typically associated with anxiety, stress, depression, and mental
> anguish, severely affecting one's ability to function socially.

This bot helps you decide what games to play by allow users in the
server to enter their picks into a draw and then it will automatically
select two winners from the picks provided. It also allows you to view the
historical stats to see who's the most lucky.

## Pre-Install Requirements

* python3 (latest)
* pip3

## How to download it

* Clone the repository: `git clone`
* Create your discord bot [here](https://discord.com/developers/applications)
* Retrieve your bot token
* Invite your bot on servers using the following invite:
  `https://discord.com/oauth2/authorize?&client_id={application_id}&scope=bot+applications.commands&permissions={permissions}`
  * Change `{application_id}` to the application ID and change `{permissions}` to the required permissions integer
    your bot needs. See [here](https://discord.com/developers/applications/{application_id}/bot)
* Add a config.json file and enter in all the configuration options:
```json
{
  "prefix": "{Prefix to use for command, default: !}",
  "token": "{Bot token from discord, required}",
  "permissions": "{App permissions from discord, required}",
  "application_id": "{App id from discord, required}",
  "owners": [
    {List of owner id's for extra priviledges, default: []}
  ],
  "timezone": "{Pytz timezone to use, default: Canada/Saskatchewan}",
  "auto_draw_weekday": {Integer week day to run autodraw every week, default: 2},
  "auto_draw_hour": {Integer hour to run the autodraw on the day, default: 19}
}
```

## Install & Run

Install:
```
python -m pip install -r requirements.txt
```
Run:
```
python main.py
```
