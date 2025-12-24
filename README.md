# NOS News Aggregator

A personalized news aggregator built with Streamlit that fetches news from NOS RSS feeds, categorizes articles using AI/LLM, and allows users to filter content based on their preferences.

## Features

- 📰 **RSS Feed Integration**: Automatically fetches news from NOS RSS feeds every 15 minutes
- 🤖 **AI Categorization**: Uses LLM (Groq, OpenAI, Hugging Face, or ChatLLM) to categorize articles
- 🎯 **Personalized Filtering**: Users can select categories and blacklist keywords
- 📊 **Statistics**: View included/excluded articles per day
- 🔄 **Background Processing**: Automatic article fetching and categorization
- 💾 **Supabase Integration**: Cloud database for articles and user preferences

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: Supabase (PostgreSQL)
- **AI/LLM**: Groq, OpenAI, Hugging Face, ChatLLM
- **RSS Parsing**: feedparser

## Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/nos-news-aggregator.git
   cd nos-news-aggregator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\Activate.ps1  # Windows PowerShell
   # or
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements_streamlit.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   SUPABASE_URL=your-supabase-url
   SUPABASE_ANON_KEY=your-supabase-anon-key
   GROQ_API_KEY=your-groq-api-key
   # Optional:
   OPENAI_API_KEY=your-openai-api-key
   HUGGINGFACE_API_KEY=your-huggingface-api-key
   CHATLLM_API_KEY=your-chatllm-api-key
   ```

5. **Set up Supabase database**
   - Run the SQL schema from `supabase_schema.sql` in your Supabase SQL editor
   - See `SUPABASE_SETUP_STEP_BY_STEP.md` for detailed instructions

6. **Run the app**
   ```bash
   streamlit run streamlit_app.py
   ```

## Deployment to Streamlit Cloud

See `DEPLOY_STREAMLIT_CLOUD.md` for detailed deployment instructions.

### Quick Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file: `streamlit_app.py`
   - Add secrets (API keys) in Settings → Secrets

3. **Set Streamlit Cloud Secrets**
   Add all your API keys in the format:
   ```toml
   SUPABASE_URL = "your-url"
   SUPABASE_ANON_KEY = "your-key"
   GROQ_API_KEY = "your-key"
   ```

## Project Structure

```
├── streamlit_app.py          # Main Streamlit application
├── supabase_client.py         # Supabase database client
├── articles_repository.py     # Article fetching and storage
├── categorization_engine.py  # AI/LLM categorization logic
├── nlp_utils.py              # ELI5 summary generation
├── background_scheduler.py   # Background RSS fetching
├── requirements_streamlit.txt # Python dependencies
├── supabase_schema.sql       # Database schema
└── .env                      # Environment variables (not committed)
```

## Configuration

### Required Environment Variables
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key

### Optional Environment Variables (for LLM)
- `GROQ_API_KEY`: For Groq LLM (recommended, free tier available)
- `OPENAI_API_KEY`: For OpenAI GPT models
- `HUGGINGFACE_API_KEY`: For Hugging Face models
- `CHATLLM_API_KEY`: For ChatLLM API

## Features in Detail

### Category Filtering
- Articles are shown only if ALL their categories are selected by the user
- Invalid categories (like "Overig") are automatically ignored
- Case-insensitive matching

### Background Scheduler
- Automatically fetches new articles every 15 minutes
- Runs independently of user interactions
- Processes and categorizes articles in the background

### User Preferences
- Select categories to include
- Blacklist keywords to exclude
- View statistics on included/excluded articles

## Troubleshooting

### No articles showing
- Check if categories are selected on the "Gebruiker" page
- Verify Supabase connection
- Check background scheduler is running (check logs)

### LLM not working
- Verify API keys are set correctly
- Check API key has sufficient credits/quota
- Try a different LLM provider

### Database errors
- Verify Supabase credentials
- Check database schema is applied
- Verify RLS policies allow access

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]
