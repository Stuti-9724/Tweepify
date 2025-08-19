# Overview

Twitter Campaign Manager is an AI-powered social media automation platform that enables users to create, schedule, and analyze Twitter marketing campaigns. The system leverages artificial intelligence for content generation, automated tweet scheduling using background task processing, and comprehensive analytics tracking. Built with Flask as the core web framework, the application provides a complete solution for managing Twitter marketing efforts with intelligent automation and detailed performance insights.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
The application follows a service-oriented architecture pattern with Flask as the web framework. The core is structured around:

- **Flask Application**: Main web server handling HTTP requests and responses
- **SQLAlchemy ORM**: Database abstraction layer with declarative models for User, Campaign, ScheduledTweet, TweetTemplate, TweetAnalytics, and TrendingHashtag entities
- **Flask-Login**: User session management and authentication
- **Service Layer Pattern**: Dedicated service classes for AI content generation, Twitter API interactions, analytics processing, and campaign management
- **Background Task Processing**: Celery-based asynchronous task queue for tweet scheduling and analytics collection

## Frontend Architecture
Browser-based interface using:

- **Bootstrap 5**: UI framework with dark theme support
- **Font Awesome**: Icon library for consistent visual elements
- **Chart.js**: Data visualization for analytics dashboards
- **Vanilla JavaScript**: Client-side interactions and AJAX requests
- **Jinja2 Templates**: Server-side HTML template rendering

## Authentication & Authorization
User management implemented through Flask-Login with:

- **Username/password authentication**: Local account creation and login
- **OAuth 1.0a integration**: Twitter API authentication for posting capabilities
- **Session-based security**: Secure user session handling with configurable session secrets
- **Password hashing**: Werkzeug-based secure password storage

## Data Storage Strategy
Relational database design with:

- **User-centric data model**: All entities linked to user accounts for multi-tenant isolation
- **Campaign management**: Hierarchical structure with campaigns containing scheduled tweets and analytics
- **JSON field storage**: Flexible keyword and hashtag storage within relational structure
- **Cascading relationships**: Automatic cleanup of dependent records on deletion

## AI Integration Pattern
Content generation system using:

- **Google Gemini API**: AI-powered tweet content generation based on campaign parameters
- **Template-based prompting**: Structured prompts incorporating keywords, hashtags, and target audience data
- **Character limit validation**: Automatic enforcement of Twitter's 280-character constraint
- **Context-aware generation**: Integration with trending hashtags and campaign-specific requirements

## Background Processing Architecture
Asynchronous task handling through:

- **Celery task queue**: Distributed task processing for time-sensitive operations
- **Redis backend**: Message broker and result storage for task coordination
- **Task routing**: Specialized queues for different operation types (tweet posting, analytics, background maintenance)
- **Retry mechanisms**: Configurable retry logic with exponential backoff for failed operations
- **Error handling**: Comprehensive exception handling with status tracking

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework for Python
- **SQLAlchemy**: Object-relational mapping and database toolkit
- **Flask-Login**: User session management extension
- **Werkzeug**: WSGI utility library for password hashing and middleware

## AI and Content Generation
- **Google Gemini API**: AI-powered content generation service requiring API key authentication
- **Natural language processing**: Content optimization and character limit enforcement

## Social Media Integration
- **Twitter API v2**: Read operations for analytics and trending data collection
- **Twitter OAuth 1.0a**: Write operations for tweet posting and user authentication
- **Tweepy**: Python Twitter API wrapper for simplified integration

## Background Processing
- **Celery**: Distributed task queue system for asynchronous processing
- **Redis**: In-memory data store serving as message broker and result backend
- **Task scheduling**: Time-based tweet posting and periodic analytics collection

## Frontend Libraries
- **Bootstrap 5**: CSS framework with dark theme support
- **Font Awesome**: Icon library for user interface elements
- **Chart.js**: JavaScript charting library for analytics visualization

## Database System
- **PostgreSQL**: Primary relational database (configurable via DATABASE_URL environment variable)
- **Connection pooling**: SQLAlchemy engine optimization for concurrent connections
- **Migration support**: Built-in table creation and schema management
