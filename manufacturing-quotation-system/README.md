# Manufacturing Quotation System

An AI-powered manufacturing quotation system that analyzes 2D/3D drawings and provides comprehensive manufacturing quotes with machining analysis, cost calculation, and professional quote generation.

## Features

### Core Functionality
- **Multi-format Drawing Upload**: Support for CAD files (STEP, STL, DWG), PDFs, and images
- **AI-Powered Analysis**: Automatic part identification and feature extraction
- **Machining Process Analysis**: Cycle time estimation, tool requirements, stock material analysis
- **Cost Calculation**: Comprehensive pricing with overhead management
- **Professional Quote Generation**: Client-ready quotes with margin protection
- **Feedback Loop**: Model retraining with actual production data

### System Components
- **Frontend**: React with TypeScript for modern UI/UX
- **Backend**: FastAPI for high-performance API
- **AI Engine**: Computer vision and machine learning for drawing analysis
- **Database**: PostgreSQL for data persistence
- **File Storage**: AWS S3 compatible storage for drawings

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Docker (optional)

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd manufacturing-quotation-system
```

2. Install backend dependencies
```bash
cd backend
pip install -r requirements.txt
```

3. Install frontend dependencies
```bash
cd ../frontend
npm install
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm start
```

## Architecture

```
manufacturing-quotation-system/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── ai/             # AI/ML components
│   ├── requirements.txt
│   └── main.py
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utilities
│   ├── package.json
│   └── public/
├── database/               # Database migrations
├── docker-compose.yml      # Docker configuration
└── README.md
```

## Development Workflow

1. **Upload Phase**: Users upload 2D/3D drawings
2. **Analysis Phase**: AI analyzes drawings and extracts manufacturing data
3. **Quotation Phase**: System calculates costs and generates quotes
4. **Approval Phase**: Internal review with margin management
5. **Client Delivery**: Professional quote delivery to clients
6. **Feedback Phase**: Actual data collection for model improvement

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details