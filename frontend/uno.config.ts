import {
  defineConfig,
  presetAttributify,
  presetIcons,
  presetWind,
  presetWebFonts,
  transformerDirectives,
  transformerVariantGroup,
} from 'unocss'

export default defineConfig({
  presets: [
    presetWind(),
    presetWebFonts({
      fonts: {
        sans: 'PT Sans:400,700',
        oswald: 'Oswald:400,700',
      }
    }),
    presetAttributify(),
    presetIcons({
      scale: 1.2,
      extraProperties: {
        'display': 'inline-block',
        'vertical-align': 'middle',
      },
    }),
  ],
  theme: {
    colors: {
      // Custom theme colors
      primary: {
        DEFAULT: '#ff0e02', // Flashy red for title
        dark: '#cc0b02',
      },
      background: {
        DEFAULT: '#090909', // True black background
        light: '#121212',
      },
      text: {
        primary: '#ffffff', // White primary text
        secondary: '#fcfbe0', // Beige popcorn color
      },
      card: {
        border: '#fcfbe0', // Beige popcorn border
        blur: 'rgba(252, 251, 224, 0.3)', // Beige blur for hover effects
      },
      screening: {
        bg: '#181616', // Dark background for screening groups
        text: '#fcfbe0', // Beige popcorn text
      }
    }
  },
  transformers: [
    transformerDirectives(),
    transformerVariantGroup(),
  ],
  shortcuts: {
    'app-bg': 'bg-background text-text-primary min-h-screen',
    'card-border': 'border-2 border-card-border',
    'screening-group': 'bg-screening-bg text-screening-text',
    'title-flashy': 'text-primary uppercase font-bold font-oswald',
    'text-secondary': 'text-text-secondary',
    'movie-title': 'font-oswald font-bold text-xl',
    'card-hover-blur': 'hover:border-card-border hover:border-2 transition-all duration-300',
    'card-blur-border': 'hover:border-card-border hover:border-2 hover:backdrop-blur-sm transition-all duration-300',
    'card-beige-blur-border': 'relative hover:border-card-border hover:border-2 transition-all duration-300 group',
    'screening-time': 'text-white font-medium',
  }
})
