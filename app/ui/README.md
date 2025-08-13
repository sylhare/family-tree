# Family Tree UI

A React TypeScript frontend for the Genealogical Tree Application. This modern web interface allows you to create, manage, and visualize family trees that are stored in a Neo4j graph database.

## 🎯 Features

- ✨ **Add Family Members**: Create persons with ID, name, and birth date
- 🔗 **Build Relationships**: Connect family members with various relationship types
- 👀 **Live Preview**: See your family tree structure as you build it
- 💾 **Save to Neo4j**: Submit complete family trees to the database
- 🔄 **Real-time Status**: API connectivity monitoring
- 📱 **Responsive Design**: Works on desktop and mobile

## 🚀 Quick Start (Recommended)

The easiest way to run the UI is with the complete stack:

```bash
cd ../  # Go to app directory
docker compose up --build
```

Then open **http://localhost:3000** in your browser.

## 🛠️ Development

### Local Development

For UI development with hot reload:

```bash
# Terminal 1: Start backend services
cd ../
docker compose up neo4j api

# Terminal 2: Start UI in development mode
cd ui
npm install
npm run dev       # Start development server
```

The app will run on http://localhost:5173 (Vite default) and proxy API calls to http://localhost:8000.

### Production Build

```bash
npm run build
npm run preview   # Preview production build
```

## 🎯 How to Use the Interface

### 1. Check API Connection
- Look for **"✅ Online"** status in the header
- If showing **"❌ Offline"**, wait for backend to start or check Docker services

### 2. Add Family Members

Use the **"Add Person"** form:
- **ID**: Unique identifier (e.g., "john-1", "jane-2")  
- **Name**: Full name (e.g., "John Doe")
- **Birth Date**: Optional date (e.g., "1970-01-01")

Click **"Add Person"** to add them to your tree.

### 3. Create Relationships

Use the **"Add Relationship"** form:
1. **From Person**: Select the first person from dropdown
2. **Relationship Type**: Choose relationship:
   - **PARENT_OF**: Parent → Child
   - **MARRIED**: Spouse relationship
   - **SIBLING**: Brother/Sister
   - **GRANDPARENT_OF**: Grandparent → Grandchild
3. **To Person**: Select the second person from dropdown

Click **"Add Relationship"** to connect them.

### 4. View Your Tree

The **"Current Family Tree"** section shows:
- **Statistics**: Count of persons and relationships
- **Persons List**: All family members with birth dates
- **Relationships List**: All connections between family members
- **Clear All**: Button to reset your tree (requires confirmation)

### 5. Save to Database

Once you're happy with your family tree:
1. Click **"Save to Neo4j"** button
2. Wait for success message
3. Your tree is now permanently stored in the database

### 6. Explore in Neo4j Browser

Visit **http://localhost:7474** to query your data:
- Username: `neo4j`
- Password: `password`

## 🏗️ Architecture

- **React 18** with **TypeScript** for type safety
- **Vite** for fast development and building
- **Vitest** for testing (modern Jest alternative)
- **Fetch API** for backend communication
- **CSS Grid & Flexbox** for responsive layout
- **Nginx** for production serving and API proxying

## 🔗 API Integration

The UI communicates with the FastAPI backend:

- `GET /health` - Check API status (shown in header)
- `POST /tree` - Submit family tree data (when you click "Save to Neo4j")

Error handling includes user-friendly messages for common scenarios like duplicate IDs and invalid relationship types.

## 👥 Relationship Types

The UI supports these relationship types:
- `PARENT_OF` - Parent to child relationship
- `MARRIED` - Spouse/marriage relationship
- `SIBLING` - Brother/sister relationship  
- `GRANDPARENT_OF` - Grandparent to grandchild relationship

Custom types can be added by updating the `RELATIONSHIP_TYPES` array in `RelationshipForm.tsx`. 

## 🧪 Testing

### Running Tests

```bash
npm test                    # Interactive test runner with Vitest
npm run test:coverage       # Run tests with coverage report
```

### Test Migration Success ✅

