# MCP Call Analyzer - Documentation Index

Welcome to the comprehensive documentation for the MCP Call Analyzer system. This index provides quick access to all documentation resources.

## 📚 Documentation Structure

### 🚀 Getting Started
- **[Setup Guide](../SETUP_GUIDE.md)** - Complete installation and configuration instructions
- **[Quick Start](README.md#quick-start)** - Get up and running in 5 minutes
- **[Interactive Demo](examples/INTERACTIVE_DEMO.md)** - Hands-on walkthrough with examples

### 🏗️ Architecture & Design
- **[Architecture Overview](README.md#architecture)** - System design and components
- **[Architecture Diagrams](architecture/ARCHITECTURE_DIAGRAMS.md)** - Visual system representations
- **[Hybrid Flow Diagram](architecture/HYBRID_FLOW_DIAGRAM.md)** - API + Browser automation flow

### 💻 API & Development
- **[API Reference](api/API_REFERENCE.md)** - Complete API documentation
- **[Database Schema](database/schema.sql)** - PostgreSQL schema definitions
- **[Code Examples](examples/)** - Sample implementations

### 🛠️ Operations
- **[Repository Cleanup](../cleanup_repo.py)** - Organize and clean project files
- **[Troubleshooting](README.md#troubleshooting)** - Common issues and solutions
- **[Performance Optimization](api/API_REFERENCE.md#performance-optimization)** - Best practices

## 🔍 Quick Links by Role

### For Developers
1. [API Reference](api/API_REFERENCE.md)
2. [Database Schema](database/schema.sql)
3. [Architecture Diagrams](architecture/ARCHITECTURE_DIAGRAMS.md)
4. [Code Examples](examples/INTERACTIVE_DEMO.md)

### For System Administrators
1. [Setup Guide](../SETUP_GUIDE.md)
2. [Environment Configuration](../SETUP_GUIDE.md#step-4-configure-environment-variables)
3. [Database Setup](database/schema.sql)
4. [Troubleshooting](README.md#troubleshooting)

### For Business Users
1. [Overview](README.md#overview)
2. [Use Cases](README.md#use-cases)
3. [Interactive Demo](examples/INTERACTIVE_DEMO.md)
4. [Analytics Examples](examples/INTERACTIVE_DEMO.md#step-7-generate-insights-dashboard)

## 📊 Key Features Documentation

### Data Collection
- [API Scraper](api/API_REFERENCE.md#apiscraper) - Metadata collection
- [MCP Browser Scraper](api/API_REFERENCE.md#mcpbrowserscraper) - Audio downloads
- [Hybrid Pipeline](architecture/HYBRID_FLOW_DIAGRAM.md) - Combined approach

### Processing Pipeline
- [Transcription](api/API_REFERENCE.md#transcribe_audio) - Deepgram integration
- [Analysis](api/API_REFERENCE.md#analyze_call) - GPT-4 insights
- [Batch Processing](api/API_REFERENCE.md#batchprocessor) - High-volume handling

### Storage & Analytics
- [Database Models](api/API_REFERENCE.md#database-models) - Data structures
- [Analytics Views](database/schema.sql#views) - Pre-built queries
- [Reporting](examples/INTERACTIVE_DEMO.md#step-9-export-results) - Export capabilities

## 🔧 Configuration Files

### Essential Configuration
- **[.env.example](../.env.example)** - Environment variables template
- **[requirements.txt](../requirements.txt)** - Python dependencies
- **[config/settings.json](README.md#configuration-files)** - Application settings

## 📈 Metrics & Monitoring
- [Performance Metrics](api/API_REFERENCE.md#monitoring)
- [Error Handling](api/API_REFERENCE.md#error-handling)
- [Logging Configuration](api/API_REFERENCE.md#logging)

## 🚦 Status Codes & States

### Call Processing States
- `pending_download` - Awaiting audio download
- `downloading` - Audio download in progress
- `downloaded` - Audio ready for transcription
- `transcribing` - Deepgram processing
- `transcribed` - Ready for analysis
- `analyzing` - GPT-4 processing
- `analyzed` - Complete and ready
- `error` - Processing failed

### API Response Codes
- `200` - Success
- `401` - Authentication required
- `403` - Access denied
- `429` - Rate limit exceeded
- `500` - Server error

## 📚 External Resources

### APIs Used
- [Digital Concierge API](api/API_REFERENCE.md#digital-concierge-api)
- [Deepgram API](https://developers.deepgram.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [Supabase](https://supabase.com/docs)

### MCP Tools
- [Playwright Browser](https://github.com/modelcontextprotocol/servers/tree/main/src/playwright)
- [Filesystem Tools](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)

## 🤝 Contributing
- [Development Setup](README.md#development)
- [Testing Guide](api/API_REFERENCE.md#testing)
- [Code Style](README.md#code-style)

## 📞 Support
- [Common Issues](README.md#troubleshooting)
- [Debug Mode](../SETUP_GUIDE.md#debug-mode)
- [GitHub Issues](https://github.com/yourusername/mcp-call-analyzer/issues)

---

*Last Updated: January 2024*