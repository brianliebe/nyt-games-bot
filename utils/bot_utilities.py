import discord, io, re
import matplotlib.pyplot as plt
from bokeh.io.export import get_screenshot_as_png
from bokeh.models import ColumnDataSource, DataTable, TableColumn
from enum import Enum, auto
from datetime import date, datetime, timedelta, timezone
from discord.ext import commands
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

class NYTGame(Enum):
    CONNECTIONS = auto()
    STRANDS = auto()
    WORDLE = auto()
    UNKNOWN = auto()

class BotUtilities():
    def __init__(self, client: discord.Client, bot: commands.Bot) -> None:
        self.client: discord.Client = client
        self.bot: commands.Bot = bot

    # GAME TYPE

    def get_game_from_channel(self, message: discord.Message) -> NYTGame:
        channel_name: str = message.channel.name.lower()
        if 'connections' in channel_name:
            return NYTGame.CONNECTIONS
        elif 'strands' in channel_name:
            return NYTGame.STRANDS
        elif 'wordle' in channel_name:
            return NYTGame.WORDLE
        else:
            return NYTGame.UNKNOWN

    # QUERIES

    def get_nickname(self, user_id: str) -> str:
        guild = self.bot.get_guild(self.bot.guild_id)
        for member in guild.members:
            if str(member.id) == str(user_id):
                return member.display_name
        return "?"

   # VALIDATION

    def is_user(self, word: str) -> bool:
        return re.match(r'^<@[!]?\d+>', word)

    def is_date(self, date_str: str) -> bool:
        return re.match(r'^\d{1,2}/\d{1,2}(/\d{2}(?:\d{2})?)?$', date_str)

    def is_sunday(self, query_date: date) -> bool:
        if query_date is not None and type(query_date) is date:
            return query_date.strftime('%A') == 'Sunday'
        else:
            return False

    def is_wordle_submission(self, line: str) -> str:
        return re.match(r'^Wordle (\d+|\d{1,3}(,\d{3})*)( 🎉)? (\d|X)\/\d$', line)

    def is_connections_submission(self, lines: str) -> str:
        return re.match(r'^Connections *(\n)Puzzle #\d+', lines)

    def is_strands_submission(self, lines: str) -> str:
        return re.match(r'Strands #\d+', lines)

    # DATES/TIMES

    def get_todays_date(self) -> date:
        return datetime.now(timezone(timedelta(hours=-5), 'EST')).date()

    def get_week_start(self, query_date: date):
        if query_date is not None and type(query_date) is date:
            return query_date - timedelta(days = (query_date.weekday() + 1) % 7)
        return None

    def get_date_from_str(self, date_str: str) -> date:
        if not self.is_date(date_str): return None

        if re.match(r'^\d{1,2}/\d{1,2}$', date_str):
            return datetime.strptime(date_str, f'%m/%d').replace(year=datetime.today().year).date()
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', date_str):
            return datetime.strptime(date_str, f'%m/%d/%y').date()
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
            return datetime.strptime(date_str, f'%m/%d/%Y').date()
        else:
            return None

    # CONVERT

    def convert_date_to_str(self, query_date: date) -> str:
        return query_date.strftime(f'%m/%d/%Y')

    # DATA FRAME TO IMAGE

    def get_image_from_df(self, df) -> Image.Image:
        source = ColumnDataSource(df)

        df_columns = df.columns.values
        columns_for_table=[]
        for column in df_columns:
            columns_for_table.append(TableColumn(field=column, title=column))

        data_table = DataTable(source=source, columns=columns_for_table, index_position=None, reorderable=False, autosize_mode="fit_columns")

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument('--headless')

        service = Service(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)

        generated: Image.Image = get_screenshot_as_png(data_table, driver=driver)
        return self._trim_image(generated)

    def _trim_image(self, image: Image.Image) -> Image.Image:
        if image is None:
            return None
        rgb_image = image.convert('RGB')
        width, height = image.size
        for y in reversed(range(height)):
            for x in range(0, max(15, width)):
                rgb = rgb_image.getpixel((x, y))
                if rgb != (255, 255, 255):
                    # account for differences in browsers
                    if x < 10 and rgb in [(254, 254, 254), (240, 240, 240)]:
                        return rgb_image.crop([5, 5, width, y])
                    else:
                        return rgb_image.crop([5, 5, width, y + 8])

        return rgb_image

    def fig_to_image(self, fig: plt.Figure) -> Image.Image:
        buf = io.BytesIO()
        fig.savefig(buf)
        buf.seek(0)
        img = Image.open(buf)
        return img

    def image_to_binary(self, img: Image.Image) -> io.BytesIO:
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        buf.seek(0)
        return buf

    def combine_images(self, img1: Image.Image, img2: Image.Image) -> Image.Image:
        widths, heights = zip(*(i.size for i in [img1, img2]))
        w = max(widths)
        h = sum(heights)
        combo = Image.new('RGBA', (w, h))
        combo.paste(img1, (0, 0))
        combo.paste(img2, (0, img1.size[1]))
        return combo

    def resize_image(self, image: Image.Image, width: int = None, height: int = None) -> Image.Image:
        w, h = image.size
        if width is None and height is None:
            return image
        if width is None:
            r = height / float(h)
            dim = (int(w * r), height)
        else:
            r = width / float(w)
            dim = (width, int(h * r))
        try:
            return image.resize(dim)
        except Exception as e:
            print('Caught exception: ' + str(e))
            return None

    def remove_emojis(self, data: str) -> str:
        emoj = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002500-\U00002BEF"  # chinese char
            u"\U00002702-\U000027B0"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001f926-\U0001f937"
            u"\U00010000-\U0010ffff"
            u"\u2640-\u2642"
            u"\u2600-\u2B55"
            u"\u200d"
            u"\u23cf"
            u"\u23e9"
            u"\u231a"
            u"\ufe0f"  # dingbats
            u"\u3030"
                        "]+", re.UNICODE)
        return re.sub(emoj, '', data)
