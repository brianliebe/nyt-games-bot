# Wordle Discord Bot 🤖
### Simple Discord Bot that tracks users' Wordle scores and maintains a leaderboard!
### 🟩 🟨 ⬜


## Commands
- `?ranks`
  - Bot will respond with the current leaderboards
- `?info <user>`
  - Bot will respond with a list of all the user's entries in the database (passing no user will default to the asking user)
- `?add <user> <puzzle output>`
  - Bot will add an entry to the database for the specified user. Please user shift+enter between the user and the puzzle output.
  
**NOTE:** Simply copy-pasting the Wordle results into the Discord server will alert the Bot, and it will automatically add the result into the database. The point of `?add` is just to allow users to add other users' scores if need be.

## Example Usage

Adding a score without `?add`:

<img width="629" alt="image" src="https://user-images.githubusercontent.com/25470007/148973925-d6d06a74-d33e-4bb4-a68c-cd511f6e056f.png">

Viewing the leaderboard with `?ranks`:

<img width="629" alt="image" src="https://user-images.githubusercontent.com/25470007/148973941-391ccba7-6ae2-45dc-af60-c5dea7a6ce91.png">

## Notes

This is by no means a complete project, just something I threw together for fun. Feel free to branch or really do whatever you want with it. There are some other implementations of this type of Discord Bot for Wordle on the internet already. Check those out too!

The "database" this bot uses is literally just a .json file that I'm storing the results into, not a real database, so it goes without saying that this is not meant to be used heavily on some massive server. There's a ton of ideas I have to add to this, but it might just not be necessary for my use-case. Again, feel free to add whatever.

To deploy this yourself, I highly suggest taking a look at [this](https://realpython.com/how-to-make-a-discord-bot-python/) guide.

## TODO

- Add permissioning so that only specific users may enter scores (and/or only some users may use `?add`)
- Add permissioning so that only specific channels may be used
- Add a better database implementation
- Add a class that can be used and stored while the program is running, instead of building the objects from the database each time it's queried. It is not at all efficient right now -- just simple.
