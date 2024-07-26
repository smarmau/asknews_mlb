import os
import json
from dotenv import load_dotenv
from asknews_sdk import AsyncAskNewsSDK
import aiohttp
import aiofiles
from datetime import datetime, timedelta, date
import asyncio
from asyncio import Semaphore
import time
import requests
import re
import random
import sqlite3
import fcntl
import pytz
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import signal
import sys
from colorama import Fore, Back, Style, init

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

init(autoreset=True)
load_dotenv()
client_id_token = os.getenv('CLIENT_ID')
client_secret_token = os.getenv('CLIENT_SECRET')
odds_api_token = os.getenv('ODDS_API_KEY')

if not all([client_id_token, client_secret_token, odds_api_token]):
    raise ValueError("Missing one or more environment variables: CLIENT_ID, CLIENT_SECRET, ODDS_API_KEY")

sdk = AsyncAskNewsSDK(
    client_id=client_id_token,
    client_secret=client_secret_token,
    scopes=["chat", "news", "stories"]
)

class ScrapeSportsbookreview:
    def __init__(self, sport='MLB', date="", current_line=True):
        self.games = self.scrape_games(sport, date, current_line)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    def scrape_games(self, sport="MLB", date="", current_line=True):
        if date == "":
            date = datetime.today().strftime("%Y-%m-%d")
        _line = 'currentLine' if current_line else 'openingLine'

        sport_dict = {"NBA": "nba-basketball", "NFL": "nfl-football", "NHL": "nhl-hockey", "MLB": "mlb-baseball", "NCAAB": "ncaa-basketball"}

        spread_url = f"https://www.sportsbookreview.com/betting-odds/{sport_dict[sport]}/?date={date}"
        try:
            start_time = time.time()
            r = requests.get(spread_url)
            r.raise_for_status()
            elapsed_time = time.time() - start_time
            logger.info(f"API call to {spread_url} took {elapsed_time:.2f} seconds")
            
            j = re.findall('__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
            
            if not j:
                logger.warning(f"No data found for {sport} on {date}")
                return []

            build_id = json.loads(j[0])['buildId']
            spreads_url = f"https://www.sportsbookreview.com/_next/data/{build_id}/betting-odds/{sport_dict[sport]}.json?league={sport_dict[sport]}&date={date}"
            
            start_time = time.time()
            spreads_response = requests.get(spreads_url)
            spreads_response.raise_for_status()
            elapsed_time = time.time() - start_time
            logger.info(f"API call to {spreads_url} took {elapsed_time:.2f} seconds")
            
            spreads_json = spreads_response.json()
            spreads_list = spreads_json['pageProps']['oddsTables'][0]['oddsTableModel']['gameRows']
            spreads = {g['gameView']['gameId']: g for g in spreads_list}

            moneyline_url = f"https://www.sportsbookreview.com/_next/data/{build_id}/betting-odds/{sport_dict[sport]}/money-line/full-game.json?league={sport_dict[sport]}&oddsType=money-line&oddsScope=full-game&date={date}"
            
            start_time = time.time()
            moneyline_response = requests.get(moneyline_url)
            moneyline_response.raise_for_status()
            elapsed_time = time.time() - start_time
            logger.info(f"API call to {moneyline_url} took {elapsed_time:.2f} seconds")
            
            moneyline_json = moneyline_response.json()
            moneylines_list = moneyline_json['pageProps']['oddsTables'][0]['oddsTableModel']['gameRows']
            moneylines = {g['gameView']['gameId']: g for g in moneylines_list}

            all_stats = {
                game_id: {'spreads': spreads[game_id], 'moneylines': moneylines[game_id]} for game_id in spreads.keys()
            }

            games = []
            for event in all_stats.values():
                game = {}
                game['date'] = event['spreads']['gameView']['startDate']
                game['home_team'] = event['spreads']['gameView']['homeTeam']['fullName']
                game['away_team'] = event['spreads']['gameView']['awayTeam']['fullName']
                game['id'] = f"{game['date']}_{game['away_team']}_{game['home_team']}"
                game['home_ml'] = {}
                game['away_ml'] = {}
                if 'moneylines' in event and 'oddsViews' in event['moneylines'] and event['moneylines']['oddsViews']:
                    for line in event['moneylines']['oddsViews']:
                        if not line:
                            continue
                        game['home_ml'][line['sportsbook']] = line[_line]['homeOdds']
                        game['away_ml'][line['sportsbook']] = line[_line]['awayOdds']
                games.append(game)
            return games
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping data for {sport} on {date}: {e}")
            raise

class OddsCache:
    def __init__(self):
        self.odds = {}
        self.last_full_scrape = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def daily_scrape(self):
        logger.info("Starting daily odds scrape")
        start_time = time.time()
        games = await fetch_today_games()
        elapsed_time = time.time() - start_time
        logger.info(f"Fetching today's games took {elapsed_time:.2f} seconds")
        
        date = datetime.now(pytz.timezone('America/New_York')).strftime("%Y-%m-%d")
        scraper = ScrapeSportsbookreview(sport="MLB", date=date)
        self.odds = {game['id']: self.format_odds(game) for game in scraper.games}
        self.last_full_scrape = datetime.now(pytz.timezone('America/New_York'))
        logger.info("Completed daily odds scrape")

    def format_odds(self, game):
        return {
            'initial_odds': game,
            'latest_odds': game,
            'last_updated': datetime.now(pytz.timezone('America/New_York'))
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def update_game_odds(self, game_id, away_team, home_team):
        date = datetime.now(pytz.timezone('America/New_York')).strftime("%Y-%m-%d")
        scraper = ScrapeSportsbookreview(sport="MLB", date=date)
        for game in scraper.games:
            if game['home_team'] == home_team and game['away_team'] == away_team:
                self.odds[game_id] = self.format_odds(game)
                logger.info(f"Updated odds for game {game_id}")
                return
        logger.warning(f"Failed to update odds for game {game_id}. Game not found.")

    def get_odds(self, game_id):
        return self.odds.get(game_id, {}).get('latest_odds')

def get_current_et_time():
    return datetime.now(pytz.timezone('America/New_York'))

def ensure_directory(directory):
    os.makedirs(directory, exist_ok=True)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
async def fetch_today_games():
    current_time = get_current_et_time()
    today = current_time.strftime('%Y-%m-%d')
    
    url = f"http://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&startDate={today}&endDate={today}"
    
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            schedule_data = await response.json()
    elapsed_time = time.time() - start_time
    logger.info(f"API call to fetch today's games took {elapsed_time:.2f} seconds")
    
    games = []
    for date in schedule_data['dates']:
        for game in date['games']:
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            game_time = datetime.strptime(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
            game_time_et = game_time.astimezone(pytz.timezone('America/New_York'))
            games.append({
                'id': game['gamePk'],
                'away_team': away_team,
                'home_team': home_team,
                'game_time': game_time_et,
                'game_data': game
            })
    return games

def construct_query(game_description, odds_info_str, is_forecast):
    if is_forecast:
        return f"Can you predict the winner for the upcoming game of {game_description}?"
    else:
        return (f"Analyze the upcoming MLB game: {game_description}. As a sports betting expert, provide a methodical analysis considering:\n"
                f"1. Recent team performance (last 10-15 games)\n"
                f"2. Starting pitchers' stats (ERA, WHIP, recent form)\n"
                f"3. Key players' current form and historical performance\n"
                f"4. Team and individual player stats (OPS, ERA, etc.)\n"
                f"5. Head-to-head record, especially at the current venue\n"
                f"6. Injuries, suspensions, or significant roster changes\n"
                f"7. Home/away performance this season\n"
                f"8. Bullpen strength and recent usage\n"
                f"9. Weather conditions and their potential impact\n"
                f"10. Any relevant trends or streaks\n\n"
                f"Additional factors:\n"
                f"11. Performance in day vs. night games (if applicable)\n"
                f"12. Recent travel and scheduling factors\n"
                f"13. Performance against left/right-handed pitchers\n"
                f"14. Umpire assignments and tendencies\n"
                f"15. Stolen base success rates vs. catcher throw-out percentages\n"
                f"16. Performance in high-leverage situations\n"
                f"17. Motivational factors (playoff race, rivalries, etc.)\n\n"
                f"Current odds:\n{odds_info_str}\n\n"
                f"Based on this analysis:\n"
                f"1. Provide an absolute recommendation at the beginning, using the phrase 'My prediction is:'\n"
                f"2. State your confidence level (low, medium, high).\n"
                f"3. Suggest the most promising betting options (money line, run line, over/under).\n"
                f"4. Explain your rationale, highlighting key factors influencing your recommendation.\n"
                f"5. Identify any potential upset scenarios or undervalued bets.\n\n"
                f"Keep the total response under 1990 characters.")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
async def process_game(game_data, odds_cache, base_directory, model, is_forecast=False):
    game_description = f"{game_data['teams']['away']['team']['name']} vs {game_data['teams']['home']['team']['name']}"
    logger.info(f"Processing game: {game_description}")

    odds_data = odds_cache.get_odds(game_data['gamePk'])
    if odds_data is None:
        logger.warning(f"No odds data available for {game_description}. Proceeding with limited information.")
        odds_info_str = "Odds data unavailable"
    else:
        home_odds = odds_data['home_ml']
        away_odds = odds_data['away_ml']
        bookmakers = list(home_odds.keys())[:3]  # Use up to 3 bookmakers
        odds_info_str = (f"Current odds from {', '.join(bookmakers)}:\n"
                         f"{game_data['teams']['home']['team']['name']}: {', '.join([str(home_odds[b]) for b in bookmakers])}\n"
                         f"{game_data['teams']['away']['team']['name']}: {', '.join([str(away_odds[b]) for b in bookmakers])}\n")

    logger.info(f"Odds info for {game_description}: {odds_info_str}")

    query = construct_query(game_description, odds_info_str, is_forecast)
    logger.info(f"Constructed query for {game_description}: {query[:100]}...")  # Log first 100 chars of query

    try:
        start_time = time.time()
        if is_forecast:
            result = await asyncio.wait_for(
                sdk.chat.get_forecast(
                    query=query,
                    model=model,
                    web_search=True,
                    additional_context=construct_query(game_description, odds_info_str, False),
                    articles_to_use=12,
                    lookback=1
                ),
                timeout=180  # 180 second timeout
            )
            elapsed_time = time.time() - start_time
            logger.info(f"API call for forecast of {game_description} took {elapsed_time:.2f} seconds")
            logger.info(f"Successfully got forecast for {game_description}")
            logger.info(f"Forecast result: {result.forecast[:100]}...")  # Log first 100 chars of forecast
        else:
            response = await asyncio.wait_for(
                sdk.chat.get_chat_completions(
                    model=model,
                    messages=[{"role": "user", "content": query}],
                    stream=False,
                    inline_citations="none",
                    append_references=False,
                    journalist_mode=False,
                    asknews_watermark=False,
                    conversational_awareness=False
                ),
                timeout=180  # 180 second timeout
            )
            elapsed_time = time.time() - start_time
            logger.info(f"API call for chat completion of {game_description} took {elapsed_time:.2f} seconds")
            logger.info(f"Successfully got chat completion for {game_description}")
            result = response.choices[0].message.content if response and response.choices else None
            logger.info(f"Chat completion result: {result[:100] if result else 'None'}...")  # Log first 100 chars of result

        if result:
            data = {
                'game': game_description,
                'game_datetime': datetime.strptime(game_data['gameDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('America/New_York')).isoformat(),
                'query': query,
                'response': result.forecast if is_forecast else result,
                'home_team': game_data['teams']['home']['team']['name'],
                'away_team': game_data['teams']['away']['team']['name'],
                'odds_info': odds_info_str,
            }
            if is_forecast:
                data.update({
                    'reasoning': result.reasoning,
                    'probability': result.probability,
                    'likelihood': result.likelihood
                })
            await append_game_result(data, base_directory, f"{model}_forecast" if is_forecast else model)
            logger.info(f"Successfully wrote game result for {game_description}")
            return data
        else:
            logger.warning(f"Received an empty response from the API for game: {game_description}")
    except asyncio.TimeoutError:
        logger.error(f"Timeout occurred while processing {game_description}")
        raise
    except Exception as e:
        logger.error(f"Error processing {game_description}: {str(e)}")
        raise
    
    return None

async def append_game_result(data, base_directory, model):
    current_date = get_current_et_time().strftime('%Y-%m-%d')
    directory = os.path.join(base_directory, 'predictions', current_date)
    ensure_directory(directory)
    
    filename = f"{model.replace('/', '_')}_predictions.json"
    filepath = os.path.join(directory, filename)
    
    data['timestamp'] = get_current_et_time().isoformat()
    try:
        async with aiofiles.open(filepath, mode='a+') as f:
            await f.seek(0)
            content = await f.read()
            predictions = json.loads(content) if content else []
            predictions.append(data)
            await f.seek(0)
            await f.truncate()
            await f.write(json.dumps(predictions, indent=2, cls=DateTimeEncoder))
        logger.info(f"Successfully appended game result to {filepath}")
    except IOError as e:
        logger.error(f"Error appending game result to file: {str(e)}")
        raise

class MLBBot:
    def __init__(self):
        self.base_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mlb_data')
        ensure_directory(self.base_directory)
        self.odds_cache = OddsCache()
        self.running = True
        self.today_games = []
        self.api_semaphore = Semaphore(5)  # Limit to 5 concurrent API calls
    
    async def setup(self):
        loop = asyncio.get_running_loop()
        for s in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(self.shutdown(s))
            )
        try:
            await asyncio.wait_for(self.odds_cache.daily_scrape(), timeout=300)  # 5 minute timeout
        except asyncio.TimeoutError:
            logger.error("Daily odds scrape timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Error during daily odds scrape: {str(e)}")

    async def shutdown(self, sig):
        self.running = False
        logger.info(f"Received exit signal {sig.name}...")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        [task.cancel() for task in tasks]
        logger.info(f"Cancelling {len(tasks)} outstanding tasks")
        await asyncio.gather(*tasks, return_exceptions=True)
        loop = asyncio.get_running_loop()
        loop.stop()

    async def run(self):
        await self.setup()
        while self.running:
            try:
                await self.fetch_today_games()
                await self.process_upcoming_games()
                await self.heartbeat()
                await asyncio.sleep(900)  # Sleep for 15 minutes
            except asyncio.CancelledError:
                logger.info("Main loop cancelled")
                break
            except Exception as e:
                logger.error(f"An error occurred in the main loop: {str(e)}")
                await asyncio.sleep(60)  # Sleep for 1 minute before retrying
        
        logger.info("Graceful shutdown complete.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def fetch_today_games(self):
        try:
            self.today_games = await asyncio.wait_for(fetch_today_games(), timeout=180)
            logger.info(f"Successfully fetched {len(self.today_games)} games for today")
        except asyncio.TimeoutError:
            logger.error("Fetching today's games timed out")
            raise
        except Exception as e:
            logger.error(f"Error fetching today's games: {str(e)}")
            raise

    async def process_upcoming_games(self):
        current_time = get_current_et_time()
        tasks = []
        
        for game in self.today_games:
            if not self.running:
                break

            time_until_game = (game['game_time'] - current_time).total_seconds()

            if 0 <= time_until_game <= 3600:  # Within 60 minutes of game start
                tasks.append(self.process_single_game(game))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error processing game: {str(result)}")

    async def process_single_game(self, game):
        game_description = f"{game['away_team']} vs {game['home_team']}"
        logger.info(f"{Fore.CYAN}Processing game: {game_description}{Style.RESET_ALL}")
        try:
            await self.odds_cache.update_game_odds(game['id'], game['away_team'], game['home_team'])
            
            model_tasks = []
            for model in ["gpt-4o", "meta-llama/Meta-Llama-3-70B-Instruct", "claude-3-5-sonnet-20240620"]:
                model_tasks.append(self.process_game(game['game_data'], model))
            
            # Process forecasts
            for model in ["claude-3-5-sonnet-20240620", "gpt-4o"]:
                model_tasks.append(self.process_game(game['game_data'], model, is_forecast=True))
            
            results = await asyncio.gather(*model_tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"{Fore.RED}Error processing model for game {game_description}: {str(result)}{Style.RESET_ALL}")
            
            logger.info(f"{Fore.GREEN}Finished processing game: {game_description}{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"{Fore.RED}Failed to process game {game_description}: {str(e)}{Style.RESET_ALL}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def process_game(self, game_data, model, is_forecast=False):
        game_description = f"{game_data['teams']['away']['team']['name']} vs {game_data['teams']['home']['team']['name']}"
        logger.info(f"{Fore.YELLOW}Processing game: {game_description} with model: {model}{Style.RESET_ALL}")

        try:
            async with self.api_semaphore:
                start_time = time.time()
                result = await asyncio.wait_for(
                    process_game(game_data, self.odds_cache, self.base_directory, model, is_forecast),
                    timeout=180  # 180 second timeout
                )
                elapsed_time = time.time() - start_time
                logger.info(f"{Fore.GREEN}API call for {game_description} with model {model} took {elapsed_time:.2f} seconds{Style.RESET_ALL}")
            logger.info(f"{Fore.GREEN}Finished processing game: {game_description} with model: {model}{Style.RESET_ALL}")
            return result
        except asyncio.TimeoutError:
            logger.error(f"{Fore.RED}Timeout processing game {game_description} with model {model}{Style.RESET_ALL}")
            raise
        except Exception as e:
            logger.error(f"{Fore.RED}Error processing game {game_description} with model {model}: {str(e)}{Style.RESET_ALL}")
            raise

    async def heartbeat(self):
        current_time = get_current_et_time()
        current_date = current_time.strftime("%Y-%m-%d")
        current_time_str = current_time.strftime("%H:%M:%S")
        
        games_str = ""
        for game in self.today_games:
            time_until_game = game['game_time'] - current_time
            game_time_str = game['game_time'].strftime("%H:%M ET")
            
            if time_until_game > timedelta(minutes=60):
                color = Fore.CYAN  # Game more than 60 minutes away
                status = f"{game_time_str} - {self.format_timedelta(time_until_game)} away"
            elif time_until_game > timedelta(0):
                color = Fore.YELLOW  # Game less than 60 minutes away
                status = f"{game_time_str} - {self.format_timedelta(time_until_game)} away"
            elif time_until_game > timedelta(hours=-3):  # Assuming a game lasts about 3 hours
                color = Fore.GREEN  # Game in progress
                status = f"{game_time_str} - In Progress"
            else:
                color = Fore.MAGENTA  # Game completed
                status = f"{game_time_str} - Completed"
            
            games_str += f"{color}{game['away_team']} vs {game['home_team']} @ {status}{Style.RESET_ALL}\n  "
        
        games_str = games_str.strip() if games_str else "No games scheduled"
        
        heartbeat_message = (
            f"{Fore.WHITE}{Back.BLUE}Heartbeat: Bot is running.{Style.RESET_ALL}\n"
            f"{Fore.WHITE}Current Date: {current_date}{Style.RESET_ALL}\n"
            f"{Fore.WHITE}Current Time: {current_time_str}{Style.RESET_ALL}\n"
            f"{Fore.WHITE}Games scheduled for today:{Style.RESET_ALL}\n  {games_str}"
        )
        
        logger.info(heartbeat_message)

    def format_timedelta(self, td):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"

async def main():
    bot = MLBBot()
    try:
        await bot.run()
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())