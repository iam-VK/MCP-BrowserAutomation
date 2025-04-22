npm install
npm run build
node cli.js

## optional customizations
# Run with vision mode (uses screenshots instead of snapshots)
node cli.js --vision

# Run in headless mode
node cli.js --headless

# Specify a different browser
node cli.js --browser firefox

# Run on a specific port for SSE transport
node cli.js --port 8931