import os, re, json, io
import statistics as stats
import discord
from discord import file
import pandas as pd
from datetime import date

from pandas.core.reshape.melt import wide_to_long

from bokeh.io.export import get_screenshot_as_png
from bokeh.models import ColumnDataSource, DataTable, TableColumn
from selenium import webdriver
from PIL import Image, ImageChops
from pyvirtualdisplay import Display
from webdriver_manager.chrome import ChromeDriverManager

os.environ['WDM_LOG_LEVEL'] = '0'

# parse environment variables
token = os.getenv('DISCORD_TOKEN')
guild_id = os.getenv('GUILD_ID')

# build Discord clientwh
intents = discord.Intents.default()
intents.members = True
d = discord.Client(intents=intents)

# read the db if the program is starting
db = {}
if os.path.exists("database.json"):
    db = json.loads(open("database.json").read())

class PuzzleScore():
    def __init__(self, user_id, message: str = None, puzzle_num = None, score = None, green = None, yellow = None, other = None) -> None:
        self.user_id = user_id
        if message is not None:
            self.green, self.yellow, self.other = self.get_square_info(message)
            self.puzzle_num, self.score = self.get_puzzle_info(message)
        else:
            self.puzzle_num = puzzle_num
            self.score = score
            self.green = green
            self.yellow = yellow
            self.other = other
        
    def get_puzzle_info(self, message) -> list:
        puzzle_title = message.split("\n")[0]
        puzzle_num, score = None, None
        try:
            if 'X/6' in puzzle_title:
                puzzle_num, _ = re.findall(r'\d+', puzzle_title)
                score = 7
            else:
                puzzle_num, score, _ = re.findall(r'\d+', puzzle_title)
                score = int(score)
        except Exception:
            pass
        return puzzle_num, score

    def get_square_info(self, message) -> list[int]:
        green = message.count('🟩')
        yellow = message.count('🟨')
        other = message.count('⬜') + message.count('⬛')
        return green, yellow, other

    def is_valid(self) -> bool:
        return self.user_id is not None and \
            self.puzzle_num is not None and \
            self.score is not None

class User():
    def __init__(self, user_id, first_score: PuzzleScore = None) -> None:
        self.user_id = user_id
        self.scores = {}
        self.rank = None
        self.true_average, self.calc_average = None, None
        self.avg_green, self.avg_yellow, self.avg_other = None, None, None

        if first_score is not None:
            self.add(first_score)

    def add(self, ps: PuzzleScore) -> None:
        self.scores[ps.puzzle_num] = ps
        self.calculate_avgs()

    def calculate_avgs(self) -> None:
        scores, greens, yellows, others = [], [], [], []
        for puzzle_num in self.scores.keys():
            scores.append(self.scores[puzzle_num].score)
            greens.append(self.scores[puzzle_num].green)
            yellows.append(self.scores[puzzle_num].yellow)
            others.append(self.scores[puzzle_num].other)
        self.true_average = stats.mean(scores)
        self.avg_green = stats.mean(greens)
        self.avg_yellow = stats.mean(yellows)
        self.avg_other = stats.mean(others)

    def calculate_adj_avg(self, total_games) -> None:
        scores = []
        for puzzle_num in self.scores.keys():
            scores.append(self.scores[puzzle_num].score)
        for _ in range(total_games - len(self.scores)):
            scores.append(7)
        self.calc_average = stats.mean(scores)


def write_db() -> None:
    f = open("database.json", "w")
    f.write(json.dumps(db, indent=4, sort_keys=True))
    f.close()

def get_nickname(user_id) -> str:
    guild = d.get_guild(int(guild_id))
    for member in guild.members:
        if member.id == user_id:
            return member.display_name
    return "?"

