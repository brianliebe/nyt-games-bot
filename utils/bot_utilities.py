import re
from datetime import date, datetime, timedelta, timezone
from bokeh.io.export import get_screenshot_as_png
from bokeh.models import ColumnDataSource, DataTable, TableColumn
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

class BotUtilities():
    def __init__(self, client, bot) -> None:
        self.client = client
        self.bot = bot

    # QUERIES

    def get_nickname(self, user_id) -> str:
        guild = self.bot.get_guild(self.bot.guild_id)
        for member in guild.members:
            if member.id == user_id:
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

    def is_wordle_submission(self, title: str) -> str:
        return re.match(r'^Wordle \d{3} \d{1}/\d{1}$', title) or re.match(r'^Wordle \d{3} X/\d{1}$', title)

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

    def get_image_from_df(self, df):
        source = ColumnDataSource(df)

        df_columns = df.columns.values
        columns_for_table=[]
        for column in df_columns:
            columns_for_table.append(TableColumn(field=column, title=column))

        data_table = DataTable(source=source, columns=columns_for_table, index_position=None, autosize_mode='fit_viewport', reorderable=False)

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument("--window-size=1024,768")
        chrome_options.add_argument('--no-proxy-server')
        chrome_options.add_argument("--proxy-server='direct://'")
        chrome_options.add_argument("--proxy-bypass-list=*")

        service = webdriver.chrome.service.Service(ChromeDriverManager().install())
        generated = get_screenshot_as_png(data_table, driver=webdriver.Chrome(service=service, options=chrome_options))

        generated = self._trim_image(generated)
        return generated

    def _trim_image(self, image):
        if image is None: return None
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