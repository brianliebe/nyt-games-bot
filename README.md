# Wordle Discord Bot 🤖
### Simple Discord Bot that tracks users' Wordle scores and maintains a leaderboard!
### 🟩 🟨 ⬜

## Commands
- `?ranks (today|week|all-time|<puzzle #>)`
  - Bot will reply with the ranked leaderboard based on the query time period/puzzle #. Defaults to week.
- `?missing (today|<puzzle #>)`
  - Bot will reply and @mention users that are missing the puzzle. Defaults to today.
- `?entries [<user>]`
  - Bot will reply with the recorded entries in the database for <user>. Defaults to requester.
- `?stats [<user1> <user2> ...]`
  - Bot will reply with data on the user's average scores, etc. Defaults to requester. (More data coming soon maybe...)
- `?add [<user>] <puzzle output>`
  - Bot will record the Wordle puzzle entry for a user. Defaults to requester.
  - NOTE: `?add` is NOT needed to record entries. Just paste the output from Wordle right into the the channel and the bot will record it. The bot will react to your message with a ✅ to let you know it has been counted.

## Example Usage

1. Adding a score without `?add`:

![image](https://user-images.githubusercontent.com/25470007/150624652-18f34aea-aab8-4187-bf19-6a41f3c2ec85.png)

2. Viewing the leaderboard with `?ranks`:

![image](https://user-images.githubusercontent.com/25470007/150624623-4b9e7043-88b7-446b-bd0e-02bc999d6006.png)

3. Viewing today's leaderboard with `?today`:

![image](https://user-images.githubusercontent.com/25470007/150624781-5ff68297-c62f-4d69-a228-50680d37fc96.png)

## Notes

This project is not complete and you might need some tweaking to get this up-and-running on a new server. I am currently using a MySQL database to store the entries, but anything would work given enough effort. The database has two tables: `users` (columns `user_id` and `name`) and `entries` (columns `puzzle_id`, `user_id`, `score`, `green`, `yellow`, `other`).

To deploy this yourself, I highly suggest taking a look at [this](https://realpython.com/how-to-make-a-discord-bot-python/) guide.

## TODO

- Add permissioning so that only specific channels may be used
- ~Add permissioning so that only specific users may enter scores (and/or only some users may use `?add`)~ Done ✅
- ~Add a better database implementation~ Done ✅