def add_score(ps: PuzzleScore) -> None:
    entry = {'user_id' : ps.user_id, 'score' : ps.score, 'green' : ps.green, \
            'yellow' : ps.yellow, 'other' : ps.other}
    if ps.puzzle_num in db.keys():
        db[ps.puzzle_num].append(entry)
    else:
        db[ps.puzzle_num] = [entry]
    write_db()

def get_ranked_users(puzzle_num = None) -> list[User]:
    users = []
    for puzzle in sorted(db.keys()):
        if puzzle_num is not None and puzzle_num != puzzle:
            continue
        for entry in db[puzzle]:
            user_id = entry['user_id']
            score = entry['score']
            green = entry['green']
            yellow = entry['yellow']
            other = entry['other']
            ps = PuzzleScore(user_id, puzzle_num=puzzle, score=score, green=green, yellow=yellow, other=other)

            found_user = False
            for user in users:
                if user.user_id == user_id:
                    user.add(ps)
                    found_user = True
                    break
            if not found_user:
                new_user = User(user_id, first_score = ps)
                users.append(new_user)

    if puzzle_num is None:
        print(max([len(x.scores) for x in users]))
        for user in users:
            user.calculate_adj_avg(max([len(x.scores) for x in users]))
        users.sort(key = lambda u: (u.calc_average, u.avg_other, u.avg_yellow, u.avg_green))
    else:
        users.sort(key = lambda u: (u.true_average, u.avg_other, u.avg_yellow, u.avg_green))

    for i, user in enumerate(users):
        if i > 0:
            prev = users[i - 1]
            if puzzle_num is None:
                # ?ranks
                if prev.calc_average == user.calc_average and \
                        prev.avg_other == user.avg_other and \
                        prev.avg_yellow == user.avg_yellow and \
                        prev.avg_green == user.avg_green:
                    user.rank = prev.rank
                    continue
            else:
                # ?today
                if prev.true_average == user.true_average and \
                        prev.avg_other == user.avg_other and \
                        prev.avg_yellow == user.avg_yellow and \
                        prev.avg_green == user.avg_green:
                    user.rank = prev.rank
                    continue
        user.rank = i + 1
    return users

def trim(image):
    if image is None: return None
    rgb_image = image.convert('RGB')
    width, height = image.size
    for y in reversed(range(height)):
        for x in range(width):
            rgb = rgb_image.getpixel((x,y))
            if rgb != (255, 255, 255):
                if x < 10:
                    return rgb_image.crop([5, 5, width, y])
                else:
                    return rgb_image.crop([5, 5, width, y + 5])
    return None

def get_output_image(df, filename):
    source = ColumnDataSource(df)

    df_columns = df.columns.values
    columns_for_table=[]
    for column in df_columns:
        columns_for_table.append(TableColumn(field=column, title=column))

    data_table = DataTable(source=source, columns=columns_for_table, index_position=None, autosize_mode='fit_viewport')

    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument('--headless')
    chrome_options.add_argument("--window-size=1024,768")
    chrome_options.add_argument('--no-proxy-server')
    chrome_options.add_argument("--proxy-server='direct://'");
    chrome_options.add_argument("--proxy-bypass-list=*");

    service = webdriver.chrome.service.Service(ChromeDriverManager().install())
    generated = get_screenshot_as_png(data_table, driver=webdriver.Chrome(service=service, options=chrome_options))

    generated = trim(generated)
    return generated

