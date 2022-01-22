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

This is by no means complete and you might need some tweaking to get this up-and-running on a new server. I continuously am adding to it, so this README might becoming outdated! As of writing, all the commands are guild_only, so this is probably only feasible for my use-case. Would take some minor tweaking of the Cogs to get that changed.

The "database" this bot uses is literally just a .json file that I'm storing the results into, not a real database, so it goes without saying that this is not meant to be used heavily on some massive server.

To deploy this yourself, I highly suggest taking a look at [this](https://realpython.com/how-to-make-a-discord-bot-python/) guide.

## TODO

- Add permissioning so that only specific users may enter scores (and/or only some users may use `?add`)
- Add permissioning so that only specific channels may be used
- Add a better database implementation
