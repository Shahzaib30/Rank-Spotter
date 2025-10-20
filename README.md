# Rank Spotter

A complete, production-ready SERP (Search Engine Results Page) tracking tool built with React and Flask. Track your domain's Google ranking position for any keyword in real-time.

## 🌟 Features

- **Real-time SERP Checking**: Get instant ranking data using SerpApi
- **Modern UI**: Beautiful, responsive interface with Tailwind CSS
- **Top 100 Results**: Searches through the first 100 Google results
- **Detailed Analytics**: View top 10 results with your domain highlighted
- **Production Ready**: Configured for deployment on Render + SiteGround
- **Secure**: Environment-based configuration, input validation
- **Toast Notifications**: Real-time user feedback
- **Comprehensive Logging**: Backend request/error tracking

## 🏗️ Tech Stack

### Backend
- **Flask** - Python web framework
- **SerpApi** - Real-time search results API
- **Flask-CORS** - Cross-origin resource sharing
- **python-dotenv** - Environment configuration
- **Gunicorn** - Production WSGI server

### Frontend
- **React 18** - UI framework
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client
- **React Hot Toast** - Notifications
- **React Scripts** - Build tooling

## 📁 Project Structure

```
serpbot/
├── server/                 # Flask Backend
│   ├── app.py             # Main Flask application
│   ├── serp_api.py        # SerpApi integration
│   ├── config.py          # Configuration management
│   ├── requirements.txt   # Python dependencies
│   ├── .env.example       # Environment template
│   └── README.md          # Backend documentation
│
├── client/                # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchForm.js      # Search input form
│   │   │   ├── ResultsTable.js    # Results display
│   │   │   └── Spinner.js         # Loading indicator
│   │   ├── App.js         # Main component
│   │   ├── index.js       # Entry point
│   │   └── index.css      # Global styles
│   ├── public/
│   ├── package.json       # Node dependencies
│   ├── tailwind.config.js # Tailwind configuration
│   └── README.md          # Frontend documentation
│
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **SerpApi Account** - Get free API key at [serpapi.com](https://serpapi.com/)

### Backend Setup

1. **Navigate to server directory**
   ```bash
   cd server
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your SerpApi key:
   ```env
   SERPAPI_KEY=your-actual-api-key-here
   FLASK_DEBUG=False
   CORS_ORIGINS=http://localhost:3000
   ```

5. **Run the server**
   ```bash
   python app.py
   ```
   
   Server will start at `http://localhost:5000`

### Frontend Setup

1. **Navigate to client directory**
   ```bash
   cd client
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env`:
   ```env
   REACT_APP_API_URL=http://localhost:5000
   ```

4. **Start development server**
   ```bash
   npm start
   ```
   
   App will open at `http://localhost:3000`

## 📖 Usage

1. **Enter a search keyword** (e.g., "python tutorials")
2. **Enter your target domain** (e.g., "python.org")
3. **Click "Check Ranking"**
4. **View results:**
   - Ranking position (#1-100 or not found)
   - Full URL, title, and snippet of your ranking
   - Top 10 search results
   - Your domain highlighted in the table

## 🔧 API Documentation

### POST /api/check-serp

**Request:**
```json
{
  "keyword": "python tutorials",
  "domain": "python.org"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "data": {
    "keyword": "python tutorials",
    "domain": "python.org",
    "position": 3,
    "found": true,
    "url": "https://www.python.org/about/gettingstarted/",
    "title": "Python For Beginners",
    "snippet": "Official Python tutorial...",
    "top_results": [...],
    "total_results": 100,
    "timestamp": "2025-10-14T12:00:00Z"
  }
}
```

**Error Response (400/500):**
```json
{
  "success": false,
  "error": "Error message here"
}
```

## 🌐 Deployment

### Backend - Deploy to Render

1. Create account at [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: serpbot-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
   - **Directory**: `server`
5. Add environment variables:
   - `SERPAPI_KEY`: Your SerpApi key
   - `FLASK_DEBUG`: False
   - `CORS_ORIGINS`: Your frontend URL
   - `SECRET_KEY`: Generate a secure random key
6. Deploy!

### Frontend - Deploy to SiteGround

1. **Build the app**
   ```bash
   cd client
   npm run build
   ```

2. **Configure production API URL**
   
   Before building, update `.env`:
   ```env
   REACT_APP_API_URL=https://your-backend.onrender.com
   ```

3. **Upload to hosting**
   - Upload contents of `build/` folder to your web hosting
   - Point your domain to the directory

### Alternative: Netlify/Vercel

1. Connect GitHub repository
2. Configure:
   - **Build command**: `npm run build`
   - **Publish directory**: `build`
   - **Base directory**: `client`
3. Add environment variable:
   - `REACT_APP_API_URL`: Your backend URL
4. Deploy!

## 🔒 Security Best Practices

- ✅ API keys stored in environment variables
- ✅ CORS configured for specific origins
- ✅ Input validation and sanitization
- ✅ Request timeouts to prevent hanging
- ✅ Error handling without exposing internals
- ✅ HTTPS required in production

## 🐛 Troubleshooting

### Backend Issues

**"SERPAPI_KEY is required" error:**
- Ensure `.env` file exists in `server/` directory
- Verify SERPAPI_KEY is set correctly

**CORS errors:**
- Update `CORS_ORIGINS` in `.env` to include your frontend URL
- Ensure no trailing slashes in URLs

### Frontend Issues

**"Cannot connect to server" error:**
- Verify backend is running
- Check `REACT_APP_API_URL` in `.env`
- Ensure backend CORS allows your frontend origin

**Tailwind styles not loading:**
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

## 📊 Sample Response

Here's what a successful SERP check looks like:

```json
{
  "success": true,
  "data": {
    "keyword": "react hooks tutorial",
    "domain": "reactjs.org",
    "position": 2,
    "found": true,
    "url": "https://reactjs.org/docs/hooks-intro.html",
    "title": "Introducing Hooks – React",
    "snippet": "Hooks are a new addition in React 16.8...",
    "displayed_link": "reactjs.org › docs › hooks-intro",
    "top_results": [
      {
        "position": 1,
        "title": "React Hooks - W3Schools",
        "link": "https://www.w3schools.com/react/react_hooks.asp",
        "snippet": "Hooks allow function components to have access to state..."
      },
      {
        "position": 2,
        "title": "Introducing Hooks – React",
        "link": "https://reactjs.org/docs/hooks-intro.html",
        "snippet": "Hooks are a new addition in React 16.8..."
      }
    ],
    "total_results": 100,
    "timestamp": "2025-10-14T15:30:45Z"
  }
}
```

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🙏 Acknowledgments

- [SerpApi](https://serpapi.com/) for search results API
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Flask](https://flask.palletsprojects.com/) for backend framework
- [React](https://reactjs.org/) for frontend framework

## 📧 Support

For issues or questions:
- Create an issue on GitHub
- Check the README files in `server/` and `client/` directories
- Review SerpApi documentation

---

**Built with ❤️ for SEO professionals and developers**
