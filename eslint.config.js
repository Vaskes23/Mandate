// ESLint 9.x flat config format
const tsParser = require('@typescript-eslint/parser');
const tsPlugin = require('@typescript-eslint/eslint-plugin');
const reactPlugin = require('eslint-plugin-react');
const reactHooksPlugin = require('eslint-plugin-react-hooks');
const prettierConfig = require('eslint-config-prettier');

module.exports = [
  // Global ignores
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/build/**',
      '**/scripts/**',
      '**/*.py',
      'webpack.*.js',
      '.eslintcache',
      '.cache/**',
      'CLAUDE_ASSESSMENT.md',
      'CODEX_ASSESSMENT.md',
      'FINAL_OPTIMIZATION_ROADMAP.md',
      'REPORT.md',
    ],
  },

  // TypeScript and React configuration
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
        project: './tsconfig.json',
      },
      globals: {
        // Node.js globals
        process: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        module: 'readonly',
        require: 'readonly',
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
      react: reactPlugin,
      'react-hooks': reactHooksPlugin,
    },
    rules: {
      // TypeScript recommended rules
      ...tsPlugin.configs.recommended.rules,

      // React recommended rules
      ...reactPlugin.configs.recommended.rules,

      // React Hooks recommended rules
      ...reactHooksPlugin.configs.recommended.rules,

      // Custom overrides
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
        },
      ],
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',

      // Descriptive variable names enforcement
      'id-length': [
        'error',
        {
          min: 3,
          max: 50,
          exceptions: ['i', 'j', 'k', 'x', 'y', 'id', 'to', 'fs', 'cv'],
          properties: 'never',
        },
      ],
      'id-denylist': [
        'error',
        'data',
        'item',
        'temp',
        'tmp',
        'obj',
        'arr',
        'val',
        'e',
        'err',
      ],
      camelcase: [
        'error',
        {
          properties: 'always',
          ignoreDestructuring: false,
          ignoreImports: false,
          allow: ['^UNSAFE_'],
        },
      ],
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },

  // Prettier configuration (must be last to override conflicting rules)
  prettierConfig,
];