# the only event handler we need, for incoming messages
@d.event
async def on_message(message):
    # return if the message is from the bot
    if message.author == d.user: return

    if message.content != "":
        # get the user id for this message
        user_id = message.author.id

        if '\n' in message.content:
            cmd = message.content[:message.content.index('\n')].strip()
            message_content = message.content[message.content.index('\n') + 1:].strip()
        else:
            cmd = message.content.strip()
            message_content = ""

        if cmd.startswith("?"):
            # ?ranks
            if cmd == "?ranks":
                df = pd.DataFrame(columns=['Rank', 'User', 'Average', '🟩', '🟨', '⬜', '🧩'])
                for user in get_ranked_users():
                    df.loc[user.rank] = [
                            user.rank, 
                            get_nickname(user.user_id),
                            "{:.2f}/6 ({:.2f}/6)".format(user.calc_average, user.true_average),
                            "{:.2f}".format(user.avg_green),
                            "{:.2f}".format(user.avg_yellow),
                            "{:.2f}".format(user.avg_other),
                            len(user.scores)
                        ]
                output_image = get_output_image(df, "leaderboard")
                if output_image is not None:
                    with io.BytesIO() as image_binary:
                        output_image.save(image_binary, 'PNG')
                        image_binary.seek(0)
                        await message.channel.send("Current Leaderboard 😘", \
                                file=discord.File(fp=image_binary, filename='image.png'))
            
            # ?today
            elif cmd == "?today":
                arbitrary_date = date(2022, 1, 10)
                arbitrary_date_puzzle = 205
                todays_date = date.today()
                todays_puzzle = str(arbitrary_date_puzzle + (todays_date - arbitrary_date).days)

                df = pd.DataFrame(columns=['Rank', 'User', 'Score', '🟩', '🟨', '⬜', '🧩'])
                for user in get_ranked_users(puzzle_num=todays_puzzle):
                    puzzle_data = user.scores[todays_puzzle]
                    df.loc[user.rank] = [
                            user.rank, 
                            get_nickname(user.user_id),
                            "{}/6".format(puzzle_data.score),
                            puzzle_data.green,
                            puzzle_data.yellow,
                            puzzle_data.other,
                            len(user.scores)
                        ]
                output_image = get_output_image(df, "todays_leaderboard")
                if output_image is not None:
                    with io.BytesIO() as image_binary:
                        output_image.save(image_binary, 'PNG')
                        image_binary.seek(0)
                        await message.channel.send("Today's Leaderboard (🧩 #{})".format(todays_puzzle), \
                                file=discord.File(fp=image_binary, filename='image.png'))

            # ?info
            elif cmd.startswith("?info"):
                query_user_id = int(cmd.split(' ')[1].strip("<>@!& ") if len(cmd.split(' ')) == 2 else user_id)
                output = "<@{}> has the following entries:".format(query_user_id)
                for user in get_ranked_users():
                    if user.user_id == query_user_id:
                        for puzzle_num in user.scores.keys():
                            ps = user.scores[puzzle_num]
                            output += "\n\t- 🧩 #{}: {}/6 (`🟩 {}` `🟨 {}` `⬜ {}`)" \
                                .format(puzzle_num, ps.score, ps.green, ps.yellow, ps.other)
                await message.channel.send(output)
            
            # ?add
            elif cmd.startswith("?add"):
                if len(cmd.split(' ')) == 2:
                    _, behalf_user_id = cmd.split(' ')
                    behalf_user_id = int(behalf_user_id.strip("<>@!& "))
                    ps = PuzzleScore(behalf_user_id, message_content)
                    if ps.is_valid():
                        add_score(ps)
                        await message.channel.send("<@{}>, a score of {}/6 has been recorded for user <@{}> on Puzzle #{}" \
                            .format(user_id, ps.score, ps.user_id, ps.puzzle_num))
                    else:
                        await message.channel.send("Sorry, could not understand request")
                else:
                    await message.channel.send("Please use format '?add <user>' followed by the puzzle output to add scores manually")
        else:
            # normal paste from website
            if re.match(r'^Wordle \d{3} \d{1}/\d{1}$', cmd) or re.match(r'^Wordle \d{3} X/\d{1}$', cmd):
                ps = PuzzleScore(user_id, message.content)
                if ps.is_valid():
                    add_score(ps)
                    await message.channel.send("<@{}>, a score of {}/6 has been recorded for Puzzle #{}" \
                        .format(ps.user_id, ps.score, ps.puzzle_num))
                else:
                    await message.channel.send("Sorry, could not understand request")

d.run(token)
