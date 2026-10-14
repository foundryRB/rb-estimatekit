import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
    /* ── Global ignores ──────────────────────────────────── */
    {
        ignores: [
            'dist/',
            'node_modules/',
            'src/api/generated/',
            '*.min.js',
        ],
    },

    /* ── Base: recommended JS + TS ───────────────────────── */
    js.configs.recommended,
    ...tseslint.configs.recommended,

    /* ── React hooks ─────────────────────────────────────── */
    {
        plugins: { 'react-hooks': reactHooks },
        rules: {
            ...reactHooks.configs.recommended.rules,
        },
    },

    /* ── Project rules ───────────────────────────────────── */
    {
        files: ['**/*.{ts,tsx,js,jsx}'],
        rules: {
            /* Formatting enforced via Prettier — these are
               the few style rules ESLint still validates. */
            indent: ['error', 4, { SwitchCase: 1 }],
            quotes: ['error', 'single', { avoidEscape: true }],
            semi: ['error', 'always'],

            /* TypeScript */
            '@typescript-eslint/no-unused-vars': [
                'warn',
                { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
            ],
            '@typescript-eslint/no-explicit-any': 'error',
            '@typescript-eslint/consistent-type-imports': [
                'error',
                { prefer: 'type-imports' },
            ],

            /* React */
            'react-hooks/exhaustive-deps': 'warn',
            'react-hooks/rules-of-hooks': 'error',

            /* General */
            'no-console': ['warn', { allow: ['warn', 'error'] }],
            eqeqeq: ['error', 'always'],
            'no-var': 'error',
            'prefer-const': 'error',
        },
    },

    /* ── Prettier compat (must be last) ──────────────────── */
    prettier,
);
