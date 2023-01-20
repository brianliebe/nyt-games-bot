# Wordle Discord Bot 🤖

### A little Discord bot that tracks users' Wordle scores and maintains a leaderboard.

Track the daily, weekly, and all-time leaderboards for your server, plus get some additional stats on how well you've played. Just copy & paste your Wordle results into Discord chat and the bot will track it.

### 🟩 🟨 ⬜

## Commands
- `?ranks (today|week|all-time|<puzzle #>)`
  - Bot will reply with the ranked leaderboard based on the query time period/puzzle #. Defaults to week.
- `?missing (today|<puzzle #>)`
  - Bot will reply and @mention users that are missing the puzzle. Defaults to today.
- `?entries [<user>]`
  - Bot will reply with the recorded entries in the database for \<user\>. Defaults to requester.
- `?stats [<user1> <user2> ...]`
  - Bot will reply with data on the user's average scores, etc. Defaults to requester. (More data coming soon maybe...)
- `?add [<user>] <puzzle output>`
  - Bot will record the Wordle puzzle entry for a user. Defaults to requester.
  - NOTE: `?add` is NOT needed to record entries. Just paste the output from Wordle right into the the channel and the bot will record it. The bot will react to your message with a ✅ to let you know it has been counted.

## Example Usage

1. Adding a score normally (without `?add`):

![image](https://user-images.githubusercontent.com/25470007/213812178-79617256-3a1f-4968-b311-1f111181ac32.png)

2. Viewing the leaderboard with `?ranks`:

| Today's Puzzle | Last 7 Days | All-time |
| ---- | ---- | ---- |
| ![image](https://user-images.githubusercontent.com/25470007/213815598-ea7a74b5-bdb9-43e8-857f-4c8987cced71.png) | ![image](https://user-images.githubusercontent.com/25470007/213814958-9477c2b7-6fbf-4c0f-b931-a546fccb9333.png) | ![image](https://user-images.githubusercontent.com/25470007/213812667-71a8765f-9673-4cd3-8228-d73e8ddd1673.png)

3. Viewing missing players for today's puzzle with `?missing`:

![image](https://user-images.githubusercontent.com/25470007/213816585-5e6a8217-e4ab-4d79-aa5f-156967c843b5.png)

4. Viewing a user's past entries with `?entries`:

![image](https://user-images.githubusercontent.com/25470007/150624781-5ff68297-c62f-4d69-a228-50680d37fc96.png)

5. Viewing stats for one or more players with `?stats`:

| One player | Two or more players |
| ---- | ---- |
| ![image](https://user-images.githubusercontent.com/25470007/213816840-58b1dd57-5862-4a1b-a5d6-58eecfe1ba0f.png) | ![image](https://user-images.githubusercontent.com/25470007/213817547-7a066053-56f9-4149-9740-5abc3ffcf68f.png) |

## Notes

This project is not complete and you might need some tweaking to get this up-and-running on a new server. I am currently using a MySQL database to store the entries, but anything would work given enough effort. The database has two tables: `users` (columns `user_id` and `name`) and `entries` (columns `puzzle_id`, `user_id`, `score`, `green`, `yellow`, `other`).

To deploy this yourself, I highly suggest taking a look at [this](https://realpython.com/how-to-make-a-discord-bot-python/) guide.

## TODO

- Add permissioning so that only specific channels may be used
- ~Add permissioning so that only specific users may enter scores (and/or only some users may use `?add`)~ Done ✅
- ~Add a better database implementation~ Done ✅
