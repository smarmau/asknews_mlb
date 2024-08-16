
# MLB LLM/AI Betting Bot

Welcome to the MLB Betting Bot. This project leverages advanced machine forecast learning models to analyze Major League Baseball (MLB) games and make informed betting recommendations. The bot integrates forecasting from AskNews to provide top-tier insights into MLB matchups, using a state of the art forecating process. In addition it also utilized generalizable LLM models from GPT4o, Claude and LLAMA for comparison. 

## Features

- **State-of-the-Art Forecasting:** Powered by AskNews, the bot uses sophisticated AI models to forecast game outcomes, offering highly accurate predictions.
- **Daily Odds Scraping:** Automatically scrapes the latest odds for MLB games from Sportsbook Review, ensuring up-to-date information.
- **Comprehensive Game Analysis:** Analyzes upcoming MLB games with detailed statistics and expert insights.
- **Automated Workflow:** Continuously runs to fetch new game data, update predictions, and provide timely betting advice.
- **Customizable Models:** Supports integration with multiple AI models for diverse forecasting perspectives.

## Results

We ran this program as an experiment for a couple of weeks. Daily profit and losses for a $100 bet per game based on the bot's predictions is recorded here. 

|                   | 26-Jul     | 27-Jul     | 28-Jul     | 29-Jul     | 30-Jul     | 31-Jul     | 1-Aug      | 2-Aug      | 3-Aug      | 4-Aug      | 5-Aug      | 6-Aug      | 7-Aug      | 8-Aug      | 9-Aug      |            | Expectancy Total Profit |
|-------------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------------------|
| llama_chat_winrate| 0.53333333 | 0.4        | 0.73333333 | 0.54545455 | 0.46666667 | 0.6        | 0.8        | 0.6        | 0.46666667 | 0.66666667 | 0.88888889 | 0.6        | 0.6        | 0.66666667 | 0.61197961 |            |                        |
| gpt_chat_winrate  | 0.46666667 | 0.4        | 0.4        | 0.54545455 | 0.46666667 | 0.46666667 | 0.66666667 | 0.53333333 | 0.73333333 | 0.66666667 | 0.88888889 | 0.7        | 0.6        | 0.66666667 | 0.61435786 |            |                        |
| claude_chat_winrate | 0.53333333 | 0.46666667 | 0.46666667 | 0.63636364 | 0.53333333 | 0.53333333 | 0.6        | 0.46666667 | 0.6        | 0.77777778 | 0.6        | 0.7        | 0.6        | 0.57955183 |            |                        |
| gpt_forecast_winrate | 0.66666667 | 0.6        | 0.46666667 | 0.63636364 | 0.53333333 | 0.6        | 0.73333333 | 0.46666667 | 0.6        | 0.77777778 | 0.6        | 0.6        | 0.6        | 0.66666667 | 0.62672883 |            |                        |
| claude_forecast_winrate | 0.6        | 0.6        | 0.46666667 | 0.54545455 | 0.53333333 | 0.46666667 | 0.8        | 0.53333333 | 0.53333333 | 0.88888889 | 0.6        | 0.53333333 | 0.6        | 0.66666667 | 0.59292929 |            |                        |
|                   |            |            |            |            |            |            |            |            |            |            |            |            |            |            |            |            |                        |
| llama_chat_pnl    | -6.66      | -403.45    | 505.54     | -65        | -236.75    | 135.76     | 195.58     | 70.95      | -292.73    | 256.7      | 529.28     | 73.59      | 62.5       | 298.43     |            | 80.9671429 | 1123.74                |
| gpt_chat_pnl      | -311.95    | -508.16    | 55.63      | 65         | -294.23    | 195.58     | 270.95     | 148.66     | 251.45     | 529.28     | 73.59      | 272.5      | 298.43     |            | 46.8714286 | 656.62                  |
| claude_chat_pnl   | -131.64    | -403.45    | -333.04    | 129.33     | -159.35    | -120.7     | -332.08    | 27.26      | -3.54      | 314.28     | 73.59      | -147.49    | 298.43     |            | -42.344286 | -592.82                 |
| gpt_forecast_pnl  | 341.02     | 70.18      | -200.21    | 165.99     | -159.35    | 79.29      | 195.58     | 445.02     | -348.86    | 16.7       | 314.28     | 73.59      | 62.5       | 298.43     |            | 96.74      | 1354.36                |
| claude_forecast_pnl | 155.08    | 70.18      | -313.66    | -54        | -159.35    | -305.44    | 195.58     | -130.04    | -123.46    | -188.29    | 529.28     | -124.44    | 62.5       | 298.43     |            | -6.2592857 | -87.63                 |

## Prerequisites

- **Python 3.8+**
- **Environment Variables:**
  - `CLIENT_ID`: Your AskNews client ID.
  - `CLIENT_SECRET`: Your AskNews client secret.
  - `ODDS_API_KEY`: Your Odds API key.

## Setup

1. **Clone the repository:**

   ```
   git clone https://github.com/yourusername/mlb-betting-bot.git
   cd mlb-betting-bot
   ```

2. **Install dependencies:**

   ```
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   Create a `.env` file in the project root directory with the following content:

   ```
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   ODDS_API_KEY=your_odds_api_key
   ```

4. **Run the bot:**

   ```
   python mlb_bot.py
   ```

## How It Works

The MLB Betting Bot is designed to continuously analyze and predict MLB game outcomes. Here’s how it works:

1. **Data Collection:** The bot scrapes daily odds and game data from Sportsbook Review, ensuring it has the most current information available.
   
2. **AI-Powered Analysis:** Using the state-of-the-art forecasting model provided by AskNews, the bot processes this data to generate predictions. This model combines news (within the last 5 mins), historical game data, player statistics, and current odds to deliver highly accurate forecasts.
   
3. **Prediction and Insights:** The bot produces game predictions along with detailed analysis and insights, helping users make informed betting decisions.

## Powered by AskNews

This bot is built on the advanced forecasting technology of AskNews. By signing up for AskNews, users can unlock the full potential of this bot, gaining access to the latest AI innovations and comprehensive data analytics. [Sign up for AskNews here](https://asknews.app).

## Contributing

We welcome contributions to improve the MLB Betting Bot

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This bot is intended for informational purposes only. Always gamble responsibly and within your means.

