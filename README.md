
# MLB LLM/AI Betting Bot

Welcome to the MLB Betting Bot. This project leverages advanced machine forecast learning models to analyze Major League Baseball (MLB) games and make informed betting recommendations. The bot integrates forecasting from AskNews to provide top-tier insights into MLB matchups, using a state of the art forecating process. In addition it also utilized generalizable LLM models from GPT4o, Claude and LLAMA for comparison. 

## Features

- **State-of-the-Art Forecasting:** Powered by AskNews, the bot uses sophisticated AI models to forecast game outcomes, offering highly accurate predictions.
- **Daily Odds Scraping:** Automatically scrapes the latest odds for MLB games from Sportsbook Review, ensuring up-to-date information.
- **Comprehensive Game Analysis:** Analyzes upcoming MLB games with detailed statistics and expert insights.
- **Automated Workflow:** Continuously runs to fetch new game data, update predictions, and provide timely betting advice.
- **Customizable Models:** Supports integration with multiple AI models for diverse forecasting perspectives.

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

This bot is built on the advanced forecasting technology of AskNews. By signing up for AskNews, users can unlock the full potential of this bot, gaining access to the latest AI innovations and comprehensive data analytics. [Sign up for AskNews here](https://asknews.app) to enhance your betting strategy with cutting-edge technology.

## Contributing

We welcome contributions to improve the MLB Betting Bot. If you'd like to contribute, please fork the repository, create a new branch, and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This bot is intended for informational purposes only. Always gamble responsibly and within your means.

---

Thank you for using the MLB Betting Bot! We hope it enhances your MLB betting experience with valuable insights and predictions.
