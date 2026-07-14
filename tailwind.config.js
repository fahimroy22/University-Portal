/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './dashboard/templates/**/*.html',
    './students/templates/**/*.html',
    './accounts/templates/**/*.html',
    './academics/templates/**/*.html',
    './faculty/templates/**/*.html',
    './finance/templates/**/*.html',
    './exams/templates/**/*.html',
    './notices/templates/**/*.html',
    './applications/templates/**/*.html',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '"IBM Plex Sans"',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'sans-serif',
        ],
      },
      colors: {
        portal: {
          accent: '#9f1c1c',
          accentDark: '#7f1717',
          accentSoft: '#fff1f2',

          danger: '#dc2626',
          dangerSoft: '#fef2f2',

          success: '#047857',
          successSoft: '#ecfdf5',

          warning: '#b45309',
          warningSoft: '#fffbeb',

          info: '#1d4ed8',
          infoSoft: '#eff6ff',

          ink: '#0f172a',
          text: '#334155',
          muted: '#64748b',
          faint: '#94a3b8',
          line: '#e2e8f0',
          canvas: '#f8fafc',
          surface: '#ffffff',
        },
      },
      borderRadius: {
        portalLg: '14px',
        portalMd: '10px',
        portalSm: '8px',
      },
      boxShadow: {
        portal: '0 1px 2px rgba(15, 23, 42, 0.04)',
      },
    },
  },
  plugins: [],
}