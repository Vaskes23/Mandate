const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

// Check if running in development mode
const isDev = process.env.NODE_ENV !== 'production';

module.exports = {
  mode: isDev ? 'development' : 'production',
  entry: './src/renderer/index.tsx',
  target: 'electron-renderer',
  devtool: isDev ? 'eval-source-map' : 'source-map',
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: {
          loader: 'ts-loader',
          options: {
            // transpileOnly skips type checking for faster builds
            // Type checking is done separately via `npm run typecheck`
            transpileOnly: isDev,
            compilerOptions: {
              // Ensure source maps work correctly
              sourceMap: true
            }
          }
        },
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js']
  },
  output: {
    filename: 'renderer.js',
    path: path.resolve(__dirname, 'dist/renderer'),
    // Required for webpack-dev-server
    publicPath: isDev ? '/' : './'
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/renderer/index.html'
    })
  ],
  // Webpack Dev Server configuration for hot reload
  devServer: {
    static: {
      directory: path.join(__dirname, 'dist/renderer')
    },
    port: 9000,
    hot: true,
    // Allow connections from Electron
    headers: {
      'Access-Control-Allow-Origin': '*'
    },
    devMiddleware: {
      writeToDisk: true
    }
  },
  // Performance hints for development
  performance: {
    hints: isDev ? false : 'warning'
  }
};
