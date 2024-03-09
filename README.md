# NYT Games Discord Bot 🤖

### A little Discord bot that tracks Wordle, Connections, and Strands scores and maintains a server leaderboard.

Track the daily, weekly, and all-time leaderboards for your server, plus get some additional stats on how well you've played. Just copy & paste your game results into Discord chat and the bot will track it.

### 🟩 🟨 ⬜ • 🟨 🟩 🟦 🟪 • 🔵 💡 🟡

## Commands
- `?ranks (today|week|all-time|<puzzle #>)`
  - View ranked leaderboard for today, this week, all-time, or for a specific puzzle. Defaults to this week.
- `?missing (today|<puzzle #>)`
  - View users that are missing today's puzzle or missing the specified puzzle. Defaults to today.
- `?entries [<user>]`
  - View recorded entries in the database for \<user\>. Defaults to requester.
- `?stats [<user1> <user2> ...]`
  - View game stats for one or more users. Defaults to requester.
- `?view [<user>] <puzzle #1> [<puzzle #2> ...]`
  - View entries for a user and one or more puzzles. Defaults to requester.

## Admin Commands
- `?add [<user>] <puzzle output>`
  - Manually add puzzle entry for a user. Defaults to requester.
- `?remove [<user>] <puzzle #>`
  - Manually remove puzzle entry for a user. Defaults to requester.

NOTE: `?add` is NOT needed to record entries. Just paste the output from the game right into the the channel and the bot will record it. The bot will react to your message with a ✅ to let you know it has been counted.

## Example Usage

1. Adding a score normally (without `?add`):

<img height="200" alt="image" src="https://github.com/brianliebe/nyt-games-bot/assets/25470007/8b747069-fce8-4e49-9622-cce648d66ff7">
<img height="200" alt="image" src="https://github.com/brianliebe/nyt-games-bot/assets/25470007/066219c6-75da-477e-8f97-439dc34196e7">
<img height="200" alt="image" src="https://github.com/brianliebe/nyt-games-bot/assets/25470007/76e31297-f7ef-4283-96de-4b599d7271f7">
<br/><br/>

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

To create your own bot and deploy this yourself, I highly suggest taking a look at [this](https://realpython.com/how-to-make-a-discord-bot-python/) guide.