Successfully migrated from **Jest/react-scripts** to **Vite/Vitest**:

- ⚡ **Faster builds** - Vite vs Webpack
- 🔧 **Modern tooling** - Latest TypeScript, ESM modules
- 📦 **Smaller bundle** - 219 dependencies vs 1545+ with react-scripts
- 🛡️ **Better security** - 5 vulnerabilities vs 9+ with react-scripts

### Test Results

**Current Status**: 45/45 tests passing (100% success rate)

- ✅ **API Service Tests**: 6/6 passing - Complete coverage
- ✅ **Component Rendering**: All basic rendering tests pass
- ✅ **Form Interactions**: Core form submission logic works
- ✅ **App Integration**: Main app functionality fully tested

### Test Structure

```
src/tests/
├── PersonForm.test.tsx      # Person form tests (6/6 passing)
├── RelationshipForm.test.tsx # Relationship form tests (8/8 passing) 
├── TreeSummary.test.tsx     # Tree summary tests (9/9 passing)
├── App.test.tsx             # Main app tests (16/16 passing)
└── api.test.ts              # API service tests (6/6 passing) ✅
```

The test framework migration is complete and functional. All critical functionality is thoroughly tested.

### Test Technologies

- **Vitest** - Fast, modern test runner with native ESM support
- **React Testing Library** - Component testing with user interactions
- **jsdom** - DOM environment for Node.js testing
- **User Event** - Realistic user interaction simulation

## 📁 File Structure

```
ui/
├── README.md               # This file  
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite build configuration
├── tsconfig.json           # TypeScript configuration
├── index.html              # Main HTML template
├── Dockerfile              # Production container
├── nginx.conf              # Nginx configuration for production
├── src/
│   ├── App.tsx             # Main application component
│   ├── App.css             # Application styles
│   ├── index.tsx           # React entry point
│   ├── types.ts            # TypeScript type definitions
│   ├── api.ts              # Backend API integration
│   ├── setupTests.ts       # Test configuration
│   ├── vite-env.d.ts       # Vite environment types
│   ├── components/
│   │   ├── PersonForm.tsx      # Add person form
│   │   ├── RelationshipForm.tsx # Add relationship form  
│   │   └── TreeSummary.tsx     # Family tree display
│   └── tests/
│       ├── App.test.tsx        # Main app tests
│       ├── PersonForm.test.tsx # Person form tests
│       ├── RelationshipForm.test.tsx # Relationship form tests
│       ├── TreeSummary.test.tsx # Tree summary tests
│       └── api.test.ts         # API service tests
└── dist/                   # Production build output (generated)
```

## 🔧 Troubleshooting

### Common Issues

**"❌ Offline" Status**
- Backend is still starting - wait 30-60 seconds
- Check if Docker services are running: `docker compose ps`

**Form Validation Errors**
- **Duplicate ID**: Use unique IDs like "john-1", "john-2" 
- **Empty Fields**: ID and Name are required for persons
- **Self-Relationship**: A person cannot have a relationship with themselves

**Build Issues**
- Run `npm install` to update dependencies
- Clear cache: `rm -rf node_modules package-lock.json && npm install`

### Development Issues

**Port Conflicts**
- UI dev server (5173) or production (3000) port in use
- Kill conflicting processes or change port in `vite.config.ts`

**API Connection Issues**  
- Check backend is running on port 8000
- Verify proxy configuration in `vite.config.ts`

## 🌟 Example Workflow

1. **Start the application**: `docker compose up --build`
2. **Open UI**: http://localhost:3000  
3. **Add persons**: 
   - john-1, "John Doe", 1970-01-01
   - jane-1, "Jane Doe", 1972-02-14
   - alice-1, "Alice Doe", 2000-05-30
4. **Add relationships**:
   - John → MARRIED → Jane  
   - John → PARENT_OF → Alice
   - Jane → PARENT_OF → Alice
5. **Save**: Click "Save to Neo4j"
6. **Explore**: Visit http://localhost:7474 to query your data

The UI provides an intuitive interface for building complex family trees that are stored as graph data in Neo4j! 🌳 